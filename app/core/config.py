import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

    APP_NAME: str = "langfast-2api"
    APP_VERSION: str = "1.0.0"
    DESCRIPTION: str = "一个将 langfa.st 转换为兼容 OpenAI 格式 API 的高性能代理。"

    # --- 安全与部署 ---
    API_MASTER_KEY: Optional[str] = "1"
    NGINX_PORT: int = 8088

    # --- 上游 API ---
    SUPABASE_URL: str = "https://yzaaxwkjukajpwqflndu.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl6YWF4d2tqdWthanB3cWZsbmR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxNTgzNzUsImV4cCI6MjA1ODczNDM3NX0.tDu7BsFUOV4aPo8U-dsokQJSRw29LQWT8JfDqQe5MoI"
    SOCKET_URL: str = "wss://langfast-prompt-runner-35808038077.us-central1.run.app"
    
    # --- 凭证池配置 ---
    MIN_CREDENTIALS: int = 5
    MAX_CREDENTIALS: int = 10

    # --- 模型列表 ---
    KNOWN_MODELS: List[str] = [
        "gpt-5", "gpt-5-mini", "gpt-5-nano",
        "gpt-4.5-preview", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
        "gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o3", "o3-mini", "o4-mini",
        "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"
    ]
    DEFAULT_MODEL: str = "gpt-4o-mini"

settings = Settings()
