import logging
import sys
from config import config


def _build_logger() -> logging.Logger:
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s]: %(message)s")

    log = logging.getLogger("ticketflow")
    log.setLevel(logging.INFO)
    # Avoid double handlers
    if log.handlers:
        return log

    fh = logging.FileHandler(
        config.get("General", "logfile"), mode="a", encoding="utf-8"
    )
    fh.setFormatter(fmt)
    log.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    log.addHandler(ch)

    return log


logger = _build_logger()
logger.info("Logging initialized")
