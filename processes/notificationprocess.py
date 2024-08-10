from markdown import markdown
from bs4 import BeautifulSoup
from integrations.workpackage import Workpackage
from integrations.comment import Comment
from integrations.notification import Notification
from integrations.smtpclient import SMTPClient
from config import config

def notification_process():
    print("Verarbeite neue OpenProject-Benachrichtigungen")
    notifications = Notification.getNotificationCollection()
    for notify in notifications:
        print("Found notification with id", notify.id)
        if notify.reason == "commented":
            print("It is a comment notification")
            try:
                #Convert comment from markdown to html for further processing and html mail
                comment = Comment.getByActivityID(notify.activityID)
                html = markdown(comment.rawtext, output_format="html5")
                #Use html scraper to find mentions in comment
                soup = BeautifulSoup(html, "html.parser")
                mentions = soup.findAll('mention')
                botfound = False
                if len(mentions) > 0:
                    for mention in mentions:
                        #Mention of bot user gets removed
                        if mention.text == f"@{config.get("OpenProject", "botuser_handle")}":
                            botfound = True
                            mention.decompose()
                        else:
                            #Other mentions (users, tickets) gets converted to only the text
                            mention.replace_with(mention.text)
                print(str(soup))

                #Only send a mail, if the botuser got mentioned in the comment
                if botfound:
                    ticket = Workpackage.getByID(notify.resourceID)
                    opid = f"[OP#{ticket.id}]"
                    print(f"Mail mit Ticketcode {opid} an {notify.actor["title"]}")
                    #Send mail
                    SMTPClient.send_mail(ticket.clientmail,
                                        f"{opid} Neue Antwort zu \"{ticket.title}\"",
                                        "",
                                        str(soup),
                                        notify.actor["title"])
            except Exception as e:
                print("Fehler beim Abrufen des Kommentars: ", e)
            else:
                print("Markiere Benachrichtigung als gelesen.")
                notify.setRead()
