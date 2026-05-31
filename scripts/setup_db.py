"""
Создаёт базу данных и применяет миграции.
Запуск: python -m scripts.setup_db
"""
import asyncio
import os
from urllib.parse import urlparse

import asyncpg
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

load_dotenv()


def _parse_url(database_url: str) -> dict:
    # strip SQLAlchemy driver prefix: postgresql+asyncpg:// → postgresql://
    clean = database_url.replace("+asyncpg", "")
    p = urlparse(clean)
    return {
        "host": p.hostname,
        "port": p.port or 5432,
        "user": p.username,
        "password": p.password,
        "database": p.path.lstrip("/"),
    }


async def create_database() -> None:
    url = os.environ["DATABASE_URL"]
    params = _parse_url(url)
    db_name = params.pop("database")

    # Connect to the default 'postgres' system database to run CREATE DATABASE
    conn = await asyncpg.connect(**params, database="postgres")
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if exists:
            print(f"  База '{db_name}' уже существует, пропускаем.")
        else:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"  База '{db_name}' создана.")
    finally:
        await conn.close()


def run_migrations() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    print("  Миграции применены.")


if __name__ == "__main__":
    print("→ Создание базы данных...")
    asyncio.run(create_database())

    print("→ Применение миграций...")
    run_migrations()

    print("\n✅ Готово.")
