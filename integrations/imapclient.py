from imap_tools import MailBox, BaseMailBox, MailBoxUnencrypted, MailBoxTls
from config import config
from model.mailintern import MailIntern

class IMAPClient():
    def __init__(self) -> None:
        self.mailbox = self.connect_mailbox()

    def connect_mailbox(self):
        #Check mailbox encryption standard
        connectBox = BaseMailBox
        if config.get("IMAP", "encryption") == "tls":
            connectBox = MailBoxTls
        elif config.get("IMAP", "encryption") == "ssl":
            connectBox = MailBox
        else:
            connectBox = MailBoxUnencrypted

        #Connect IMAP
        return connectBox(config.get("IMAP", "server")).login(config.get("IMAP", "user"), config.get("IMAP", "password"))
    
    def check_mail(self):
        mails = []
        #Iterate over inbox and process mails
        for msg in self.mailbox.fetch(mark_seen=False):
            print(f"{msg.date} {msg.subject} | {len(msg.text or msg.html)} Bytes, {len(msg.attachments)} Anhänge")

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