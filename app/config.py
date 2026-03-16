import configparser
import sys
from pathlib import Path

LOCAL_PATH = Path(__file__).parent / "config"
CONTAINER_PATH = Path("/config")


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
        with tmpl_path.open(encoding="utf-8") as f:
            return f.read()
    return None


_config_dir = _find_config() / "settings.conf"
if not _config_dir.exists():
    raise FileNotFoundError(
        f"No configuration directory found. Expected {LOCAL_PATH} or {CONTAINER_PATH}."
    )
config = configparser.ConfigParser()
config.read(_config_dir, encoding="UTF-8")
