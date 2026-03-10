from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.database import Base
from app import models

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


import asyncio
from sqlalchemy.ext.asyncio import create_async_engine


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    
    # 1. Look for the Railway/Docker environment variable first
    url = os.getenv("DATABASE_URL")
    
    # 2. If the variable is missing (like on your local laptop), 
    # fallback to the URL in alembic.ini
    if not url:
        url = config.get_main_option("sqlalchemy.url")

    # 3. Create the Async Engine (Using asyncpg)
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    # 4. Bridge function to run sync migrations inside the async connection
    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    # 5. Async helper to manage the connection
    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    # 6. Execute the migration loop
    try:
        asyncio.run(run_async_migrations())
    except RuntimeError:
        # Fallback if an event loop is already running
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_async_migrations())

# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode using an async engine."""
    
#     # Get the URL from your environment variables
#     # (Railway's DATABASE_URL with +asyncpg)
#     url = config.get_main_option("sqlalchemy.url")

#     # Create the Async Engine
#     connectable = create_async_engine(url, poolclass=pool.NullPool)

#     # Bridge function to run sync migrations inside the async connection
#     def do_run_migrations(connection):
#         context.configure(connection=connection, target_metadata=target_metadata)
#         with context.begin_transaction():
#             context.run_migrations()

#     # Async helper to manage the connection
#     async def run_async_migrations():
#         async with connectable.connect() as connection:
#             await connection.run_sync(do_run_migrations)
#         await connectable.dispose()

#     # Run the loop
#     try:
#         asyncio.run(run_async_migrations())
#     except Exception:
#         # This handles cases where a loop is already running
#         loop = asyncio.get_event_loop()
#         loop.run_until_complete(run_async_migrations())

# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode.

#     In this scenario we need to create an Engine
#     and associate a connection with the context.

#     """
#     connectable = engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection, target_metadata=target_metadata
#         )

#         with context.begin_transaction():
#             context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
