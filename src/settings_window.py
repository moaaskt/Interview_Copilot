import customtkinter as ctk
import logging
from typing import Callable, List, Optional
try:
    from audio_capture import AudioCapture
    from config_manager import ConfigManager, DEFAULT_CONFIG
    from llm_service import DEFAULT_PERSONA
except ImportError:
    from src.audio_capture import AudioCapture
    from src.config_manager import ConfigManager, DEFAULT_CONFIG
    from src.llm_service import DEFAULT_PERSONA

logger = logging.getLogger(__name__)

MODIFIER_KEYS = {
    "Control_L", "Control_R",
    "Shift_L", "Shift_R",
    "Alt_L", "Alt_R",
    "Win_L", "Win_R",
    "Caps_Lock", "Num_Lock",
}


def format_tk_to_user(tk_str: str) -> str:
    """Converte sintaxe de bind do Tkinter (ex: <Control-space>) para formato amigável (ex: Ctrl + Espaço)."""
    if not tk_str:
        return ""
    s = tk_str.strip().replace("<", "").replace(">", "")
    parts = s.split("-")
    user_parts = []
    for p in parts:
        lower = p.lower()
        if lower in ("control", "ctrl"):
            user_parts.append("Ctrl")
        elif lower == "alt":
            user_parts.append("Alt")
        elif lower == "shift":
            user_parts.append("Shift")
        elif lower == "space":
            user_parts.append("Espaço")
        elif lower == "return":
            user_parts.append("Enter")
        elif lower in ("escape", "esc"):
            user_parts.append("Esc")
        elif lower == "backspace":
            user_parts.append("Backspace")
        else:
            user_parts.append(p.upper() if len(p) == 1 else p)
    return " + ".join(user_parts)


def parse_key_event(event) -> Optional[tuple[str, str]]:
    """
    Interpreta um evento de tecla Tkinter e retorna (tk_bind_string, user_friendly_string).
    Retorna None caso o usuário tenha pressionado apenas uma tecla modificadora isolada.
    """
    keysym = event.keysym
    if keysym in MODIFIER_KEYS:
        return None

    state = event.state
    is_ctrl = bool(state & 0x0004)
    is_shift = bool(state & 0x0001)
    is_alt = bool(state & 0x20000 or state & 0x0008)

    tk_mods = []
    user_mods = []

    if is_ctrl:
        tk_mods.append("Control")
        user_mods.append("Ctrl")
    if is_alt:
        tk_mods.append("Alt")
        user_mods.append("Alt")
    if is_shift:
        tk_mods.append("Shift")
        user_mods.append("Shift")

    clean_keysym = keysym
    user_key = keysym

    lower = keysym.lower()
    if lower == "space":
        clean_keysym = "space"
        user_key = "Espaço"
    elif lower == "return":
        clean_keysym = "Return"
        user_key = "Enter"
    elif lower in ("escape", "esc"):
        clean_keysym = "Escape"
        user_key = "Esc"
    elif lower == "backspace":
        clean_keysym = "BackSpace"
        user_key = "Backspace"
    elif lower == "tab":
        clean_keysym = "Tab"
        user_key = "Tab"
    elif keysym.startswith("F") and keysym[1:].isdigit():
        clean_keysym = keysym
        user_key = keysym
    elif len(keysym) == 1:
        clean_keysym = keysym.lower()
        user_key = keysym.upper()

    tk_body = "-".join(tk_mods + [clean_keysym])
    tk_str = f"<{tk_body}>"
    user_str = " + ".join(user_mods + [user_key])

    return tk_str, user_str


