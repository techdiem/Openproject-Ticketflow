'''
OpenProject-Ticketflow
Bridge between mail and OpenProject API, to use work packages like a ticket system.

© 2024 github.com/TechDiem
Version: 1.0.0
'''
import urllib3
from config import config
from logger import logger
from processes.mailprocess import MailProcess
from processes.notificationprocess import NotificationProcess

def main():
    if not config.getboolean("OpenProject", "https_verification"):
        logger.warning("Critical: HTTPS Zertifikats-Verifikation ist deaktiviert! \
-> Unsichere Verbindung zur OpenProject-API!")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    mail_process = MailProcess()
    mail_process.run()
    notification_process = NotificationProcess()
    notification_process.run()

if __name__ == "__main__":
    main()
