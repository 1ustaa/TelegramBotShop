from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from dotenv import load_dotenv
import os


class Settings(BaseSettings):
    bot_token: SecretStr
    db_link: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


load_dotenv()

config = Settings()

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "data", "shop.db")
db_link = f"sqlite:///{db_path}"