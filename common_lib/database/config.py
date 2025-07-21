from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None

    APP_NAME: Optional[str] = None
    APP_DESCRIPTION: Optional[str] = None
    DEBUG: Optional[bool] = None
    API_VERSION: Optional[str] = None

    RABBITMQ_HOST: str = 'rabbitmq'
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = 'rmuser'
    RABBITMQ_PASS: str = 'rmpassword'
    RABBITMQ_VHOST: str = '/'
    QUEUE_NAME: str = 'ml_task_queue'

    SECRET_KEY: str = "a_very_weak_default_secret_key_replace_in_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COOKIE_NAME: str = "my_app_session_cookie"

    INITIAL_BALANCE: int = 10



    @property
    def DATABASE_URL_asyncpg(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    @property
    def DATABASE_URL_psycopg(self):
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    def validate(self) -> None:
        if not all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            raise ValueError("Missing required database configuration")
@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
