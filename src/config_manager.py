import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "audio": {
        "device_index": None,
        "device_name": "Padrão do Sistema",
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
    "quick_questions": [
        "Sobre Mim | Fale mais sobre você e sua trajetória profissional",
        "Arquitetura | Explique a arquitetura de um projeto recente que você desenvolveu",
        "Bugs | Como você aborda a investigação e resolução de um bug crítico em produção?",
        "Bancos | Qual é a sua experiência prática com bancos relacionais (MySQL/PostgreSQL) vs NoSQL?",
        "Desafio | Qual foi um desafio técnico complexo que você enfrentou e como superou?",
    ],
}


class ConfigManager:
    """
    Gerencia a persistência e o ciclo de vida das configurações do usuário (helpia_config.json).
    Suporta fallback automático para valores padrão em caso de arquivos inexistentes ou corrompidos.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
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
        """Restaura todas as configurações para o padrão original."""
        self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.save_config()
        logger.info("Configurações restauradas para os padrões.")

    @property
    def audio_device_index(self) -> Optional[int]:
        return self._config.get("audio", {}).get("device_index")

    @property
    def audio_device_name(self) -> str:
        return self._config.get("audio", {}).get("device_name", "Padrão do Sistema")

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
