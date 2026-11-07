import customtkinter as ctk
import logging
from typing import Callable, Optional
try:
    from config_manager import ConfigManager
    from settings_window import SettingsWindow
except ImportError:
    from src.config_manager import ConfigManager
    from src.settings_window import SettingsWindow

logger = logging.getLogger(__name__)

# Configurações globais de tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CopilotUI(ctk.CTk):
    """
    Interface flutuante overlay usando CustomTkinter.
    Sem barra de título (overrideredirect), sempre no topo e semi-transparente.
    Compatível nativamente com Windows 11 e Linux.
    """

    def __init__(
        self,
        title: str = "Interview Copilot",
        on_start_recording: Optional[Callable[[], None]] = None,
        on_stop_recording: Optional[Callable[[], None]] = None,
        on_toggle_recording: Optional[Callable[[], None]] = None,
        on_respond_now: Optional[Callable[[], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        config_manager: Optional[ConfigManager] = None,
        on_quick_question: Optional[Callable[[str], None]] = None,
        on_device_change: Optional[Callable[[Optional[int], str], None]] = None,
        on_llm_change: Optional[Callable[[str, Optional[str]], None]] = None,
        on_hotkeys_change: Optional[Callable[[dict], None]] = None,
        on_question_detection_change: Optional[Callable[[bool], None]] = None,
        on_pre_roll_change: Optional[Callable[[bool], None]] = None,
        on_api_keys_change: Optional[Callable[..., None]] = None,
    ) -> None:
        super().__init__()

        self.title(title)
        self.geometry("540x390+100+100")
        self.minsize(440, 260)

        # Configurações de overlay
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)  # Fundo escuro semi-transparente premium

        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.on_toggle_recording = on_toggle_recording
        self.on_respond_now = on_respond_now
        self.on_clear = on_clear
        self.config_manager = config_manager or ConfigManager()
        self._current_hotkeys = dict(self.config_manager.hotkeys) if hasattr(self.config_manager, "hotkeys") else {}
        self.on_quick_question = on_quick_question
        self.on_device_change = on_device_change
        self.on_llm_change = on_llm_change
        self.on_hotkeys_change = on_hotkeys_change
        self.on_question_detection_change = on_question_detection_change
        self.on_pre_roll_change = on_pre_roll_change
        self.on_api_keys_change = on_api_keys_change

        self.settings_window: Optional[SettingsWindow] = None

        self._offset_x = 0
        self._offset_y = 0
        self._is_recording = False
        self._is_question_detected = False
        self._registered_hotkeys: list[str] = []

        # Perfis de Visibilidade / Opacidade Dinâmica (Alto contraste garantido)
        self._opacity_profiles = [
            {
                "alpha": 0.92,
                "label": "👓 92%",
                "main_bg": "#181825",
                "header_bg": "#11111B",
                "textbox_bg": "#0D0E15",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#313244",
            },
            {
                "alpha": 1.0,
                "label": "👓 100%",
                "main_bg": "#11111B",
                "header_bg": "#08080C",
                "textbox_bg": "#040406",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#89B4FA",
            },
            {
                "alpha": 0.75,
                "label": "👓 75%",
                "main_bg": "#181825",
                "header_bg": "#11111B",
                "textbox_bg": "#0D0E15",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#45475A",
            },
            {
                "alpha": 0.85,
                "label": "👓 85%",
                "main_bg": "#181825",
                "header_bg": "#11111B",
                "textbox_bg": "#0D0E15",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#313244",
            },
        ]
        self._current_opacity_idx = 0

        # Presets de Posicionamento Rápido
        self._position_presets = ["top-center", "top-right", "top-left", "center"]
        self._current_position_idx = 0

        # Offsets e estado para arrasto 1:1 com throttling (livre de lag e runaway em 144Hz/XWayland)
        self._drag_offset_x: Optional[int] = None
        self._drag_offset_y: Optional[int] = None
        self._drag_target_x: int = 0
        self._drag_target_y: int = 0
        self._drag_scheduled: bool = False

        # Estado para redimensionamento manual livre via grip handle
        self._resize_start_x: Optional[int] = None
        self._resize_start_y: Optional[int] = None
        self._resize_start_w: Optional[int] = None
        self._resize_start_h: Optional[int] = None

        self._setup_ui()
        self._init_after_id = self.after(100, lambda: self._apply_opacity(self._opacity_profiles[self._current_opacity_idx]["alpha"]))

    def _setup_ui(self) -> None:
        """Cria e posiciona os componentes da interface."""
        # Container principal com borda sutil
        self.main_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E1E2E", border_width=1, border_color="#313244")
        self.main_frame.pack(fill="both", expand=True)

        # Cabeçalho customizado (para mover a janela) - Usando tk.Frame nativo para capturar eventos de mouse com 100% de fidelidade
        import tkinter as tk
        self.header_frame = tk.Frame(self.main_frame, height=32, bg="#181825", cursor="fleur")
        self.header_frame.pack(fill="x", padx=4, pady=(4, 2))
        self.header_frame.pack_propagate(False)

        self.title_label = tk.Label(
            self.header_frame,
            text="⚡ Interview Copilot",
            font=("Helvetica", 10, "bold"),
            fg="#89B4FA",
            bg="#181825",
            cursor="fleur"
        )
        self.title_label.pack(side="left", padx=(6, 4))

        # Badge de Status
        self.status_badge = tk.Label(
            self.header_frame,
            text="● Pronto",
            font=("Helvetica", 9),
            fg="#A6ADC8",
            bg="#181825",
            cursor="fleur"
        )
        self.status_badge.pack(side="left", padx=4)

        # Badge do Provedor de IA
        self.provider_badge = tk.Label(
            self.header_frame,
            text="🤖 IA: Groq",
            font=("Helvetica", 9, "bold"),
            fg="#89DCEB",
            bg="#181825",
            cursor="fleur"
        )
        self.provider_badge.pack(side="left", padx=4)

        # Indicador de Nível de Áudio (Mini VU-Meter)
        self.audio_meter_label = tk.Label(
            self.header_frame,
            text="🎙 ···",
            font=("Helvetica", 9),
            fg="#585B70",
            bg="#181825",
            cursor="fleur"
        )
        self.audio_meter_label.pack(side="left", padx=4)

        # Botão para fechar
        self.close_btn = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=26,
            height=24,
            fg_color="transparent",
            hover_color="#F38BA8",
            command=self.destroy
        )
        self.close_btn.pack(side="right", padx=(2, 6))

        # Botão para abrir Configurações
        self.settings_btn = ctk.CTkButton(
            self.header_frame,
            text="⚙",
            width=28,
            height=24,
            fg_color="transparent",
            hover_color="#313244",
            command=self.open_settings
        )
        self.settings_btn.pack(side="right", padx=2)

        # Botão para Presets de Ancoragem Rápida
        self.preset_pos_btn = ctk.CTkButton(
            self.header_frame,
            text="🎯",
            width=28,
            height=24,
            fg_color="transparent",
            hover_color="#313244",
            command=self.cycle_window_position
        )
        self.preset_pos_btn.pack(side="right", padx=2)

        # Botão para Ciclo de Opacidade / Stealth Mode
        self.opacity_btn = ctk.CTkButton(
            self.header_frame,
            text=self._opacity_profiles[self._current_opacity_idx]["label"],
            font=("Helvetica", 9),
            width=68,
            height=24,
            fg_color="transparent",
            hover_color="#313244",
            command=self.cycle_opacity
        )
        self.opacity_btn.pack(side="right", padx=2)

        # Eventos do mouse para arrastar a janela de forma 1:1, suave e sem saltos
        for widget in (self.header_frame, self.title_label, self.status_badge, self.audio_meter_label):
            self._bind_drag_events(widget)

        # Barra de Controles (Gravar / Parar / Responder / Limpar)
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=12, pady=(6, 4))

        self.record_btn = ctk.CTkButton(
            self.controls_frame,
            text="🎙 Gravar",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            height=32,
            command=self._handle_start_recording
        )
        self.record_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stop_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏹ Parar",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#313244",
            text_color="#A6ADC8",
            hover_color="#45475A",
            height=32,
            command=self._handle_stop_recording
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.respond_btn = ctk.CTkButton(
            self.controls_frame,
            text="⚡ Responder",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#89B4FA",
            text_color="#11111B",
            hover_color="#B4BEFE",
            height=32,
            command=self._handle_respond_now
        )
        self.respond_btn.pack(side="left", padx=(0, 4))

        self.clear_btn = ctk.CTkButton(
            self.controls_frame,
            text="🗑 Limpar",
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            text_color="#CDD6F4",
            hover_color="#45475A",
            width=75,
            height=32,
            command=self._handle_clear
        )
        self.clear_btn.pack(side="right")

        # Barra de Perguntas Rápidas de Entrevista (Quick Prompts)
        self.quick_prompts_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.quick_prompts_frame.pack(fill="x", padx=12, pady=(2, 2))
        self._build_quick_prompt_buttons()

        # Barra de Consumo de Tokens (TPM Progress Bar)
        self.token_usage_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.token_usage_frame.pack(fill="x", padx=12, pady=(2, 2))

        self.token_progressbar = ctk.CTkProgressBar(
            self.token_usage_frame,
            height=5,
            corner_radius=3,
            fg_color="#313244",
            progress_color="#A6E3A1"
        )
        self.token_progressbar.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.token_progressbar.set(0.0)

        self.token_usage_label = tk.Label(
            self.token_usage_frame,
            text="⚡ TPM: 0 / 7000 (0%)",
            font=("Helvetica", 8, "bold"),
            fg="#A6ADC8",
            bg="#1E1E2E"
        )
        self.token_usage_label.pack(side="right")

        # Área de Transcrição
        self.transcription_label = ctk.CTkLabel(
            self.main_frame,
            text="Pergunta Transcrita:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A6ADC8"
        )
        self.transcription_label.pack(anchor="w", padx=12, pady=(4, 2))

        self.transcription_textbox = ctk.CTkTextbox(
            self.main_frame,
            height=70,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#CDD6F4",
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.transcription_textbox.pack(fill="x", padx=12, pady=(0, 4))

        # Área de Resposta da IA
        self.ai_label = ctk.CTkLabel(
            self.main_frame,
            text="Sugestão da IA (Groq):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A6E3A1"
        )
        self.ai_label.pack(anchor="w", padx=12, pady=(2, 2))

        self.ai_textbox = ctk.CTkTextbox(
            self.main_frame,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#A6E3A1",
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.ai_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Grip Handle no canto inferior direito para redimensionamento livre do overlay
        self.resize_grip = tk.Label(
            self.main_frame,
            text="⇲",
            font=("Segoe UI Symbol", 10),
            fg="#585B70",
            bg="#1E1E2E",
            cursor="size_nw_se"
        )
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-4, y=-4)
        self.resize_grip.bind("<Button-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._resize)
        self.resize_grip.bind("<ButtonRelease-1>", self._stop_resize)

        # Registra atalhos de teclado e atualiza legendas dos botões com os atalhos atuais
        self._bind_hotkeys()
        self.update_button_labels()

    def _parse_quick_prompt_entry(self, entry: str) -> tuple[str, str]:
        """
        Extrai (rótulo_do_botão, pergunta_completa) de uma entrada rápida.
        Suporta o formato 'Nome do Botão | Pergunta' ou texto simples de pergunta.
        """
        if not entry or not entry.strip():
            return ("", "")

        if "|" in entry:
            parts = entry.split("|", 1)
            label = parts[0].strip()
            prompt = parts[1].strip()
            return (label or prompt[:12], prompt or label)

        # Fallback para entradas sem delimitador '|'
        lower = entry.lower()
        if "sobre você" in lower or "trajetória" in lower:
            label = "Sobre Mim"
        elif "arquitetura" in lower or "projeto" in lower:
            label = "Arquitetura"
        elif "bug" in lower or "investigação" in lower:
            label = "Bugs"
        elif "banco" in lower or "sql" in lower:
            label = "Bancos"
        elif "desafio" in lower:
            label = "Desafio"
        else:
            label = entry[:12] + ".." if len(entry) > 12 else entry
        return (label, entry.strip())

    def _build_quick_prompt_buttons(self) -> None:
        """Renderiza botões de atalho rápido para todas as perguntas cadastradas, com quebra de linha (wrap) dinâmica."""
        # Limpa widgets anteriores
        for widget in self.quick_prompts_frame.winfo_children():
            widget.destroy()

        questions = self.config_manager.quick_questions
        if not questions:
            return

        # Calcula a largura disponível no container para o wrap
        try:
            self.update_idletasks()
            container_w = self.quick_prompts_frame.winfo_width()
        except Exception:
            container_w = 0

        if container_w <= 60:
            container_w = max(420, self.winfo_width() - 24)

        # Cria primeira linha
        row_frame = ctk.CTkFrame(self.quick_prompts_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=1)

        lbl = ctk.CTkLabel(
            row_frame,
            text="⚡ Rápidas:",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#89B4FA"
        )
        lbl.pack(side="left", padx=(0, 6))

        current_w = 72
        current_row = row_frame

        # Itera por TODAS as perguntas salvas, sem limite fixo
        for q in questions:
            label_text, prompt_text = self._parse_quick_prompt_entry(q)
            if not label_text or not prompt_text:
                continue

            btn_w = max(58, len(label_text) * 7 + 14)
            # Se o botão ultrapassar a largura disponível da linha atual, cria uma nova linha (wrap)
            if current_w + btn_w + 4 > container_w and current_w > 80:
                current_row = ctk.CTkFrame(self.quick_prompts_frame, fg_color="transparent")
                current_row.pack(fill="x", pady=1)
                current_w = 0

            btn = ctk.CTkButton(
                current_row,
                text=label_text,
                font=ctk.CTkFont(size=10),
                fg_color="#181825",
                text_color="#CDD6F4",
                hover_color="#313244",
                height=22,
                width=btn_w,
                command=lambda question=prompt_text: self._handle_quick_prompt(question)
            )
            btn.pack(side="left", padx=2)
            current_w += btn_w + 4

    def _handle_quick_prompt(self, question: str) -> Optional[str]:
        """Dispara pergunta rápida pré-selecionada."""
        if self.on_quick_question:
            self.on_quick_question(question)
        else:
            self.update_transcription(question, is_final=True)
            if self.on_respond_now:
                self.on_respond_now()
        return "break"

    def open_settings(self, event=None) -> Optional[str]:
        """Abre a janela modal de configurações."""
        if self.settings_window is not None:
            try:
                if self.settings_window.winfo_exists():
                    self.settings_window.lift()
                    self.settings_window.focus_force()
                    return "break"
            except Exception:
                pass

        self.settings_window = SettingsWindow(
            self,
            config_manager=self.config_manager,
            on_device_change=self.on_device_change,
            on_llm_change=self.on_llm_change,
            on_hotkeys_change=self.apply_hotkeys,
            on_quick_questions_change=self._on_quick_questions_updated,
            on_question_detection_change=self.on_question_detection_change,
            on_pre_roll_change=self.on_pre_roll_change,
            on_api_keys_change=self.on_api_keys_change,
        )
        return "break"

    def _on_quick_questions_updated(self, questions: list) -> None:
        """Atualiza a barra de botões quando as perguntas forem salvas nas configurações."""
        self._build_quick_prompt_buttons()

    def _format_hotkey_for_button(self, key_str: str) -> str:
        """Converte sintaxe de bind do Tkinter ou combo legível para formato de botão (ex: <Control-space> -> Ctrl+Espaço)."""
        if not key_str:
            return ""
        s = key_str.strip().replace("<", "").replace(">", "")
        parts = s.replace("+", "-").split("-")
        res = []
        for p in parts:
            p_clean = p.strip()
            if not p_clean:
                continue
            lower = p_clean.lower()
            if lower in ("control", "ctrl"):
                res.append("Ctrl")
            elif lower == "alt":
                res.append("Alt")
            elif lower == "shift":
                res.append("Shift")
            elif lower == "space":
                res.append("Espaço")
            elif lower in ("return", "enter"):
                res.append("Enter")
            elif lower in ("escape", "esc"):
                res.append("Esc")
            elif lower == "backspace":
                res.append("Backspace")
            elif lower == "tab":
                res.append("Tab")
            elif lower.startswith("f") and lower[1:].isdigit():
                res.append(lower.upper())
            elif len(p_clean) == 1:
                res.append(p_clean.upper())
            else:
                res.append(p_clean.capitalize())
        return "+".join(res)

    def update_button_labels(self, hotkeys_dict: Optional[dict] = None) -> None:
        """Atualiza as legendas dos botões com base nas configurações ativas de atalhos."""
        if hotkeys_dict is not None:
            self._current_hotkeys = dict(hotkeys_dict)
        hotkeys = self._current_hotkeys
        k_rec = self._format_hotkey_for_button(hotkeys.get("toggle_recording", "<Control-space>"))
        k_resp = self._format_hotkey_for_button(hotkeys.get("respond_now", "<Control-Return>"))
        k_clear = self._format_hotkey_for_button(hotkeys.get("clear_session", "<Escape>"))

        rec_label = f" [{k_rec}]" if k_rec else ""
        resp_label = f" [{k_resp}]" if k_resp else ""
        clear_label = f" [{k_clear}]" if k_clear else ""

        if not self._is_recording:
            self.record_btn.configure(text=f"🎙 Gravar{rec_label}")
        else:
            self.record_btn.configure(text=f"🎙 Gravando{rec_label}")

        self.stop_btn.configure(text="⏹ Parar")
        self.respond_btn.configure(text=f"⚡ Responder{resp_label}")
        self.clear_btn.configure(text=f"🗑 Limpar{clear_label}")

    def _bind_hotkeys(self) -> None:
        """Registra os atalhos de teclado globais da janela."""
        for seq in self._registered_hotkeys:
            try:
                self.unbind_all(seq)
            except Exception:
                pass
        self._registered_hotkeys.clear()

        hotkeys = self._current_hotkeys

        # Gravar / Parar
        k_rec = hotkeys.get("toggle_recording", "<Control-space>")
        k_rec_alt = hotkeys.get("toggle_recording_alt", "<F9>")
        if k_rec:
            self.bind_all(k_rec, self._handle_toggle_recording)
            self._registered_hotkeys.append(k_rec)
        if k_rec_alt:
            self.bind_all(k_rec_alt, self._handle_toggle_recording)
            self._registered_hotkeys.append(k_rec_alt)

        # Responder Agora
        k_resp = hotkeys.get("respond_now", "<Control-Return>")
        if k_resp:
            self.bind_all(k_resp, self._handle_respond_now)
            self._registered_hotkeys.append(k_resp)

        # Limpar Sessão
        k_clear = hotkeys.get("clear_session", "<Escape>")
        k_clear_alt = hotkeys.get("clear_session_alt", "<Control-BackSpace>")
        if k_clear:
            self.bind_all(k_clear, self._handle_clear)
            self._registered_hotkeys.append(k_clear)
        if k_clear_alt:
            self.bind_all(k_clear_alt, self._handle_clear)
            self._registered_hotkeys.append(k_clear_alt)

        # Presets e Opacidade
        k_pos = hotkeys.get("cycle_position", "<F8>")
        k_op = hotkeys.get("cycle_opacity", "<F10>")
        if k_pos:
            self.bind_all(k_pos, self.cycle_window_position)
            self._registered_hotkeys.append(k_pos)
        if k_op:
            self.bind_all(k_op, self.cycle_opacity)
            self._registered_hotkeys.append(k_op)

        # Abrir Configurações
        k_sett = hotkeys.get("open_settings", "<F12>")
        if k_sett:
            self.bind_all(k_sett, self.open_settings)
            self._registered_hotkeys.append(k_sett)

    def apply_hotkeys(self, hotkeys_dict: dict) -> None:
        """Aplica novo mapeamento de teclas."""
        self._current_hotkeys = dict(hotkeys_dict)
        if hasattr(self.config_manager, "set"):
            try:
                self.config_manager.set("hotkeys", None, hotkeys_dict)
            except Exception:
                pass
        self._bind_hotkeys()
        self.update_button_labels(hotkeys_dict)

        if self.on_hotkeys_change:
            self.on_hotkeys_change(hotkeys_dict)

    def _bind_drag_events(self, widget) -> None:
        """Vincula eventos de arrastar diretamente ao widget."""
        widget.bind("<Button-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag)
        widget.bind("<ButtonRelease-1>", self._stop_drag)

    def _start_drag(self, event) -> Optional[str]:
        """Salva o offset absoluto inicial entre o cursor na tela e o canto da janela."""
        self._drag_offset_x = event.x_root - self.winfo_x()
        self._drag_offset_y = event.y_root - self.winfo_y()
        self._drag_scheduled = False
        return "break"

    def _drag(self, event) -> Optional[str]:
        """Calcula a nova posição alvo e agenda atualização desacoplada via after_idle."""
        if getattr(self, "_drag_offset_x", None) is None or getattr(self, "_drag_offset_y", None) is None:
            return "break"

        self._drag_target_x = event.x_root - self._drag_offset_x
        self._drag_target_y = event.y_root - self._drag_offset_y

        if not getattr(self, "_drag_scheduled", False):
            self._drag_scheduled = True
            self.after_idle(self._apply_drag)
        return "break"

    def _apply_drag(self) -> None:
        """Aplica a geometria no frame idle do Tk, eliminando acúmulo de fila e overshoot no XWayland."""
        self._drag_scheduled = False
        if getattr(self, "_drag_offset_x", None) is None or getattr(self, "_drag_offset_y", None) is None:
            return
        if not self.winfo_exists():
            return
        self.geometry(f"+{self._drag_target_x}+{self._drag_target_y}")

    def _stop_drag(self, event=None) -> Optional[str]:
        """Finaliza o arrasto e reseta os offsets."""
        self._drag_offset_x = None
        self._drag_offset_y = None
        self._drag_scheduled = False
        return "break"

    def _start_resize(self, event) -> Optional[str]:
        """Salva a posição e o tamanho iniciais ao iniciar o redimensionamento manual."""
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.winfo_width()
        self._resize_start_h = self.winfo_height()
        return "break"

    def _resize(self, event) -> Optional[str]:
        """Calcula e aplica novas dimensões respeitando limites mínimos ergonômicos."""
        if getattr(self, "_resize_start_x", None) is None or getattr(self, "_resize_start_y", None) is None:
            return "break"

        dw = event.x_root - self._resize_start_x
        dh = event.y_root - self._resize_start_y

        new_w = max(440, self._resize_start_w + dw)
        new_h = max(260, self._resize_start_h + dh)

        self.geometry(f"{new_w}x{new_h}")
        return "break"

    def _stop_resize(self, event=None) -> Optional[str]:
        """Finaliza o redimensionamento, limpa o estado e re-renderiza o wrap de perguntas rápidas."""
        old_w = getattr(self, "_resize_start_w", None)
        self._resize_start_x = None
        self._resize_start_y = None
        self._resize_start_w = None
        self._resize_start_h = None
        if old_w and abs(self.winfo_width() - old_w) > 15:
            self.after_idle(self._build_quick_prompt_buttons)
        return "break"

    def _handle_start_recording(self, event=None) -> Optional[str]:
        if self.on_start_recording:
            self.on_start_recording()
        elif self.on_toggle_recording and not self._is_recording:
            self.on_toggle_recording()
        return "break"

    def _handle_stop_recording(self, event=None) -> Optional[str]:
        if self.on_stop_recording:
            self.on_stop_recording()
        elif self.on_toggle_recording and self._is_recording:
            self.on_toggle_recording()
        return "break"

    def _handle_toggle_recording(self, event=None) -> Optional[str]:
        if self.on_toggle_recording:
            self.on_toggle_recording()
        return "break"

    def _handle_respond_now(self, event=None) -> Optional[str]:
        if self.on_respond_now:
            self.on_respond_now()
        return "break"

    def _handle_clear(self, event=None) -> Optional[str]:
        if self.on_clear:
            self.on_clear()
        else:
            self.clear_all()
        return "break"

    def get_transcription_text(self) -> str:
        """Retorna o texto atualmente exibido na caixa de transcrição, limpando prefixos."""
        raw = self.transcription_textbox.get("1.0", "end").strip()
        # Remove prefixos visuais como '✔ ' ou '🎙 '
        for prefix in ("✔ ", "🎙 "):
            if raw.startswith(prefix):
                raw = raw[len(prefix):].strip()
        return raw

    def set_recording_state(self, is_recording: bool) -> None:
        """Atualiza visualmente os botões de gravação/parada e badge de status."""
        self._is_recording = is_recording
        k_rec = self._format_hotkey_for_button(self._current_hotkeys.get("toggle_recording", "<Control-space>"))
        rec_label = f" [{k_rec}]" if k_rec else ""
        if is_recording:
            self.record_btn.configure(
                text=f"🎙 Gravando{rec_label}",
                fg_color="#313244",
                text_color="#A6ADC8",
                hover_color="#45475A"
            )
            self.stop_btn.configure(
                fg_color="#F38BA8",
                text_color="#11111B",
                hover_color="#EBA0AC"
            )
            self.status_badge.configure(
                text="● Ouvindo Pergunta...",
                fg="#F38BA8"
            )
        else:
            self.record_btn.configure(
                text=f"🎙 Gravar{rec_label}",
                fg_color="#A6E3A1",
                text_color="#11111B",
                hover_color="#94E2D5"
            )
            self.stop_btn.configure(
                fg_color="#313244",
                text_color="#A6ADC8",
                hover_color="#45475A"
            )
            self.status_badge.configure(
                text="● Pronto",
                fg="#A6ADC8"
            )

    def set_status(self, text: str, color: str = "#A6ADC8") -> None:
        """Atualiza a badge de status (ex: Gravando, Pronto, Reconectando)."""
        if self.status_badge.winfo_exists():
            self.status_badge.config(text=text, fg=color)

    def set_ai_provider(self, provider_name: str) -> None:
        """Atualiza a badge de provedor de IA atual no HUD."""
        if self.provider_badge.winfo_exists():
            if "Groq" in provider_name:
                self.provider_badge.config(text=f"🤖 IA: {provider_name}", fg="#89DCEB") # Azul Groq
            elif "Gemini" in provider_name:
                self.provider_badge.config(text=f"🤖 IA: {provider_name}", fg="#F9E2AF") # Amarelo Gemini
            else:
                self.provider_badge.config(text=f"🤖 IA: {provider_name}", fg="#CBA6F7")

    def update_token_usage(self, used: int, limit: int) -> None:
        """
        Atualiza o indicador visual de consumo de tokens por minuto (TPM).
        Aplica cores semânticas: Verde (<60%), Amarelo (60-85%), Vermelho (>85%).
        """
        if not hasattr(self, "token_progressbar") or not self.token_progressbar.winfo_exists():
            return

        safe_limit = max(1, limit)
        fraction = min(1.0, max(0.0, used / safe_limit))
        pct = int(fraction * 100)

        if fraction < 0.60:
            color = "#A6E3A1"  # Verde (seguro)
        elif fraction <= 0.85:
            color = "#F9E2AF"  # Amarelo (atenção)
        else:
            color = "#F38BA8"  # Vermelho (crítico / perto do fallback)

        self.token_progressbar.configure(progress_color=color)
        self.token_progressbar.set(fraction)

        if hasattr(self, "token_usage_label") and self.token_usage_label.winfo_exists():
            self.token_usage_label.config(
                text=f"⚡ TPM: {used:,} / {safe_limit:,} ({pct}%)".replace(",", "."),
                fg=color if fraction >= 0.60 else "#A6ADC8"
            )

    def update_transcription(self, text: str, is_final: bool = False) -> None:
        """Atualiza a caixa de transcrição."""
        self.transcription_textbox.delete("1.0", "end")
        prefix = "✔ " if is_final else "🎙 "
        self.transcription_textbox.insert("1.0", f"{prefix}{text}")
        self.transcription_textbox.see("end")

    def append_ai_token(self, token: str) -> None:
        """Adiciona token em tempo real na caixa de resposta da IA com auto-scroll adaptativo."""
        # Se o usuário rolou manualmente para cima, pausa o auto-scroll para não sequestrar a leitura
        should_scroll = True
        try:
            if hasattr(self.ai_textbox, "_textbox") and self.ai_textbox._textbox.winfo_height() > 10:
                _, bottom = self.ai_textbox._textbox.yview()
                if bottom < 0.98:
                    should_scroll = False
        except Exception:
            should_scroll = True

        self.ai_textbox.insert("end", token)

        if should_scroll:
            self.ai_textbox.see("end")

    def _apply_opacity(self, alpha: float) -> None:
        """
        Aplica opacidade real à janela.
        Compatível nativamente com Windows e macOS (-alpha), e Linux X11/XWayland
        através da propriedade _NET_WM_WINDOW_OPACITY via xprop.
        """
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # 1. Atributo padrão Tkinter (Windows, macOS)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            pass

        # 2. X11 / XWayland via xprop para compositores Linux
        try:
            import subprocess
            val = int(alpha * 0xFFFFFFFF)
            wid = self.winfo_id()
            targets = [str(wid)]
            try:
                out = subprocess.check_output(
                    ["xwininfo", "-id", str(wid), "-children"],
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                for line in out.splitlines():
                    if "Parent window id:" in line:
                        parent_id = line.split("Parent window id:")[1].strip().split()[0]
                        targets.append(parent_id)
            except Exception:
                pass

            for t in targets:
                subprocess.run(
                    ["xprop", "-id", t, "-f", "_NET_WM_WINDOW_OPACITY", "32c", "-set", "_NET_WM_WINDOW_OPACITY", str(val)],
                    stderr=subprocess.DEVNULL,
                    check=False
                )
        except Exception as e:
            logger.debug(f"Falha ao aplicar opacidade via xprop: {e}")

    def cycle_opacity(self, event=None) -> Optional[str]:
        """Alterna ciclicamente a opacidade real e o tema visual da janela HUD."""
        self._current_opacity_idx = (self._current_opacity_idx + 1) % len(self._opacity_profiles)
        prof = self._opacity_profiles[self._current_opacity_idx]

        # 1. Aplica transparência real na janela (Windows/macOS e Linux)
        self._apply_opacity(prof["alpha"])

        # 2. Atualiza estilos visuais com alto contraste garantido
        self.main_frame.configure(fg_color=prof["main_bg"], border_color=prof["border"])
        self.header_frame.configure(bg=prof["header_bg"])
        self.title_label.configure(bg=prof["header_bg"])
        self.status_badge.configure(bg=prof["header_bg"])
        self.audio_meter_label.configure(bg=prof["header_bg"])

        if self._is_question_detected:
            self.transcription_textbox.configure(
                fg_color=prof["textbox_bg"],
                text_color=prof["tx_text"],
                border_width=2,
                border_color="#FAB387"
            )
        else:
            self.transcription_textbox.configure(
                fg_color=prof["textbox_bg"],
                text_color=prof["tx_text"],
                border_width=0,
                border_color=prof["border"]
            )
        self.ai_textbox.configure(fg_color=prof["textbox_bg"], text_color=prof["ai_text"])
        if hasattr(self, "token_usage_label") and self.token_usage_label.winfo_exists():
            self.token_usage_label.configure(bg=prof["main_bg"])
        if hasattr(self, "resize_grip") and self.resize_grip.winfo_exists():
            self.resize_grip.configure(bg=prof["main_bg"])

        self.opacity_btn.configure(text=prof["label"])
        logger.info(f"Tema e opacidade alterados para: {prof['label']}")
        return "break"

    def _get_active_monitor(self) -> tuple[int, int, int, int]:
        """
        Detecta as coordenadas reais (origem_x, origem_y, largura, altura) do monitor ativo.
        Suporta multi-monitores de diferentes orientações (ex: horizontal + vertical),
        evitando que a janela caia em áreas mortas fora da tela.
        """
        import subprocess
        import re

        monitors = []
        try:
            out = subprocess.check_output(["xrandr", "--current"], stderr=subprocess.DEVNULL, text=True)
            for line in out.splitlines():
                if " connected " in line:
                    m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
                    if m:
                        mw, mh, mx, my = map(int, m.groups())
                        monitors.append((mx, my, mw, mh))
        except Exception:
            pass

        if not monitors:
            return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

        # Centro atual da janela
        win_cx = self.winfo_x() + 260
        win_cy = self.winfo_y() + 195

        for mx, my, mw, mh in monitors:
            if mx <= win_cx < mx + mw and my <= win_cy < my + mh:
                return mx, my, mw, mh

        # Se a janela caiu fora dos limites de todos os monitores, ancora no maior/principal
        monitors.sort(key=lambda m: m[2] * m[3], reverse=True)
        return monitors[0]

    def cycle_window_position(self, event=None) -> Optional[str]:
        """Reposiciona a janela HUD nos 4 presets estratégicos do monitor ativo."""
        preset = self._position_presets[self._current_position_idx]
        self._current_position_idx = (self._current_position_idx + 1) % len(self._position_presets)

        mx, my, mw, mh = self._get_active_monitor()
        w = max(440, self.winfo_width())
        h = max(260, self.winfo_height())

        if preset == "top-center":
            # Ancorado logo abaixo da webcam no topo do monitor ativo
            x = mx + max(0, (mw - w) // 2)
            y = my + 20
        elif preset == "top-right":
            x = mx + max(0, mw - w - 20)
            y = my + 20
        elif preset == "top-left":
            x = mx + 20
            y = my + 20
        else:  # "center"
            x = mx + max(0, (mw - w) // 2)
            y = my + max(0, (mh - h) // 2)

        self.geometry(f"{w}x{h}+{x}+{y}")
        logger.info(f"Janela HUD posicionada em '{preset}' ({x}, {y}) no monitor ({mx}, {my}, {mw}x{mh})")
        return "break"

    def clear_ai_response(self) -> None:
        """Limpa a caixa de resposta da IA para receber nova resposta."""
        self.ai_textbox.delete("1.0", "end")

    def set_question_detected(self, is_detected: bool) -> None:
        """Atualiza o realce visual (Catppuccin Peach) quando uma pergunta for detectada."""
        self._is_question_detected = is_detected
        if not hasattr(self, "transcription_label") or not self.transcription_label.winfo_exists():
            return
        if is_detected:
            self.transcription_label.configure(
                text="🎯 Pergunta Detectada:",
                text_color="#FAB387"
            )
            self.transcription_textbox.configure(
                border_width=2,
                border_color="#FAB387"
            )
        else:
            self.transcription_label.configure(
                text="Pergunta Transcrita:",
                text_color="#A6ADC8"
            )
            prof = self._opacity_profiles[self._current_opacity_idx]
            self.transcription_textbox.configure(
                border_width=0,
                border_color=prof["border"]
            )

    def clear_transcription(self) -> None:
        """Limpa a caixa de texto de transcrição e reseta o destaque de pergunta."""
        self.transcription_textbox.delete("1.0", "end")
        self.set_question_detected(False)

    def clear_all(self) -> None:
        """Limpa ambas as caixas de texto."""
        self.clear_transcription()
        self.clear_ai_response()

    def update_audio_level(self, rms: float) -> None:
        """Atualiza a representação visual do mini VU-meter de áudio no HUD e nas configurações se aberto."""
        if rms < 150:
            text = "🎙 ···"
            color = "#585B70"
        elif rms < 800:
            text = "🎙 ▃··"
            color = "#94E2D5"
        elif rms < 2500:
            text = "🎙 ▃▅·"
            color = "#A6E3A1"
        else:
            text = "🎙 ▃▅█"
            color = "#89B4FA"

        self.audio_meter_label.configure(text=text, fg=color)

        # Se a janela de configurações estiver aberta, atualiza seu medidor em tempo real
        if self.settings_window is not None:
            try:
                if self.settings_window.winfo_exists():
                    self.settings_window.update_audio_level(rms)
            except Exception:
                pass

    def destroy(self) -> None:
        """Limpa timers pendentes e encerra a janela e subjanelas."""
        if hasattr(self, "_init_after_id") and self._init_after_id:
            try:
                self.after_cancel(self._init_after_id)
            except Exception:
                pass

        if self.settings_window is not None:
            try:
                if self.settings_window.winfo_exists():
                    self.settings_window.destroy()
            except Exception:
                pass

        super().destroy()
