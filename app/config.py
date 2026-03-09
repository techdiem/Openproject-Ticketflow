import configparser
import sys
from pathlib import Path

LOCAL_PATH = Path(__file__).parent / "config"
CONTAINER_PATH = Path("/config")

def _find_config() -> Path:
    if LOCAL_PATH.exists():
        return LOCAL_PATH
    if sys.platform != "win32" and CONTAINER_PATH.exists():
        return CONTAINER_PATH
    # Fallback: lokaler Pfad
    return None

def get_html_template(name: str) -> str:
    """Load an HTML template from the config directory."""
    tmpl_path = _find_config() / f"{name}.html"
    if tmpl_path.exists():
        with tmpl_path.open(encoding="utf-8") as f:
            return f.read()
    return None

config = configparser.ConfigParser()
_config_path = _find_config() / "settings.conf"
if _config_path is None:
    raise FileNotFoundError("No configuration file found at expected locations.")
config.read(_config_path, encoding="UTF-8")
