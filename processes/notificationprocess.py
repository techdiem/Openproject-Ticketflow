from markdown import markdown
from bs4 import BeautifulSoup
from integrations.workpackage import Workpackage
from integrations.comment import Comment
from integrations.notification import Notification
from integrations.smtpclient import SMTPClient
from config import config

class NotificationProcess:
    def process_bot_mention(self, notification:Notification, content_cleaned:str):
        ticket = Workpackage.getByID(notification.resourceID)
        opid = f"[OP#{ticket.id}]"
        print(f"Mail mit Ticketcode {opid} an {notification.actor['title']}")
        content = (f"{content_cleaned}"
                   ""
                   "<i>Bitte antworten Sie auf diese Nachricht über die Antworten-Funktion des Mailprogramms.\n"
                   "Wir können Ihre Nachricht dann einfacher zuordnen. Danke!</i>")
        #Send mail
        SMTPClient.send_mail(ticket.clientmail,
                            f"{opid} Neue Antwort zu \"{ticket.title}\"",
                            notification.actor["title"],
                            content_html=content)

    def notification_comment(self, notification:Notification):
        print("Es könnte eine Kommentar-Benachrichtigung sein, rufe Aktivität ab...")
        #Convert comment from markdown to html for further processing and html mail
        comment = Comment.getByActivityID(notification.activityID)
        if comment == None:
            print("Die Aktivität dieser Benachrichtigung ist kein Kommentar, überspringe...")
            return
        try:
            html = markdown(comment.rawtext, output_format="html5")
        except TypeError as e:
            print("Fehler beim konvertieren der Nachricht, ist es ein gültiger Kommentar?:", e)
        print("Es ist ein Kommentar")
        #Use html scraper to find mentions in comment
        soup = BeautifulSoup(html, "html.parser")
        mentions = soup.findAll('mention')
        botfound = False
        if len(mentions) > 0:
            for mention in mentions:
                #Mention of bot user gets removed
                if mention.text == f"@{config.get('OpenProject', 'botuser_handle')}":
                    botfound = True
                    mention.decompose()
                else:
                    #Other mentions (users, tickets) gets converted to only the text
                    mention.replace_with(mention.text)
        #print(str(soup))

        #The botuser got mentioned in the comment
        if botfound:
            print("Bot wurde markiert")
            self.process_bot_mention(notification, str(soup))
        else:
            print("Bot wurde nicht markiert")

    def run(self):
        print("Verarbeite neue OpenProject-Benachrichtigungen")
        notifications = Notification.getNotificationCollection()
        for notify in notifications:
            print("Neue Benachrichtigung, ID:", notify.id)
            if notify.reason in ["commented", "mentioned", "watched"]:
                try:
                    self.notification_comment(notify)
                except Exception as e:
                    print("Fehler beim Bearbeiten der Benachrichtigung: ", e)
                else:
                    print("Markiere Benachrichtigung als gelesen.")
                    notify.setRead()
            else:
                print("Benachrichtigung ist kein Kommentar, Typ:", notify.reason)
                print("Markiere Benachrichtigung als gelesen.")
                notify.setRead()
