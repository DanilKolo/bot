import os
from pydantic_settings import BaseSettings, SettingsConfigDict

current_dir = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    BOT_TOKEN: str
    GEMINI_API_KEY: str
    
    # Конфігурація БД (беремо значення за замовчуванням, якщо немає в .env)
    DB_USER: str = "danil_user"
    DB_PASSWORD: str = "super_password123"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "rag_bot_database"

    @property
    def database_url(self) -> str:
        """Формує URL підключення для SQLAlchemy Async"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=os.path.join(current_dir, '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()