class SettingsWindow(ctk.CTkToplevel):
    """
    Janela modal de configurações do Interview Copilot (helpIA).
    Permite selecionar dispositivo de áudio, visualizar VU-meter de teste em tempo real,
    editar a persona/system prompt da IA, escolher estilos de resposta, remapear atalhos
    e gerenciar perguntas rápidas de entrevista dev.
    """

    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        on_device_change: Optional[Callable[[Optional[int], str], None]] = None,
        on_llm_change: Optional[Callable[[str, Optional[str]], None]] = None,
        on_hotkeys_change: Optional[Callable[[dict], None]] = None,
        on_quick_questions_change: Optional[Callable[[List[str]], None]] = None,
    ) -> None:
        super().__init__(parent)

        self.parent = parent
        self.config_manager = config_manager
        self.on_device_change = on_device_change
        self.on_llm_change = on_llm_change
        self.on_hotkeys_change = on_hotkeys_change
        self.on_quick_questions_change = on_quick_questions_change

        self.title("Configurações - Interview Copilot")
        self.geometry("560x490")
        self.minsize(520, 440)
        self.attributes("-topmost", True)
        self.configure(fg_color="#181825")

        self._devices_cache: list[dict] = []
        self._setup_ui()
        self.lift()
        self.focus_force()

    def _setup_ui(self) -> None:
        """Cria abas e componentes da interface de configurações."""
        # Cabeçalho da Janela de Configurações
        self.header = ctk.CTkFrame(self, fg_color="#11111B", height=40, corner_radius=0)
        self.header.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self.header,
            text="⚙ Painel de Configurações - helpIA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#89B4FA"
        )
        self.title_label.pack(side="left", padx=16, pady=8)

        # Abas Organizacionais
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#1E1E2E",
            segmented_button_fg_color="#11111B",
            segmented_button_selected_color="#89B4FA",
            segmented_button_selected_hover_color="#B4BEFE",
            segmented_button_unselected_hover_color="#313244",
            text_color="#CDD6F4"
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        self.tab_audio = self.tabview.add("🎙 Áudio")
        self.tab_llm = self.tabview.add("🧠 IA & Persona")
        self.tab_hotkeys = self.tabview.add("⌨ Atalhos")
        self.tab_quick = self.tabview.add("⚡ Perguntas Rápidas")

        self._build_audio_tab()
        self._build_llm_tab()
        self._build_hotkeys_tab()
        self._build_quick_tab()

    # ==========================================
    # ABA 1: ÁUDIO & MEDIDOR VU
    # ==========================================
    def _build_audio_tab(self) -> None:
        tab = self.tab_audio

        lbl_device = ctk.CTkLabel(
            tab,
            text="Placa de Som / Dispositivo de Entrada:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A6ADC8"
        )
        lbl_device.pack(anchor="w", padx=12, pady=(10, 4))

        # Dropdown de seleção de dispositivo
        self.device_var = ctk.StringVar(value=self.config_manager.audio_device_name)
        self.device_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.device_var,
            values=["Padrão do Sistema"],
            width=480,
            fg_color="#313244",
            button_color="#45475A",
            button_hover_color="#585B70"
        )
        self.device_menu.pack(fill="x", padx=12, pady=(0, 8))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 16))

        self.refresh_devices_btn = ctk.CTkButton(
            btn_row,
            text="🔄 Atualizar Dispositivos",
            width=160,
            height=28,
            fg_color="#313244",
            hover_color="#45475A",
            command=self._refresh_device_list
        )
        self.refresh_devices_btn.pack(side="left")

        self.save_device_btn = ctk.CTkButton(
            btn_row,
            text="💾 Salvar Dispositivo",
            width=140,
            height=28,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            command=self._save_audio_device
        )
        self.save_device_btn.pack(side="right")

        # Seção de Teste de Nível em Tempo Real
        vu_box = ctk.CTkFrame(tab, fg_color="#11111B", corner_radius=8)
        vu_box.pack(fill="x", padx=12, pady=(8, 12))

        vu_header = ctk.CTkLabel(
            vu_box,
            text="Medidor de Nível em Tempo Real (Teste de Captação):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A6ADC8"
        )
        vu_header.pack(anchor="w", padx=12, pady=(10, 4))

        vu_row = ctk.CTkFrame(vu_box, fg_color="transparent")
        vu_row.pack(fill="x", padx=12, pady=(0, 10))

        self.vu_indicator_label = ctk.CTkLabel(
            vu_row,
            text="🎙 ···",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#585B70",
            width=80
        )
        self.vu_indicator_label.pack(side="left")

        self.vu_progress_bar = ctk.CTkProgressBar(
            vu_row,
            height=14,
            corner_radius=7,
            progress_color="#89B4FA",
            fg_color="#181825"
        )
        self.vu_progress_bar.set(0.0)
        self.vu_progress_bar.pack(side="left", fill="x", expand=True, padx=(8, 12))

        # Carrega lista inicial de dispositivos
        self._refresh_device_list()

    def _refresh_device_list(self) -> None:
        """Busca dispositivos no sistema e atualiza o dropdown."""
        try:
            self._devices_cache = AudioCapture.list_available_devices()
            options = ["Padrão do Sistema"]
            for d in self._devices_cache:
                options.append(f"[{d['index']}] {d['name']}")
            self.device_menu.configure(values=options)

            # Restaura seleção salva se existir
            saved_idx = self.config_manager.audio_device_index
            if saved_idx is not None:
                for opt in options:
                    if opt.startswith(f"[{saved_idx}]"):
                        self.device_var.set(opt)
                        break
        except Exception as e:
            logger.error(f"Falha ao carregar dispositivos: {e}")

    def _save_audio_device(self) -> None:
        """Salva a escolha do dispositivo e notifica callback."""
        selected_text = self.device_var.get()
        if selected_text == "Padrão do Sistema":
            device_idx = None
            device_name = "Padrão do Sistema"
        else:
            try:
                # Extrai índice no formato "[idx] nome"
                device_idx = int(selected_text.split("]")[0].replace("[", "").strip())
                device_name = selected_text.split("]", 1)[1].strip()
            except Exception:
                device_idx = None
                device_name = selected_text

        self.config_manager.set("audio", "device_index", device_idx)
        self.config_manager.set("audio", "device_name", device_name)

        if self.on_device_change:
            self.on_device_change(device_idx, device_name)

        logger.info(f"Dispositivo de áudio salvo: [{device_idx}] {device_name}")

    def update_audio_level(self, rms: float) -> None:
        """Atualiza a barra e o indicador visual de VU na tela de configurações."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Atualiza o indicador textual
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

        self.vu_indicator_label.configure(text=text, text_color=color)

        # Atualiza a barra de progresso suave (escala até ~4000 RMS)
        progress = min(1.0, max(0.0, rms / 4000.0))
        self.vu_progress_bar.set(progress)

    # ==========================================
    # ABA 2: IA, ESTILOS & PERSONA
    # ==========================================
    def _build_llm_tab(self) -> None:
        tab = self.tab_llm

        lbl_style = ctk.CTkLabel(
            tab,
            text="Estilo de Resposta da IA:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A6ADC8"
        )
        lbl_style.pack(anchor="w", padx=12, pady=(10, 4))

        style_map = {"direta": "⚡ Direta (3-4 frases)", "tecnica": "🔬 Técnica (Aprofundada)", "star": "⭐ Método STAR"}
        inv_style_map = {v: k for k, v in style_map.items()}

        current_style_key = self.config_manager.response_style
        current_style_label = style_map.get(current_style_key, "⚡ Direta (3-4 frases)")

        self.style_segmented = ctk.CTkSegmentedButton(
            tab,
            values=["⚡ Direta (3-4 frases)", "🔬 Técnica (Aprofundada)", "⭐ Método STAR"],
            selected_color="#89B4FA",
            selected_hover_color="#B4BEFE",
            unselected_color="#181825",
            unselected_hover_color="#313244",
            text_color="#CDD6F4"
        )
        self.style_segmented.set(current_style_label)
        self.style_segmented.pack(fill="x", padx=12, pady=(0, 10))

        lbl_persona = ctk.CTkLabel(
            tab,
            text="Contexto & Perfil do Candidato (System Prompt):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A6ADC8"
        )
        lbl_persona.pack(anchor="w", padx=12, pady=(4, 4))

        self.persona_textbox = ctk.CTkTextbox(
            tab,
            height=170,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#CDD6F4",
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        current_persona = self.config_manager.custom_persona or DEFAULT_PERSONA
        self.persona_textbox.insert("1.0", current_persona)
        self.persona_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))

        self.restore_persona_btn = ctk.CTkButton(
            btn_row,
            text="↺ Restaurar Padrão",
            width=140,
            height=28,
            fg_color="#313244",
            hover_color="#45475A",
            command=self._restore_default_persona
        )
        self.restore_persona_btn.pack(side="left")

        self.save_llm_btn = ctk.CTkButton(
            btn_row,
            text="💾 Salvar IA & Persona",
            width=160,
            height=28,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            command=lambda: self._save_llm_settings(inv_style_map)
        )
        self.save_llm_btn.pack(side="right")

    def _restore_default_persona(self) -> None:
        """Restaura o texto da persona para o padrão de Moacir Neto."""
        self.persona_textbox.delete("1.0", "end")
        self.persona_textbox.insert("1.0", DEFAULT_PERSONA)

    def _save_llm_settings(self, inv_style_map: dict) -> None:
        """Persiste estilo e texto do prompt e dispara callback."""
        selected_label = self.style_segmented.get()
        style_key = inv_style_map.get(selected_label, "direta")
        persona_content = self.persona_textbox.get("1.0", "end").strip()

        # Se idêntico ao padrão, salva como None no config para economizar espaço
        custom_persona = None if persona_content == DEFAULT_PERSONA.strip() else persona_content

        self.config_manager.set("llm", "response_style", style_key)
        self.config_manager.set("llm", "custom_persona", custom_persona)

        if self.on_llm_change:
            self.on_llm_change(style_key, custom_persona)

        logger.info(f"Configurações de IA salvas: estilo='{style_key}'")

    # ==========================================
    # ABA 3: ATALHOS CUSTOMIZÁVEIS
    # ==========================================
    def _build_hotkeys_tab(self) -> None:
        tab = self.tab_hotkeys

        lbl_desc = ctk.CTkLabel(
            tab,
            text="Mapeamento de Teclas de Atalho:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A6ADC8"
        )
        lbl_desc.pack(anchor="w", padx=12, pady=(10, 2))

        lbl_help = ctk.CTkLabel(
            tab,
            text="💡 Clique em qualquer campo e pressione as teclas no seu teclado para capturar o atalho.",
            font=ctk.CTkFont(size=11),
            text_color="#89B4FA"
        )
        lbl_help.pack(anchor="w", padx=12, pady=(0, 10))

        hotkeys = self.config_manager.hotkeys
        self.hotkey_entries = {}
        self.hotkey_values = {}

        fields = [
            ("toggle_recording", "🎙 Gravar / Parar Pergunta:", hotkeys.get("toggle_recording", "<Control-space>")),
            ("respond_now", "⚡ Responder Agora:", hotkeys.get("respond_now", "<Control-Return>")),
            ("clear_session", "🗑 Limpar Tela / Reset:", hotkeys.get("clear_session", "<Escape>")),
            ("cycle_position", "🎯 Alternar Posição HUD:", hotkeys.get("cycle_position", "<F8>")),
            ("cycle_opacity", "👓 Alternar Opacidade:", hotkeys.get("cycle_opacity", "<F10>")),
            ("open_settings", "⚙ Abrir Configurações:", hotkeys.get("open_settings", "<F12>")),
        ]

        grid_frame = ctk.CTkFrame(tab, fg_color="transparent")
        grid_frame.pack(fill="x", padx=12, pady=(0, 12))

        for idx, (key, label, default_val) in enumerate(fields):
            lbl = ctk.CTkLabel(grid_frame, text=label, anchor="w", font=ctk.CTkFont(size=11), text_color="#CDD6F4")
            lbl.grid(row=idx, column=0, sticky="w", padx=(0, 10), pady=4)

            entry = ctk.CTkEntry(
                grid_frame,
                width=190,
                height=28,
                fg_color="#11111B",
                border_color="#313244",
                font=ctk.CTkFont(size=11, weight="bold"),
                justify="center"
            )
            entry.insert(0, format_tk_to_user(default_val))
            entry.grid(row=idx, column=1, sticky="e", pady=4)
            self.hotkey_entries[key] = entry
            self.hotkey_values[key] = default_val

            # Vincula eventos para captura automática de teclas
            self._setup_key_capture(key, entry)

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(10, 10))

        self.restore_hotkeys_btn = ctk.CTkButton(
            btn_row,
            text="↺ Atalhos Padrão",
            width=140,
            height=28,
            fg_color="#313244",
            hover_color="#45475A",
            command=self._restore_default_hotkeys
        )
        self.restore_hotkeys_btn.pack(side="left")

        self.save_hotkeys_btn = ctk.CTkButton(
            btn_row,
            text="💾 Salvar Atalhos",
            width=140,
            height=28,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            command=self._save_hotkeys
        )
        self.save_hotkeys_btn.pack(side="right")

    def _setup_key_capture(self, key_id: str, entry: ctk.CTkEntry) -> None:
        """Vincula eventos de foco e digitação para captura interativa de teclas."""
        def on_focus_in(event):
            entry.delete(0, "end")
            entry.insert(0, "⌨ Pressione as teclas...")
            entry.configure(border_color="#89B4FA", text_color="#89B4FA")

        def on_key_press(event):
            parsed = parse_key_event(event)
            if parsed is not None:
                tk_str, user_str = parsed
                self.hotkey_values[key_id] = tk_str
                entry.delete(0, "end")
                entry.insert(0, user_str)
                entry.configure(border_color="#313244", text_color="#CDD6F4")
                self.focus_set()
                return "break"
            return "break"

        def on_focus_out(event):
            current = entry.get().strip()
            if current == "⌨ Pressione as teclas..." or not current:
                saved = self.hotkey_values.get(key_id, "")
                entry.delete(0, "end")
                entry.insert(0, format_tk_to_user(saved))
            entry.configure(border_color="#313244", text_color="#CDD6F4")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<KeyPress>", on_key_press)
        entry.bind("<FocusOut>", on_focus_out)

    def _restore_default_hotkeys(self) -> None:
        """Restaura campos para atalhos padrão."""
        defaults = DEFAULT_CONFIG["hotkeys"]
        for key, entry in self.hotkey_entries.items():
            if key in defaults:
                def_val = defaults[key]
                self.hotkey_values[key] = def_val
                entry.delete(0, "end")
                entry.insert(0, format_tk_to_user(def_val))
                entry.configure(border_color="#313244", text_color="#CDD6F4")

    def _save_hotkeys(self) -> None:
        """Salva mapa de atalhos e notifica callback."""
        updated = {}
        for key, entry in self.hotkey_entries.items():
            val = self.hotkey_values.get(key)
            if not val:
                raw_text = entry.get().strip()
                if raw_text:
                    val = raw_text
            if val:
                updated[key] = val

        self.config_manager.set("hotkeys", None, updated)
        if self.on_hotkeys_change:
            self.on_hotkeys_change(updated)

        logger.info("Novos atalhos salvos com sucesso.")

    # ==========================================
    # ABA 4: PERGUNTAS RÁPIDAS (QUICK PROMPTS)
    # ==========================================
    def _build_quick_tab(self) -> None:
        tab = self.tab_quick

        lbl_desc = ctk.CTkLabel(
            tab,
            text="Perguntas Rápidas de Entrevista (Uma por linha):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A6ADC8"
        )
        lbl_desc.pack(anchor="w", padx=12, pady=(10, 4))

        self.quick_textbox = ctk.CTkTextbox(
            tab,
            height=200,
            corner_radius=8,
            fg_color="#11111B",
            text_color="#CDD6F4",
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        questions = self.config_manager.quick_questions
        self.quick_textbox.insert("1.0", "\n".join(questions))
        self.quick_textbox.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))

        self.restore_quick_btn = ctk.CTkButton(
            btn_row,
            text="↺ Perguntas Padrão",
            width=150,
            height=28,
            fg_color="#313244",
            hover_color="#45475A",
            command=self._restore_default_quick
        )
        self.restore_quick_btn.pack(side="left")

        self.save_quick_btn = ctk.CTkButton(
            btn_row,
            text="💾 Salvar Perguntas",
            width=150,
            height=28,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            command=self._save_quick_questions
        )
        self.save_quick_btn.pack(side="right")

    def _restore_default_quick(self) -> None:
        """Restaura perguntas padrão."""
        defaults = DEFAULT_CONFIG["quick_questions"]
        self.quick_textbox.delete("1.0", "end")
        self.quick_textbox.insert("1.0", "\n".join(defaults))

    def _save_quick_questions(self) -> None:
        """Salva lista de perguntas e notifica callback."""
        raw = self.quick_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in raw.splitlines() if line.strip()]

        self.config_manager.set("quick_questions", None, lines)
        if self.on_quick_questions_change:
            self.on_quick_questions_change(lines)

        logger.info(f"{len(lines)} perguntas rápidas salvas com sucesso.")
