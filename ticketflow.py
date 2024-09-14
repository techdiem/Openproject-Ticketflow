#
# OpenProject-Ticketflow
#

import urllib3
from config import config
from logger import logger
from processes.mailprocess import MailProcess
from processes.notificationprocess import NotificationProcess

def main():
    if config.get("OpenProject", "https_verification") == "false":
        logger.warning("Critical: HTTPS Zertifikats-Verifikation ist deaktiviert! \
                       -> Unsichere Verbindung zur OpenProject-API!")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    mail_process = MailProcess()
    mail_process.run()
    notification_process = NotificationProcess()
    notification_process.run()

if __name__ == "__main__":
    main()
