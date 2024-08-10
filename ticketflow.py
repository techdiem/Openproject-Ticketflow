#
# OpenProject-Ticketflow
#

from processes.mailprocess import MailProcess
from processes.notificationprocess import NotificationProcess

def main():
    mailProcess = MailProcess()
    mailProcess.run()
    notificationProcess = NotificationProcess()
    notificationProcess.run()

if __name__ == "__main__":
    main()
