#
# OpenProject-Ticketflow
#

from processes.mailprocess import mail_process
from processes.notificationprocess import notification_process

def main():
    mail_process()
    notification_process()

if __name__ == "__main__":
    main()
