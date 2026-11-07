import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_TECH_KEYWORDS: List[str] = [
    # Linguagens & Frameworks
    "PHP:2", "CodeIgniter:3", "CodeIgniter 4:3", "Python:2", "FastAPI:2",
    "TypeScript:2", "JavaScript:2", "React:2", "Next.js:2", "Node.js:2",
    "HTML5:2", "CSS3:2", "Tailwind:2",
    # Bancos de Dados & Caches
    "MySQL:2", "PostgreSQL:2", "Redis:2", "MongoDB:2", "SQLite:2", "NoSQL:2", "SQL:2",
    # DevOps & Infra
    "Docker:2", "Docker Compose:2", "Kubernetes:2", "AWS:2", "CI/CD:2",
    "Git:2", "GitHub:2", "Linux:2", "Nginx:2", "Apache:2", "Postman:2",
    # Arquitetura & Conceitos
    "API REST:2", "RESTful:2", "WebSocket:2", "JWT:2", "OAuth:2",
    "Microservices:2", "CRUD:2", "STAR:2", "Unit Tests:2", "TDD:2", "Clean Code:2",
    # Projetos do Candidato
    "Doar Digital:2", "Evento Santo:2", "VetOS:2", "Rastrecob:2", "WhatsMiau:3", "Asaas:2", "SENAI:2",
]

DEFAULT_CONFIG: Dict[str, Any] = {
    "audio": {
        "device_index": None,
        "device_name": "Padrão do Sistema",
        "pre_roll_seconds": 5.0,
        "pre_roll_enabled": True,
    },
    "transcription": {
        "language": "pt-BR",
        "endpointing_ms": 350,
        "custom_keywords": [],
    },
    "llm": {
        "response_style": "direta",  # "direta", "tecnica", "star"
        "custom_persona": None,
        "model": "qwen/qwen3.8-27b",
    },
    "hotkeys": {
        "toggle_recording": "<Control-space>",
        "toggle_recording_alt": "<F9>",
        "respond_now": "<Control-Return>",
        "clear_session": "<Escape>",
        "clear_session_alt": "<Control-BackSpace>",
        "cycle_position": "<F8>",
        "cycle_opacity": "<F10>",
        "open_settings": "<F12>",
    },
    "question_detection": {
        "enabled": True,
        "auto_trigger_on_silence": False,
        "silence_delay_ms": 1200,
    },
    "quick_questions": [
        "Sobre Mim | Fale mais sobre você e sua trajetória profissional",
        "Arquitetura | Explique a arquitetura de um projeto recente que você desenvolveu",
        "Bugs | Como você aborda a investigação e resolução de um bug crítico em produção?",
        "Bancos | Qual é a sua experiência prática com bancos relacionais (MySQL/PostgreSQL) vs NoSQL?",
        "Desafio | Qual foi um desafio técnico complexo que você enfrentou e como superou?",
    ],
    "api_keys": {
        "groq_api_key": "",
        "gemini_api_key": "",
        "deepgram_api_key": "",
    },
}


