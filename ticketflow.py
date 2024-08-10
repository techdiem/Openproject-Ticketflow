#
# OpenProject-Ticketflow
#

from processes.mailprocess import mail_process
from processes.notificationprocess import NotificationProcess

def main():
    mail_process()
    notificationProcess = NotificationProcess
    notificationProcess.run()

if __name__ == "__main__":
    main()
