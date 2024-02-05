from imap_tools import MailBox
import json
from config import config

from workpackage import Workpackage

#Connect IMAP
mailbox = MailBox(config.get("IMAP", "server")).login(config.get("IMAP", "user"), config.get("IMAP", "password"))

for msg in mailbox.fetch(mark_seen=False):
    print(f"{msg.date} {msg.subject} | {len(msg.text or msg.html)} Bytes, {len(msg.attachments)} Anhänge")

    subject = "Kein Titel" if msg.subject == "" else msg.subject
    message = ""
    if (len(msg.text) != 0):
        message = f"Absender: {msg.from_values.full}\n---------\n{msg.text}"
    elif (len(msg.html) != 0):
        message = f"Absender: {msg.from_values.full}\n---------\n{msg.html}"
    else:
        message = f"Absender: {msg.from_values.full}\n---------\nKein Text"
    ticket = Workpackage(subject, message)
    result = ticket.publish()
    try:
        ticket.id = json.loads(result.content)["id"]
        print(f"Ticket {ticket.title} erstellt, ID {ticket.id}")
    except:
        print(f"Fehler beim Erstellen des Arbeitspaketes {ticket.title}!\n{result.content}")
    else:
        #Save attachments
        for attachment in msg.attachments:
            print(f"Anhang {attachment.filename} vom Typ {attachment.content_type} gefunden.")
            try:
                result = ticket.add_attachment(attachment.filename, attachment.payload)
            except:
                print(f"Fehler beim hinzufügen des Anhangs {attachment.filename}!\n{result.content}")
                break
        #Delete Mail
        mailbox.delete(msg.uid)

#Close IMAP connection
mailbox.client.close()
