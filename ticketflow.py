#
# OpenProject-Ticketflow
#

from processes.mailprocess import MailProcess
from processes.notificationprocess import NotificationProcess
from config import config
from logger import logger
import urllib3

def main():
    if config.get("OpenProject", "https_verification") == "false":
        logger.warning("Critical: HTTPS Zertifikats-Verifikation ist deaktiviert! -> Unsichere Verbindung zur OpenProject-API!")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    mailProcess = MailProcess()
    mailProcess.run()
    if config.get('Workflow', 'comment_to_mail') == "true":
        notificationProcess = NotificationProcess()
        notificationProcess.run()

if __name__ == "__main__":
    main()
