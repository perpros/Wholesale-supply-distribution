import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add project root to sys.path
# Assuming env.py is in alembic/ and project root is one level up.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Custom part for our application ---
# Import Base from your models and settings
from app.db.base import Base  # Corrected: Base is exported from app.db.base
from app.core.config import settings as app_settings # Your application settings
# Get the constructed URI directly from app_settings or build it as in session.py
# For simplicity, let's assume app_settings are loaded and URI might need construction if not already done.
# app.db.session.SQLALCHEMY_DATABASE_URI is formed AFTER settings are loaded.
# A better way is to ensure settings.SQLALCHEMY_DATABASE_URI is populated.
if not app_settings.SQLALCHEMY_DATABASE_URI:
    app_settings.SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{app_settings.POSTGRES_USER}:{app_settings.POSTGRES_PASSWORD}@{app_settings.POSTGRES_SERVER}/{app_settings.POSTGRES_DB}"

SQLALCHEMY_DATABASE_URI = app_settings.SQLALCHEMY_DATABASE_URI

# Set the SQLAlchemy URL from your application settings
# This overrides the sqlalchemy.url from alembic.ini
config.set_main_option('sqlalchemy.url', SQLALCHEMY_DATABASE_URI)

target_metadata = Base.metadata
# --- End of custom part ---

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
        compare_type=True, # Detect column type changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    # Use the engine from our application's session.py or create one from settings
    # This ensures consistency with how the app connects.
    from app.db.session import engine as app_engine

    connectable = app_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True, # Detect column type changes
            compare_server_default=True, # Detect server default changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
