"""集中配置。敏感信息只从 .env 读取，代码不硬编码。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    # SQLite 相对路径以启动目录为准（从 backend/ 启动 → backend/data/weilan.db）
    database_url: str = "sqlite:///data/weilan.db"
    collect_interval_minutes: int = 45
    collect_timeout_seconds: int = 20

    # 大模型（OpenAI 兼容接口，可切 DeepSeek 官方或火山方舟）
    model_api_key: str = ""
    model_base_url: str = "https://api.deepseek.com"
    model_name: str = "deepseek-chat"
    model_timeout_seconds: int = 120
    model_max_retries: int = 2

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
