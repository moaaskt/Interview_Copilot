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

        # Variáveis para permitir arrastar a janela
        self._offset_x = 0
        self._offset_y = 0
        self._is_recording = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Cria e posiciona os componentes da interface."""
        # Container principal com borda sutil
        self.main_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E1E2E", border_width=1, border_color="#313244")
        self.main_frame.pack(fill="both", expand=True)

        # Cabeçalho customizado (para mover a janela)
        self.header_frame = ctk.CTkFrame(self.main_frame, height=32, fg_color="#181825", corner_radius=10)
        self.header_frame.pack(fill="x", padx=4, pady=(4, 2))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ Interview Copilot",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#89B4FA"
        )
        self.title_label.pack(side="left", padx=10)

        # Badge de Status
        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="● Pronto",
            font=ctk.CTkFont(size=11),
            text_color="#A6ADC8"
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
        self.header_frame.bind("<Button-1>", self._start_drag)
        self.header_frame.bind("<B1-Motion>", self._drag)
        self.title_label.bind("<Button-1>", self._start_drag)
        self.title_label.bind("<B1-Motion>", self._drag)
        self.status_badge.bind("<Button-1>", self._start_drag)
        self.status_badge.bind("<B1-Motion>", self._drag)

        # Barra de Controles (Gravar / Responder / Limpar)
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=12, pady=(6, 4))

        self.record_btn = ctk.CTkButton(
            self.controls_frame,
            text="🎙 Gravar Pergunta",
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
            text="⚡ Responder Agora",
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
            text="🗑 Limpar",
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            text_color="#CDD6F4",
            hover_color="#45475A",
            width=70,
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

    def _start_drag(self, event) -> None:
        self._offset_x = event.x
        self._offset_y = event.y

    def _drag(self, event) -> None:
        x = self.winfo_x() + (event.x - self._offset_x)
        y = self.winfo_y() + (event.y - self._offset_y)
        self.geometry(f"+{x}+{y}")

    def _handle_toggle_recording(self) -> None:
        if self.on_toggle_recording:
            self.on_toggle_recording()

    def _handle_respond_now(self) -> None:
        if self.on_respond_now:
            self.on_respond_now()

    def _handle_clear(self) -> None:
        if self.on_clear:
            self.on_clear()
        else:
            self.clear_all()

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
                text="⏹ Parar e Responder",
                fg_color="#F38BA8",
                text_color="#11111B",
                hover_color="#EBA0AC"
            )
            self.status_badge.configure(
                text="● Ouvindo Pergunta...",
                text_color="#F38BA8"
            )
        else:
            self.record_btn.configure(
                text="🎙 Gravar Pergunta",
                fg_color="#A6E3A1",
                text_color="#11111B",
                hover_color="#94E2D5"
            )
            self.status_badge.configure(
                text="● Pronto",
                text_color="#A6ADC8"
            )

    def set_status(self, text: str, color: str = "#A6ADC8") -> None:
        """Atualiza a mensagem e cor do badge de status."""
        self.status_badge.configure(text=text, text_color=color)

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

