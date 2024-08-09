
import json
from config import config
from markdown import markdown
from bs4 import BeautifulSoup
from integrations.workpackage import Workpackage
from integrations.imapclient import IMAPClient
from integrations.comment import Comment
from integrations.notification import Notification
from integrations.smtpclient import SMTPClient

def create_workpackage(subject, message, from_values, attachments, text_format):
    #Add sender heading
    message = f"Absender: {from_values.full}\n---------\n{message}"
    ticket = Workpackage(subject, message, from_values.email, text_format)
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

print("Verarbeite eingehende Mails via IMAP")
imapclient = IMAPClient()
newmails = imapclient.check_mail()

for mail in newmails:
    try:
        create_workpackage(mail[1], mail[2], mail[3], mail[4], mail[5])
    except RuntimeError:
        pass
    else:
        #Delete Mail
        imapclient.mailbox.delete(mail[0])
#Close IMAP connection
imapclient.mailbox.client.close()

print("Verarbeite neue OpenProject-Benachrichtigungen")
notifications = Notification.getNotificationCollection()
for notify in notifications:
    print("Found notification with id", notify.id)
    if notify.reason == "commented":
        print("It is a comment notification")
        try:
            comment = Comment.getByActivityID(notify.activityID)
            html = markdown(comment.rawtext, output_format="html5")
            soup = BeautifulSoup(html, "html.parser")
            mentions = soup.findAll('mention')
            botfound = False
            if len(mentions) > 0:
                for mention in mentions:
                    if mention.text == f"@{config.get("OpenProject", "botuser_handle")}":
                        botfound = True
                        break
            print(comment.rawtext)
            if botfound:
                ticket = Workpackage.getByID(notify.resourceID)
                opid = f"[OP#{ticket.id}]"
                print("Ticketcode: ", opid)
                print("Sending mail to", notify.actor["title"])
                SMTPClient.send_mail(ticket.clientmail,
                                    f"{opid} Neue Antwort zu \"{ticket.title}\"",
                                    comment.rawtext,
                                    "",
                                    notify.actor["title"])
        except Exception as e:
            print("Fehler beim Abrufen des Kommentars: ", e)
        else:
            print("Markiere Benachrichtigung als gelesen.")
            notify.setRead()
