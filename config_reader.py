import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from dotenv import load_dotenv
import os


class Settings(BaseSettings):
    bot_token: SecretStr
    db_link: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


load_dotenv()

config = Settings()

base_dir = os.path.dirname(os.path.abspath(__file__))
db_link = os.getenv("DB_LINK")