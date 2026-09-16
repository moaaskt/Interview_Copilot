import asyncio
import logging
from typing import Callable, Dict, Optional

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False

logger = logging.getLogger(__name__)


def to_pynput_hotkey(tk_str: str) -> Optional[str]:
    """
    Converte a sintaxe de bind do Tkinter (ex: <Control-space>, <F12>, <Control-Shift-r>)
    para o formato compatível com pynput.keyboard.GlobalHotKeys (ex: <ctrl>+<space>, <f12>, <ctrl>+<shift>+r).
    """
    if not tk_str or not isinstance(tk_str, str):
        return None

    cleaned = tk_str.strip().replace("<", "").replace(">", "")
    if not cleaned:
        return None

    parts = cleaned.split("-")
    pynput_parts = []

    for p in parts:
        lower = p.lower()
        if lower in ("control", "ctrl"):
            pynput_parts.append("<ctrl>")
        elif lower == "alt":
            pynput_parts.append("<alt>")
        elif lower == "shift":
            pynput_parts.append("<shift>")
        elif lower == "space":
            pynput_parts.append("<space>")
        elif lower == "return":
            pynput_parts.append("<enter>")
        elif lower in ("escape", "esc"):
            pynput_parts.append("<esc>")
        elif lower == "backspace":
            pynput_parts.append("<backspace>")
        elif lower == "tab":
            pynput_parts.append("<tab>")
        elif lower.startswith("f") and lower[1:].isdigit():
            pynput_parts.append(f"<{lower}>")
        elif len(p) == 1:
            pynput_parts.append(p.lower())
        else:
            pynput_parts.append(f"<{lower}>")

    return "+".join(pynput_parts)


class HotkeyManager:
    """
    Gerenciador de atalhos globais de teclado do sistema operacional.
    Permite acionar comandos do Interview Copilot mesmo com outra janela em foco
    (ex: Google Meet, Zoom, navegador ou IDE).
    """

    def __init__(
        self,
        callbacks: Dict[str, Callable[[], None]],
        hotkeys: Optional[Dict[str, str]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self.callbacks = callbacks
        self.hotkeys = hotkeys or {}
        self.loop = loop
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._is_running = False

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Define ou atualiza o loop de eventos assíncrono."""
        self.loop = loop

    def _dispatch_callback(self, action_name: str) -> None:
        """Executa a callback associada à ação de forma thread-safe."""
        callback = self.callbacks.get(action_name)
        if not callback:
            return

        def _safe_call():
            try:
                callback()
            except Exception as e:
                logger.error(f"Erro ao executar callback global '{action_name}': {e}")

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(_safe_call)
        else:
            _safe_call()

    def _build_hotkeys_map(self) -> Dict[str, Callable[[], None]]:
        """Monta o dicionário de mapeamento para o GlobalHotKeys do pynput."""
        hotkey_map = {}

        for action_name, tk_combo in self.hotkeys.items():
            if not tk_combo:
                continue

            pynput_combo = to_pynput_hotkey(tk_combo)
            if not pynput_combo:
                continue

            # Cria closure capturando action_name
            def make_handler(name: str):
                return lambda: self._dispatch_callback(name)

            hotkey_map[pynput_combo] = make_handler(action_name)
            logger.debug(f"[HotkeyManager] Registrado global: {pynput_combo} -> {action_name}")

        return hotkey_map

    def start(self) -> None:
        """Inicia a escuta de atalhos globais em thread em segundo plano."""
        if not PYNPUT_AVAILABLE:
            logger.warning("[HotkeyManager] Biblioteca 'pynput' não disponível. Atalhos globais desabilitados.")
            return

        if self._is_running:
            self.stop()

        hotkey_map = self._build_hotkeys_map()
        if not hotkey_map:
            logger.warning("[HotkeyManager] Nenhum atalho global configurado para escuta.")
            return

        try:
            self._listener = keyboard.GlobalHotKeys(hotkey_map)
            self._listener.daemon = True
            self._listener.start()
            self._is_running = True
            logger.info(f"[HotkeyManager] Escuta de atalhos globais iniciada ({len(hotkey_map)} atalhos registrados).")
        except Exception as e:
            logger.error(f"[HotkeyManager] Falha ao iniciar GlobalHotKeys: {e}")
            self._listener = None
            self._is_running = False

    def stop(self) -> None:
        """Interrompe a escuta de atalhos globais."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception as e:
                logger.debug(f"[HotkeyManager] Erro ao parar listener: {e}")
            finally:
                self._listener = None

        self._is_running = False
        logger.info("[HotkeyManager] Escuta de atalhos globais finalizada.")

    def update_hotkeys(self, new_hotkeys: Dict[str, str]) -> None:
        """Atualiza a tabela de atalhos e reinicia a escuta globalmente."""
        self.hotkeys = dict(new_hotkeys)
        logger.info("[HotkeyManager] Atualizando atalhos globais...")
        if self._is_running:
            self.stop()
            self.start()
