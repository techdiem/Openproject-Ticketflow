from imap_tools import MailBox, BaseMailBox, MailBoxUnencrypted, MailBoxTls
from config import config
import json

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
        #Read config for mail senders which mails are imported as html
        mail_html_to_md = json.loads(config.get("Workflow", "mail_html_to_md"))

        mails = []
        #Iterate over inbox and process mails
        for msg in self.mailbox.fetch(mark_seen=False):
            print(f"{msg.date} {msg.subject} | {len(msg.text or msg.html)} Bytes, {len(msg.attachments)} Anhänge")

            #Handle empty subject
            subject = "Kein Titel" if msg.subject == "" else msg.subject

            #Check which text bodies exist
            text_bodies = {}
            text_message = ""
            if len(msg.text) != 0: text_bodies["textile"] = msg.text
            if len(msg.html) != 0: text_bodies["html"] = msg.html
            if len(text_bodies) == 0: text_bodies["textile"] = "Kein Text"
            #Select html on whitelisted addresses
            if (len(text_bodies) == 2 and msg.from_values.email in mail_html_to_md) or not "textile" in text_bodies:
                text_message = text_bodies["html"]
                text_format = "html"
            else:
                text_message = text_bodies["textile"]
                text_format = "textile"
            
            mail = [msg.uid, subject, text_message, msg.from_values, msg.attachments, text_format]
            mails.append(mail)

        return mails