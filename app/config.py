import sys
from pathlib import Path
import importlib.util
import configparser
from commentedconfigparser import CommentedConfigParser

LOCAL_PATH = Path(__file__).parent / "config"
CONTAINER_PATH = Path("/config")
CURRENT_CONFIG_VERSION = 2


def _find_config() -> Path | None:
    if sys.platform != "win32" and CONTAINER_PATH.exists():
        return CONTAINER_PATH
    if LOCAL_PATH.exists():
        return LOCAL_PATH
    return None


def get_html_template(name: str) -> str | None:
    """Load an HTML template from the config directory.

    Returns the template content as a string, or ``None`` when the config
    directory cannot be found or the template file does not exist.
    """
    config_dir = _find_config()
    if config_dir is None:
        return None
    tmpl_path = config_dir / f"{name}.html"
    if tmpl_path.exists():
        with tmpl_path.open(encoding="utf-8") as template_file:
            return template_file.read()
    return None


def run_migration_module(config_parser: CommentedConfigParser, migration_path: Path) -> None:
    """Load and run a migration module from a file path.

    The module must expose a `migrate(config_parser)` function.
    """
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load migration module from {migration_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "migrate"):
        raise AttributeError(f"Migration {migration_path} has no migrate(config) function")
    module.migrate(config_parser)


_config_dir = _find_config() / "settings.conf"
if not _config_dir.exists():
    raise FileNotFoundError(
        f"No configuration directory found. Expected {LOCAL_PATH} or {CONTAINER_PATH}."
    )

# Load configuration
config = configparser.ConfigParser()
config.read(_config_dir, encoding="UTF-8")

try:
    CURRENT_VERSION = int(config.get("General", "config_version", fallback="1"))
except ValueError:
    CURRENT_VERSION = 1

if CURRENT_VERSION < CURRENT_CONFIG_VERSION:
    print(f"Config version {CURRENT_VERSION} detected. Migrating to version {CURRENT_CONFIG_VERSION}.")
    migrations_dir = Path(__file__).parent / "migrations"

    # Use a separate CommentedConfigParser instance for migration to avoid losing comments
    # Always reading using this does not work with array like syntax at mail_html_to_md
    config_migrator = CommentedConfigParser()
    config_migrator.read(_config_dir, encoding="UTF-8")

    for v in range(CURRENT_VERSION, CURRENT_CONFIG_VERSION):
        print(f"Running migration to version {v + 1}.")
        migration_file = migrations_dir / f"migration_{v+1}.py"
        if not migration_file.exists():
            raise FileNotFoundError(f"Missing migration file: {migration_file}")
        run_migration_module(config_migrator, migration_file)
        # update version in config and persist after each migration
        config_migrator.set("General", "config_version", str(v + 1))
        with _config_dir.open("w", encoding="UTF-8") as f:
            config_migrator.write(f)
        print(f"Migration to version {v + 1} completed.")

    del config_migrator
    # Refresh the config object to reflect the migrated settings
    config.read(_config_dir, encoding="UTF-8")
