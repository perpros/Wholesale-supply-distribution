from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Import settings from the application to use the same DATABASE_URL
from backend.app.core.config import settings as app_settings

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the sqlalchemy.url in the Alembic config object from application settings
# This ensures Alembic uses the same database URL as the application
config.set_main_option("sqlalchemy.url", app_settings.DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
from backend.app.database import Base  # Import Base
# Import all your models here so Base knows about them for Alembic autogenerate
import backend.app.models.user
import backend.app.models.request
import backend.app.models.proposal
import backend.app.models.request_status_history
# The __init__.py in backend/app/models/ also imports these,
# so just importing that might be an alternative if it imports all models into its namespace.
# e.g., import backend.app.models
target_metadata = Base.metadata  # Set target_metadata

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
    # Use the URL from app_settings directly for offline mode
    # url = config.get_main_option("sqlalchemy.url") # This would read from alembic.ini if not overridden
    context.configure(
        url=app_settings.DATABASE_URL, # Use app_settings directly
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use a configuration dictionary derived from app_settings for online mode
    # This avoids using engine_from_config which relies on alembic.ini sections
    configuration = config.get_section(config.config_ini_section)
    if configuration is None: # Should not happen if alembic.ini is present
        configuration = {}
    configuration["sqlalchemy.url"] = app_settings.DATABASE_URL # Override with app settings

    connectable = engine_from_config(
        configuration, # Use the modified configuration
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Original online mode setup:
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
