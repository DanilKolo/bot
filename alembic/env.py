import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from dotenv import load_dotenv

from alembic import context

# === НАШІ ІМПОРТИ ===
from db import Base
import models  # Обов'язково імпортуємо моделі

# Явно завантажуємо файл .env з кореня проєкту
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск міграцій в режимі 'Offline'."""
    # Зчитуємо рядок з .env
    url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_migrations():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, 
        target_metadata=target_metadata
    )

    # Замість begin_migrations() викликаємо напряму run_migrations()
    context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск міграцій в режимі 'Online'."""
    alembic_config = config.get_section(config.config_ini_section) or {}
    
    # Зчитуємо рядок з .env
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
    alembic_config["sqlalchemy.url"] = db_url

    connectable = async_engine_from_config(
        alembic_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())