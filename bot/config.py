from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    bot_token: str
    database_url: str


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    database_url = os.getenv("DATABASE_URL")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set in environment variables")
    if not database_url:
        raise ValueError("DATABASE_URL is not set in environment variables")

    return Config(
        bot_token=bot_token,
        database_url=database_url,
    )


config = load_config()
