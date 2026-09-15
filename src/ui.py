import customtkinter as ctk
import logging
from typing import Optional

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
        on_toggle_recording: Optional[callable] = None,
        on_respond_now: Optional[callable] = None,
        on_clear: Optional[callable] = None,
    ) -> None:
        super().__init__()

        self.title(title)
        self.geometry("520x390+100+100")
        
        # Configurações de overlay
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)  # Fundo escuro semi-transparente premium

        self.on_toggle_recording = on_toggle_recording
        self.on_respond_now = on_respond_now
        self.on_clear = on_clear

        self._offset_x = 0
        self._offset_y = 0
        self._is_recording = False

        # Perfis de Visibilidade / Opacidade Dinâmica (Alto contraste garantido)
        self._opacity_profiles = [
            {
                "alpha": 0.92,
                "label": "👓 92% Padrão",
                "main_bg": "#181825",
                "header_bg": "#11111B",
                "textbox_bg": "#0D0E15",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#313244",
            },
            {
                "alpha": 1.0,
                "label": "👓 100% Foco",
                "main_bg": "#11111B",
                "header_bg": "#08080C",
                "textbox_bg": "#040406",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#89B4FA",
            },
            {
                "alpha": 0.75,
                "label": "👓 75% Discreto",
                "main_bg": "#181825",
                "header_bg": "#11111B",
                "textbox_bg": "#0D0E15",
                "ai_text": "#50FA7B",
                "tx_text": "#FFFFFF",
                "border": "#45475A",
            },
            {
                "alpha": 0.85,
                "label": "👓 85% Suave",
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

        # Offsets para arrasto 1:1 perfeitamente sincronizado com o ponteiro
        self._drag_offset_x: Optional[int] = None
        self._drag_offset_y: Optional[int] = None

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
        self.title_label.pack(side="left", padx=10)

        # Badge de Status
        self.status_badge = tk.Label(
            self.header_frame,
            text="● Pronto",
            font=("Helvetica", 9),
            fg="#A6ADC8",
            bg="#181825",
            cursor="fleur"
        )
        self.status_badge.pack(side="left", padx=(8, 4))

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
            width=88,
            height=24,
            fg_color="transparent",
            hover_color="#313244",
            command=self.cycle_opacity
        )
        self.opacity_btn.pack(side="right", padx=2)

        # Eventos do mouse para arrastar a janela de forma 1:1, suave e sem saltos
        for widget in (self.header_frame, self.title_label, self.status_badge, self.audio_meter_label):
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)
            widget.bind("<ButtonRelease-1>", self._stop_drag)

        # Barra de Controles (Gravar / Responder / Limpar)
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=12, pady=(6, 4))

        self.record_btn = ctk.CTkButton(
            self.controls_frame,
            text="🎙 Gravar [Ctrl+Espaço]",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            height=32,
            command=self._handle_toggle_recording
        )
        self.record_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.respond_btn = ctk.CTkButton(
            self.controls_frame,
            text="⚡ Responder [Ctrl+Enter]",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#89B4FA",
            text_color="#11111B",
            hover_color="#B4BEFE",
            height=32,
            command=self._handle_respond_now
        )
        self.respond_btn.pack(side="left", padx=(0, 6))

        self.clear_btn = ctk.CTkButton(
            self.controls_frame,
            text="🗑 Limpar [Esc]",
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            text_color="#CDD6F4",
            hover_color="#45475A",
            width=85,
            height=32,
            command=self._handle_clear
        )
        self.clear_btn.pack(side="right")

        # Área de Transcrição
        self.transcription_label = ctk.CTkLabel(
            self.main_frame,
            text="Pergunta Transcrita:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A6ADC8"
        )
        self.transcription_label.pack(anchor="w", padx=12, pady=(6, 2))

        self.transcription_textbox = ctk.CTkTextbox(
            self.main_frame,
            height=75,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#CDD6F4",
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.transcription_textbox.pack(fill="x", padx=12, pady=(0, 6))

        # Área de Resposta da IA
        self.ai_label = ctk.CTkLabel(
            self.main_frame,
            text="Sugestão da IA (Groq):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A6E3A1"
        )
        self.ai_label.pack(anchor="w", padx=12, pady=(4, 2))

        self.ai_textbox = ctk.CTkTextbox(
            self.main_frame,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#A6E3A1",
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.ai_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Atalhos de Teclado Globais (Foco na janela)
        self.bind_all("<Control-space>", self._handle_toggle_recording)
        self.bind_all("<F9>", self._handle_toggle_recording)
        self.bind_all("<Control-Return>", self._handle_respond_now)
        self.bind_all("<Escape>", self._handle_clear)
        self.bind_all("<Control-BackSpace>", self._handle_clear)
        self.bind_all("<F8>", self.cycle_window_position)
        self.bind_all("<F10>", self.cycle_opacity)

    def _bind_drag_events(self, widget) -> None:
        """Vincula eventos de arrastar diretamente ao widget."""
        widget.bind("<Button-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag)
        widget.bind("<ButtonRelease-1>", self._stop_drag)

    def _start_drag(self, event) -> Optional[str]:
        """Salva o offset exato do ponteiro em relação à janela para arrasto 1:1 perfeito."""
        pointer_x, pointer_y = self.winfo_pointerxy()
        self._drag_offset_x = pointer_x - self.winfo_x()
        self._drag_offset_y = pointer_y - self.winfo_y()
        return "break"

    def _drag(self, event) -> Optional[str]:
        """Move a janela acompanhando 1:1 o cursor do mouse sem aceleração nem saltos."""
        if getattr(self, "_drag_offset_x", None) is None or getattr(self, "_drag_offset_y", None) is None:
            return "break"
        pointer_x, pointer_y = self.winfo_pointerxy()
        new_x = pointer_x - self._drag_offset_x
        new_y = pointer_y - self._drag_offset_y
        self.geometry(f"+{new_x}+{new_y}")
        return "break"

    def _stop_drag(self, event=None) -> Optional[str]:
        """Finaliza o arrasto e reseta os offsets."""
        self._drag_offset_x = None
        self._drag_offset_y = None
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
        """Atualiza visualmente o botão e badge de status de gravação."""
        self._is_recording = is_recording
        if is_recording:
            self.record_btn.configure(
                text="⏹ Parar [Ctrl+Espaço]",
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
                text="🎙 Gravar [Ctrl+Espaço]",
                fg_color="#A6E3A1",
                text_color="#11111B",
                hover_color="#94E2D5"
            )
            self.status_badge.configure(
                text="● Pronto",
                fg="#A6ADC8"
            )

    def set_status(self, text: str, color: str = "#A6ADC8") -> None:
        """Atualiza a mensagem e cor do badge de status."""
        self.status_badge.configure(text=text, fg=color)

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

        self.transcription_textbox.configure(fg_color=prof["textbox_bg"], text_color=prof["tx_text"])
        self.ai_textbox.configure(fg_color=prof["textbox_bg"], text_color=prof["ai_text"])

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
        w = 520
        h = 390

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

    def clear_transcription(self) -> None:
        """Limpa a caixa de texto de transcrição."""
        self.transcription_textbox.delete("1.0", "end")

    def clear_all(self) -> None:
        """Limpa ambas as caixas de texto."""
        self.clear_transcription()
        self.clear_ai_response()

    def update_audio_level(self, rms: float) -> None:
        """Atualiza a representação visual do mini VU-meter de áudio no HUD."""
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

    def destroy(self) -> None:
        """Limpa timers pendentes e encerra a janela."""
        if hasattr(self, "_init_after_id") and self._init_after_id:
            try:
                self.after_cancel(self._init_after_id)
            except Exception:
                pass
        super().destroy()


