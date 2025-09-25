from typing import Any, Dict, Optional

from .settings import AppConfig


class Config:
    """配置管理类 - 基于Pydantic的类型安全配置"""

    def __init__(self,
                 config_path: str = "config/config.yaml",
                 secrets_path: str = "config/secrets.yaml"):
        self.config_path = config_path
        self.secrets_path = secrets_path
        self._app_config = AppConfig.load_from_files(config_path, secrets_path)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（向后兼容方法）"""
        # 将点分隔的key转换为对象属性访问
        keys = key.split(".")
        value = self._app_config

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def get_auth(self) -> Dict[str, str]:
        """获取认证配置"""
        return self._app_config.get_auth_dict()

    def get_api_config(self) -> Dict[str, str]:
        """获取API配置"""
        return self._app_config.get_api_dict()

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self._app_config.get_llm_dict()

    def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        return self._app_config.get_proxy_dict()

    def get_prompts(self) -> Dict[str, Dict[str, Any]]:
        """获取prompt内容，按site匹配"""
        return self._app_config.get_prompts_dict()

    def get_queue_config(self) -> Dict[str, Any]:
        """获取队列配置"""
        return self._app_config.get_queue_dict()

    def get_database_url(self) -> str:
        """获取数据库URL"""
        return self._app_config.database.url

    def get_logging_config(self) -> Dict[str, str]:
        """获取日志配置"""
        return self._app_config.get_logging_dict()

    @property
    def app_config(self) -> AppConfig:
        """获取完整的应用配置对象"""
        return self._app_config


# 全局配置实例
config = Config()
