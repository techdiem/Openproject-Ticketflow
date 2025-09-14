from imap_tools import MailBox, MailBoxUnencrypted, MailBoxTls
from config import config
from model.mail_intern import MailIntern
from logger import logger

class IMAPClient():
    def __init__(self) -> None:
        self.mailbox = self.connect_mailbox()

    def connect_mailbox(self):
        #Check mailbox encryption standard
        connect_box = None
        if config.get("IMAP", "encryption") == "tls":
            connect_box = MailBoxTls
        elif config.get("IMAP", "encryption") == "ssl":
            connect_box = MailBox
        else:
            connect_box = MailBoxUnencrypted

        #Connect IMAP
        #TODO handle MailBoxLoginError
        return connect_box(config.get("IMAP", "server")).login(config.get("IMAP", "user"),
                                                              config.get("IMAP", "password"))

    def check_mail(self):
        mails = []
        #Iterate over inbox and process mails
        for msg in self.mailbox.fetch(mark_seen=False):
            logger.info("%s %s | %s Bytes, %s Anhänge",
                        msg.date,
                        msg.subject,
                        len(msg.text or msg.html),
                        len(msg.attachments))

            #Handle empty subject
            subject = "Kein Titel" if msg.subject == "" else msg.subject

            mail = MailIntern(msg.uid,
                              subject,
                              msg.text,
                              msg.html,
                              msg.from_values,
                              msg.attachments)
            mails.append(mail)

        return mails
