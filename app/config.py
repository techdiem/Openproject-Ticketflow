import configparser
import sys
from pathlib import Path

LOCAL_PATH = Path(__file__).parent / "settings.conf"
CONTAINER_PATH = Path("/config/settings.conf")

def _find_config() -> Path:
    if LOCAL_PATH.exists():
        return LOCAL_PATH
    if sys.platform != "win32" and CONTAINER_PATH.exists():
        return CONTAINER_PATH
    # Fallback: lokaler Pfad
    return None

config = configparser.ConfigParser()
_config_path = _find_config()
if (_config_path is None):
    raise FileNotFoundError("No configuration file found at expected locations.")
config.read(_config_path, encoding="UTF-8")
