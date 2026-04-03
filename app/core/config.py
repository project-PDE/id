import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорировать лишние переменные
    )

    NAME: str = Field(default="ID", description="Название приложения")
    HOST: str = Field(default="127.0.0.1", description="Хост приложения")
    PORT: str = Field(default="8000", description="Порт приложения")
    DATABASE_URL: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432", description="URL базы данных")
    JWT_SECRET_KEY: str = Field(default="change_me_to_a_long_random_secret", description="Секретный ключ для подписи JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм подписи JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Время жизни access токена в минутах")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=365, description="Время жизни refresh токена в днях")


IN_DOCKER = os.getenv("IN_DOCKER", "").lower() in ("1", "true", "yes")
env_path = Path(".env")

if not IN_DOCKER and not env_path.exists():
    if not env_path.exists():
        with open(env_path, "w", encoding="utf-8") as f:
            for field_name, field_info in ConfigSettings.model_fields.items():
                desc = field_info.description or ""
                default = field_info.get_default()
                if isinstance(default, bool):
                    default = "true" if default else "false"
                else:
                    default = str(default)

                f.write(f"# {desc}\n")
                f.write(f"{field_name}={default}\n\n")

        raise RuntimeError(
            "Файл .env не найден и был создан со шаблоном.\n"
            "Отредактируйте параметры перед запуском:\n"
            f"- Файл: {env_path.absolute()}"
        )

# Создание экземпляра конфигурации
config = ConfigSettings()
