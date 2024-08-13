#
# OpenProject-Ticketflow
#

from processes.mailprocess import MailProcess
from processes.notificationprocess import NotificationProcess
from config import config

def main():
    # mailProcess = MailProcess()
    # mailProcess.run()
    if config.get('Workflow', 'comment_to_mail') == "true":
        notificationProcess = NotificationProcess()
        notificationProcess.run()

if __name__ == "__main__":
    main()