class ConfigManager:
    """
    Gerencia a persistência e o ciclo de vida das configurações do usuário (helpia_config.json).
    Suporta fallback automático para valores padrão em caso de arquivos inexistentes ou corrompidos.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._is_default_path = config_path is None
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Raiz do projeto (um nível acima de src/)
            project_root = Path(__file__).resolve().parent.parent
            self.config_path = project_root / "helpia_config.json"

        self._config: Dict[str, Any] = {}
        self.load_config()

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Mescla dicionários recursivamente garantindo que novas chaves padrão existam."""
        result = base.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def load_config(self) -> Dict[str, Any]:
        """Carrega a configuração do arquivo JSON ou inicializa com os padrões."""
        if not self.config_path.exists():
            logger.info(f"Arquivo de configuração não encontrado em {self.config_path}. Usando padrões.")
            self._config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save_config()
            return self._config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Mescla com defaults para garantir integridade caso novos campos tenham sido adicionados
            self._config = self._deep_merge(DEFAULT_CONFIG, loaded)
            logger.info("Configurações carregadas com sucesso.")
        except Exception as e:
            logger.warning(f"Erro ao ler {self.config_path} ({e}). Recriando configurações com padrões.")
            self._config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save_config()

        return self._config

    def save_config(self) -> bool:
        """Salva a configuração atual no arquivo JSON."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configurações salvas em {self.config_path}.")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações em {self.config_path}: {e}")
            return False

    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Obtém um valor ou seção inteira da configuração."""
        if section not in self._config:
            return default
        if key is None:
            return self._config[section]
        return self._config[section].get(key, default)

    def set(self, section: str, key: Optional[str], value: Any) -> None:
        """Define um valor ou seção e persiste em disco."""
        if key is None:
            self._config[section] = value
        else:
            if section not in self._config or not isinstance(self._config[section], dict):
                self._config[section] = {}
            self._config[section][key] = value
        self.save_config()

    def reset_defaults(self) -> None:
        """Restaura todas as configurações para o padrão original, preservando chaves de API."""
        preserved_keys = self._config.get("api_keys")
        self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        if isinstance(preserved_keys, dict):
            self._config["api_keys"] = dict(preserved_keys)
        self.save_config()
        logger.info("Configurações restauradas para os padrões.")

    @property
    def groq_api_key(self) -> str:
        saved = self._config.get("api_keys", {}).get("groq_api_key", "")
        if saved and str(saved).strip():
            return str(saved).strip()
        return (os.getenv("GROQ_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip())

    @property
    def gemini_api_key(self) -> str:
        saved = self._config.get("api_keys", {}).get("gemini_api_key", "")
        if saved and str(saved).strip():
            return str(saved).strip()
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def deepgram_api_key(self) -> str:
        saved = self._config.get("api_keys", {}).get("deepgram_api_key", "")
        if saved and str(saved).strip():
            return str(saved).strip()
        return os.getenv("DEEPGRAM_API_KEY", "").strip()

    def set_api_keys(
        self,
        groq_key: str,
        gemini_key: str,
        deepgram_key: Optional[str] = None,
        sync_env: bool = True,
    ) -> None:
        """Salva e sincroniza as chaves de API da Groq, do Gemini e da Deepgram em disco e no ambiente."""
        groq_clean = (groq_key or "").strip()
        gemini_clean = (gemini_key or "").strip()
        if deepgram_key is None:
            deepgram_clean = str(self._config.get("api_keys", {}).get("deepgram_api_key", "") or "").strip()
        else:
            deepgram_clean = (deepgram_key or "").strip()

        self._config["api_keys"] = {
            "groq_api_key": groq_clean,
            "gemini_api_key": gemini_clean,
            "deepgram_api_key": deepgram_clean,
        }
        self.save_config()

        os.environ["GROQ_API_KEY"] = groq_clean
        os.environ["GEMINI_API_KEY"] = gemini_clean
        if deepgram_key is not None:
            os.environ["DEEPGRAM_API_KEY"] = deepgram_clean

        if sync_env and self._is_default_path:
            env_file = self.config_path.parent / ".env"
            if env_file.exists():
                try:
                    from dotenv import set_key
                    set_key(str(env_file), "GROQ_API_KEY", groq_clean)
                    set_key(str(env_file), "GEMINI_API_KEY", gemini_clean)
                    if deepgram_key is not None:
                        set_key(str(env_file), "DEEPGRAM_API_KEY", deepgram_clean)
                except Exception as e:
                    logger.warning(f"Não foi possível sincronizar chaves no arquivo .env: {e}")

    @property
    def audio_device_index(self) -> Optional[int]:
        return self._config.get("audio", {}).get("device_index")

    @property
    def audio_device_name(self) -> str:
        return self._config.get("audio", {}).get("device_name", "Padrão do Sistema")

    @property
    def pre_roll_seconds(self) -> float:
        return float(self._config.get("audio", {}).get("pre_roll_seconds", 5.0))

    @property
    def pre_roll_enabled(self) -> bool:
        return bool(self._config.get("audio", {}).get("pre_roll_enabled", True))

    @property
    def response_style(self) -> str:
        return self._config.get("llm", {}).get("response_style", "direta")

    @property
    def custom_persona(self) -> Optional[str]:
        return self._config.get("llm", {}).get("custom_persona")

    @property
    def hotkeys(self) -> Dict[str, str]:
        return self._config.get("hotkeys", {})

    @property
    def quick_questions(self) -> List[str]:
        return self._config.get("quick_questions", [])

    @property
    def transcription_language(self) -> str:
        return self._config.get("transcription", {}).get("language", "pt-BR")

    @property
    def transcription_endpointing_ms(self) -> int:
        return int(self._config.get("transcription", {}).get("endpointing_ms", 350))

    @property
    def custom_keywords(self) -> List[str]:
        return self._config.get("transcription", {}).get("custom_keywords", [])

    @property
    def question_detection_enabled(self) -> bool:
        return bool(self._config.get("question_detection", {}).get("enabled", True))

    @property
    def auto_trigger_enabled(self) -> bool:
        return bool(self._config.get("question_detection", {}).get("auto_trigger_on_silence", False))

    @property
    def silence_delay_ms(self) -> int:
        return int(self._config.get("question_detection", {}).get("silence_delay_ms", 1200))

    def get_combined_keywords(self) -> List[str]:
        """
        Mescla a lista de keywords padrão com as custom_keywords do usuário
        seguindo normalização determinística:
        - Sanitização de espaços (strip).
        - Descarte de strings vazias ou nulas.
        - Chave de unicidade: base_term.lower().
        - Custom keywords sobrescrevem termos padrão com o mesmo nome base.
        - Preserva a ordem original do padrão e anexa novos custom termos ao final.
        """
        def _parse_term(raw: str) -> Optional[tuple[str, str, Optional[str]]]:
            if not raw:
                return None
            cleaned = str(raw).strip()
            if not cleaned:
                return None
            if ":" in cleaned:
                parts = cleaned.rsplit(":", 1)
                base = parts[0].strip()
                weight = parts[1].strip()
                if not base:
                    return None
                return (base.lower(), base, weight if weight else None)
            else:
                return (cleaned.lower(), cleaned, None)

        custom_raw_list = self.custom_keywords or []
        custom_map: Dict[str, tuple[str, Optional[str]]] = {}
        custom_keys_order: List[str] = []

        for raw in custom_raw_list:
            parsed = _parse_term(raw)
            if parsed:
                key, base, weight = parsed
                if key not in custom_map:
                    custom_keys_order.append(key)
                custom_map[key] = (base, weight)

        result: List[str] = []
        handled_keys: set = set()

        # 1. Processa keywords padrão preservando a ordem
        for raw in DEFAULT_TECH_KEYWORDS:
            parsed = _parse_term(raw)
            if not parsed:
                continue
            key, base, weight = parsed
            if key in handled_keys:
                continue

            if key in custom_map:
                c_base, c_weight = custom_map[key]
                formatted = f"{c_base}:{c_weight}" if c_weight is not None else c_base
            else:
                formatted = f"{base}:{weight}" if weight is not None else base

            result.append(formatted)
            handled_keys.add(key)

        # 2. Anexa custom keywords que não existiam no padrão
        for key in custom_keys_order:
            if key not in handled_keys:
                c_base, c_weight = custom_map[key]
                formatted = f"{c_base}:{c_weight}" if c_weight is not None else c_base
                result.append(formatted)
                handled_keys.add(key)

        return result
