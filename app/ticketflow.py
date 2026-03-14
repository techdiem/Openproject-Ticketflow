# Version: 2.1.0
"""
OpenProject-Ticketflow
Bridge between mail and OpenProject API, to use work packages like a ticket system.

© 2026 github.com/TechDiem
"""
import signal
import sys
import threading
import urllib3

from config import config
from logger import logger
from processes.mailprocess import MailProcess
from processes.notificationprocess import NotificationProcess


def _polling_thread(
    interval: float,
    fn,
    name: str,
    stop_event: threading.Event,
) -> None:
    """Call *fn()* repeatedly, sleeping *interval* seconds between runs.

    Exits when *stop_event* is set.  Uses ``stop_event.wait()`` as the sleep
    so a shutdown signal wakes the thread immediately instead of waiting out
    the full interval.
    """
    while not stop_event.is_set():
        logger.info("[%s] Starting run …", name)
        try:
            fn()
        except Exception as exc:
            logger.error("[%s] Unhandled error: %s", name, exc)
        logger.info("[%s] Next run in %.0f s.", name, interval)
        stop_event.wait(timeout=interval)


def main() -> None:
    if not config.getboolean("OpenProject", "https_verification"):
        logger.warning(
            "TLS certificate verification is disabled! "
            "→ Insecure connection to the OpenProject API!"
        )
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    mail_process = MailProcess()
    notification_process = NotificationProcess()

    # Single shared stop event – set by signal handlers or KeyboardInterrupt
    stop_event = threading.Event()

    def _request_shutdown(*_) -> None:
        logger.info("Shutdown signal received – stopping Ticketflow …")
        stop_event.set()

    signal.signal(signal.SIGINT, _request_shutdown)
    # SIGTERM is not fully supported on Windows, but works correctly on Linux/macOS
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, _request_shutdown)

    # --- Choose mail reception strategy ---
    use_idle = MailProcess.probe_idle_support()

    notify_interval = config.getfloat(
        "Scheduler", "notification_interval_seconds", fallback=60.0
    )

    threads: list[threading.Thread] = []

    if use_idle:
        threads.append(
            threading.Thread(
                target=mail_process.run_idle_loop,
                args=(stop_event,),
                name="mail_idle",
                daemon=True,
            )
        )
    else:
        mail_interval = config.getfloat("Scheduler", "mail_interval_seconds", fallback=60.0)
        logger.info("[Scheduler] Polling mode – mail interval %.0f s.", mail_interval)
        threads.append(
            threading.Thread(
                target=_polling_thread,
                args=(mail_interval, mail_process.run, "MailProcess/Poll", stop_event),
                name="mail_poll",
                daemon=True,
            )
        )

    threads.append(
        threading.Thread(
            target=_polling_thread,
            args=(notify_interval, notification_process.run, "NotificationProcess", stop_event),
            name="notification_poll",
            daemon=True,
        )
    )

    mail_strategy = "IDLE" if use_idle else "polling"
    logger.info(
        "Ticketflow started. Mail strategy: %s. Notification interval: %.0f s.",
        mail_strategy,
        notify_interval,
    )

    for t in threads:
        t.start()

    # Block the main thread until a shutdown signal arrives
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received – stopping Ticketflow …")
        stop_event.set()

    logger.info("Waiting for worker threads to finish …")
    for t in threads:
        t.join(timeout=10)
        if t.is_alive():
            logger.warning("Thread '%s' did not stop within 10 s.", t.name)

    logger.info("Ticketflow stopped, bye.")


if __name__ == "__main__":
    main()
