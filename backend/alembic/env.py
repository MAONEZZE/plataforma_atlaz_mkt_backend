import os
from dotenv import load_dotenv

load_dotenv()

from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context
from app.shared.infrastructure.sqlalchemy_base import Base

# Alembic Config object
config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

# Import all ORM models here so autogenerate finds them.
# (Add imports as each context is implemented.)

target_metadata = Base.metadata

DATABASE_URL = os.environ["DATABASE_URL"]
# Convert async URL to sync for alembic
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(SYNC_DATABASE_URL)
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
