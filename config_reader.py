import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from dotenv import load_dotenv
import os


class Settings(BaseSettings):
    bot_token: SecretStr
    db_link: str
    db_link_async: str
    secret_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


load_dotenv()

config = Settings()

base_dir = os.path.dirname(os.path.abspath(__file__))
db_link = os.getenv("DB_LINK")
db_link_async = os.getenv("DB_LINK_ASYNC")
secret_key = os.getenv("SECRET_KEY")