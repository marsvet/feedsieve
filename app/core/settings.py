"""
Pydantic配置模型定义

使用Pydantic定义所有配置结构，提供类型检查和验证
"""

import os
import re
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class PromptConfig(BaseModel):
    """单个Prompt配置"""
    site: List[str] = Field(..., description="网站URL列表")
    refetch_content: bool = Field(default=False, description="是否重新抓取网页内容")
    prompt: str = Field(..., description="Prompt内容")


class QueueConfig(BaseModel):
    """队列配置"""
    retry_times: int = Field(default=3, ge=1, description="重试次数")
    dead_letter_retry_daily: bool = Field(default=True, description="是否每日重试死信")
    process_interval_seconds: int = Field(
        default=300, ge=60, description="队列处理间隔，单位：秒（最小60秒）")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = Field(default="sqlite:///./data/feedsieve.db",
                     description="数据库连接URL")


class LoggingFilesConfig(BaseModel):
    """日志文件配置"""
    app: str = Field(default="data/feedsieve.log", description="主应用日志文件")
    error: str = Field(default="data/error.log", description="错误日志文件")
    webhook: str = Field(default="data/webhook.log", description="Webhook日志文件")
    queue: str = Field(default="data/queue.log", description="队列处理日志文件")
    llm: str = Field(default="data/llm.log", description="LLM服务日志文件")
    readwise: str = Field(default="data/readwise.log",
                          description="Readwise服务日志文件")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    files: LoggingFilesConfig = Field(
        default_factory=LoggingFilesConfig, description="日志文件配置")


class AuthConfig(BaseModel):
    """认证配置"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class ApiConfig(BaseModel):
    """API配置"""
    openrouter_key: str = Field(..., description="OpenRouter API密钥")
    readwise_token: str = Field(..., description="Readwise API令牌")


class ProxyConfig(BaseModel):
    """代理配置"""
    type: str = Field(..., description="代理类型：http 或 socks5")
    url: str = Field(..., description="代理URL")


class MainConfig(BaseModel):
    """主配置模型"""
    prompts: List[PromptConfig] = Field(
        default_factory=list, description="Prompt配置列表")
    queue: QueueConfig = Field(default_factory=QueueConfig, description="队列配置")
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="数据库配置")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="日志配置")


class SecretsConfig(BaseModel):
    """敏感信息配置模型"""
    auth: AuthConfig = Field(..., description="认证配置")
    api: ApiConfig = Field(..., description="API配置")
    proxy: Optional[ProxyConfig] = Field(default=None, description="代理配置")


class AppConfig(BaseModel):
    """完整应用配置模型"""
    # 主配置
    prompts: List[PromptConfig] = Field(
        default_factory=list, description="Prompt配置列表")
    queue: QueueConfig = Field(default_factory=QueueConfig, description="队列配置")
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="数据库配置")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="日志配置")

    # 敏感信息配置
    auth: AuthConfig = Field(..., description="认证配置")
    api: ApiConfig = Field(..., description="API配置")
    proxy: Optional[ProxyConfig] = Field(default=None, description="代理配置")

    @classmethod
    def load_from_files(
        cls,
        config_path: str = "config/config.yaml",
        secrets_path: str = "config/secrets.yaml"
    ) -> "AppConfig":
        """从配置文件加载配置"""
        # 加载主配置文件
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        main_config_data = cls._load_yaml_with_env(config_path)

        # 加载敏感信息配置文件
        if not os.path.exists(secrets_path):
            raise FileNotFoundError(f"敏感信息配置文件不存在: {secrets_path}")

        secrets_data = cls._load_yaml_with_env(secrets_path)

        # 合并配置
        config_data = {**main_config_data, **secrets_data}

        return cls(**config_data)

    @staticmethod
    def _load_yaml_with_env(file_path: str) -> Dict[str, Any]:
        """加载YAML文件并处理环境变量"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 处理环境变量占位符 ${ENV_VAR:-default_value}
            def replace_env_vars(match):
                var_expr = match.group(1)
                if ":-" in var_expr:
                    env_var, default_value = var_expr.split(":-", 1)
                    return os.getenv(env_var, default_value)
                else:
                    return os.getenv(var_expr, "")

            content = re.sub(r"\$\{([^}]+)\}", replace_env_vars, content)
            return yaml.safe_load(content) or {}
        except Exception as e:
            raise RuntimeError(f"配置文件加载失败 {file_path}: {e}")

    def get_prompts_dict(self) -> Dict[str, Dict[str, Any]]:
        """获取prompt内容，按site URL匹配"""
        prompts_dict = {}

        for item in self.prompts:
            # 使用site列表作为key，包含prompt和refetch_content的字典作为value
            prompts_dict[tuple(item.site)] = {
                "prompt": item.prompt,
                "refetch_content": item.refetch_content
            }

        return prompts_dict

    def get_auth_dict(self) -> Dict[str, str]:
        """获取认证配置字典"""
        return {
            "username": self.auth.username,
            "password": self.auth.password,
        }

    def get_api_dict(self) -> Dict[str, str]:
        """获取API配置字典"""
        return {
            "openrouter_key": self.api.openrouter_key,
            "readwise_token": self.api.readwise_token,
        }

    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """获取代理配置字典"""
        if self.proxy:
            return {
                "type": self.proxy.type,
                "url": self.proxy.url,
            }
        return None

    def get_queue_dict(self) -> Dict[str, Any]:
        """获取队列配置字典"""
        return {
            "retry_times": self.queue.retry_times,
            "dead_letter_retry_daily": self.queue.dead_letter_retry_daily,
            "process_interval_seconds": self.queue.process_interval_seconds,
        }

    def get_logging_dict(self) -> Dict[str, str]:
        """获取日志配置字典"""
        return {
            "level": self.logging.level,
            "format": self.logging.format,
        }
