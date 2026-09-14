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
    """

    def __init__(self, title: str = "Interview Copilot") -> None:
        super().__init__()

        self.title(title)
        self.geometry("450x300+100+100")
        
        # Configurações de overlay no Windows
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.88)  # Fundo escuro semi-transparente

        # Variáveis para permitir arrastar a janela
        self._offset_x = 0
        self._offset_y = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Cria e posiciona os componentes da interface."""
        # Container principal com borda sutil
        self.main_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E1E2E", border_width=1, border_color="#313244")
        self.main_frame.pack(fill="both", expand=True)

        # Cabeçalho customizado (para mover a janela)
        self.header_frame = ctk.CTkFrame(self.main_frame, height=30, fg_color="#181825", corner_radius=10)
        self.header_frame.pack(fill="x", padx=2, pady=2)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ Interview Copilot",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#89B4FA"
        )
        self.title_label.pack(side="left", padx=10)

        # Botão para fechar
        self.close_btn = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=24,
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

        # Área de Transcrição
        self.transcription_label = ctk.CTkLabel(
            self.main_frame,
            text="Transcrição em tempo real:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A6ADC8"
        )
        self.transcription_label.pack(anchor="w", padx=12, pady=(8, 2))

        self.transcription_textbox = ctk.CTkTextbox(
            self.main_frame,
            height=65,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#CDD6F4",
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.transcription_textbox.pack(fill="x", padx=12, pady=(0, 8))

        # Área de Resposta da IA
        self.ai_label = ctk.CTkLabel(
            self.main_frame,
            text="Sugestão da IA (gpt-4o-mini):",
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
        self.ai_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _start_drag(self, event) -> None:
        self._offset_x = event.x
        self._offset_y = event.y

    def _drag(self, event) -> None:
        x = self.winfo_x() + (event.x - self._offset_x)
        y = self.winfo_y() + (event.y - self._offset_y)
        self.geometry(f"+{x}+{y}")

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
