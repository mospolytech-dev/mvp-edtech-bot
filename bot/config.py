from dataclasses import dataclass, field
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    bot_token: str
    database_url: str
    admin_ids: frozenset[int] = field(default_factory=frozenset)


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    database_url = os.getenv("DATABASE_URL")
    admin_ids_raw = os.getenv("ADMIN_IDS", "")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")
    if not database_url:
        raise ValueError("DATABASE_URL is not set")

    admin_ids = frozenset(
        int(x.strip()) for x in admin_ids_raw.split(",") if x.strip().isdigit()
    )

    return Config(bot_token=bot_token, database_url=database_url, admin_ids=admin_ids)


config = load_config()
