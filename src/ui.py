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

        # Variáveis para controle de arrasto
        self._offset_x = 0
        self._offset_y = 0
        self._is_recording = False

        self._setup_ui()

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
        self.status_badge.pack(side="left", padx=8)

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
        self.close_btn.pack(side="right", padx=5)

        # Eventos do mouse para arrastar a janela sem barra de título
        for widget in (self.header_frame, self.title_label, self.status_badge):
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)

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

    def _bind_drag_events(self, widget) -> None:
        """Vincula eventos de arrastar diretamente ao widget."""
        widget.bind("<Button-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag)

    def _start_drag(self, event) -> None:
        """Calcula o offset estático do mouse em relação ao canto superior esquerdo da janela."""
        self._offset_x = event.x_root - self.winfo_x()
        self._offset_y = event.y_root - self.winfo_y()

    def _drag(self, event) -> None:
        """Define a posição da janela diretamente pelo cursor menos o offset do clique inicial."""
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.geometry(f"+{x}+{y}")

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
        """Adiciona token em tempo real na caixa de resposta da IA."""
        self.ai_textbox.insert("end", token)
        self.ai_textbox.see("end")

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

