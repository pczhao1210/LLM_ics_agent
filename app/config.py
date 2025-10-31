import os
import json
from pathlib import Path
from typing import Dict, Any

class Settings:
    def __init__(self):
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        config_path = Path("config/config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # 环境变量覆盖
        if os.getenv("OPENAI_API_KEY"):
            config.setdefault("openai", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_BASE_URL"):
            config.setdefault("openai", {})["base_url"] = os.getenv("OPENAI_BASE_URL")
        return config
    
    @property
    def api_host(self) -> str:
        return self._config.get("api", {}).get("host", "0.0.0.0")
    
    @property
    def api_port(self) -> int:
        return self._config.get("api", {}).get("port", 8000)
    
    @property
    def openai_api_key(self) -> str:
        return self._config.get("openai", {}).get("api_key", "")
    
    @property
    def openai_base_url(self) -> str:
        return self._config.get("openai", {}).get("base_url", "https://api.openai.com/v1")
    
    @property
    def openai_model(self) -> str:
        return self._config.get("openai", {}).get("model", "gpt-4-vision-preview")
    
    @property
    def storage_path(self) -> str:
        return self._config.get("storage", {}).get("path", "./storage")
    
    @property
    def async_enabled(self) -> bool:
        return self._config.get("async", {}).get("enabled", True)
    
    @property
    def max_workers(self) -> int:
        return self._config.get("async", {}).get("max_workers", 4)
    
    @property
    def image_resize(self) -> bool:
        return self._config.get("image_processing", {}).get("resize", True)
    
    @property
    def image_max_width(self) -> int:
        return self._config.get("image_processing", {}).get("max_width", 1024)
    
    @property
    def image_max_height(self) -> int:
        return self._config.get("image_processing", {}).get("max_height", 1024)
    
    @property
    def image_quality(self) -> int:
        return self._config.get("image_processing", {}).get("quality", 85)
    
    @property
    def image_auto_rotate(self) -> bool:
        return self._config.get("image_processing", {}).get("auto_rotate", True)
    
    @property
    def image_denoise(self) -> bool:
        return self._config.get("image_processing", {}).get("denoise", False)
    
    def get_reminder_hours(self, ticket_type: str) -> int:
        return self._config.get("ics", {}).get("reminder_hours", {}).get(ticket_type, 1)
    
    @property
    def streamlit_credentials(self) -> Dict[str, Any]:
        auth_config = self._config.get("auth", {}).get("streamlit", {})
        username = auth_config.get("username") or os.getenv("STREAMLIT_USERNAME")
        password = auth_config.get("password") or os.getenv("STREAMLIT_PASSWORD")
        return {
            "username": username,
            "password": password
        }
    
    @property
    def api_token(self) -> str:
        token = self._config.get("auth", {}).get("api", {}).get("token")
        if token:
            return token
        return os.getenv("API_AUTH_TOKEN", "")

settings = Settings()
