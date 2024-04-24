from imap_tools import MailBox, BaseMailBox, MailBoxUnencrypted, MailBoxTls
import json
from config import config
from workpackage import Workpackage

def create_workpackage(subject, message, attachments, text_format):
    ticket = Workpackage(subject, message, text_format)
    result = ticket.publish()
    try:
        ticket.id = json.loads(result.content)["id"]
        print(f"Ticket {ticket.title} erstellt, ID {ticket.id}")
    except:
        print(f"Fehler beim Erstellen des Arbeitspaketes {ticket.title}!\n{result.content}")
        raise RuntimeError
    else:
        #Save attachments
        for attachment in attachments:
            print(f"Anhang {attachment.filename} vom Typ {attachment.content_type} gefunden.")
            try:
                result = ticket.add_attachment(attachment.filename, attachment.payload)
            except:
                print(f"Fehler beim hinzufügen des Anhangs {attachment.filename}!\n{result.content}")
                raise RuntimeError

def connect_mailbox():
    #Check mailbox encryption standard
    connectBox = BaseMailBox
    if config.get("IMAP", "encryption") == "tls":
        connectBox = MailBoxTls
    elif config.get("IMAP", "encryption") == "ssl":
        connectBox = MailBox
    else:
        connectBox = MailBoxUnencrypted

    #Connect IMAP
    box = connectBox(config.get("IMAP", "server")).login(config.get("IMAP", "user"), config.get("IMAP", "password"))
    return box


#Read config for mail senders which mails are imported as html
mail_html_to_md = json.loads(config.get("Workflow", "mail_html_to_md"))

mailbox = connect_mailbox()

#Iterate over inbox and process mails
for msg in mailbox.fetch(mark_seen=False):
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
    #Add heading
    message = f"Absender: {msg.from_values.full}\n---------\n{text_message}"
    
    #Create ticket
    try:
        create_workpackage(subject, message, msg.attachments, text_format)
    except RuntimeError:
        pass
    else:
        #Delete Mail
        mailbox.delete(msg.uid)

#Close IMAP connection
mailbox.client.close()
