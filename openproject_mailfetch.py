import imaplib
import email
import os
import json
from config import config

from mail import Mail
from workpackage import Workpackage


#IMAP connection
mail = imaplib.IMAP4(config.get("IMAP", "server"))
mail.login(config.get("IMAP", "user"), config.get("IMAP", "password"))
mail.select()

#Get inbox
typ, data = mail.search(None, 'ALL')

tickets = []

for num in data[0].split():
    status, data = mail.fetch(num, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])
    message = Mail(msg, num)
    print(f"Mail von {message.sender}, Betreff: {message.subject}")
    #Create Workpackage object
    tickets.append(Workpackage(message))

for ticket in tickets:
    #Publish work_package and extract id
    result = ticket.publish()
    try:
        ticket.id = json.loads(result.content)["id"]
        print("Ticket erstellt: ", ticket.id)
    except:
        print(f"Fehler beim Erstellen eines Arbeitspaketes!\n\n{result.content}")
    else:
        #Delete Mail
        mail.store(ticket.message.imappointer, "+FLAGS", "\\Deleted")
        #Save attachments
        for attachment in ticket.message.attachments:
            ticket.add_attachment(attachment[0], attachment[1])

#Logout mail
mail.close()
mail.logout()