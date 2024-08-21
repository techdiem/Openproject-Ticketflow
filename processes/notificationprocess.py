from markdown import markdown
from bs4 import BeautifulSoup
from integrations.workpackage import Workpackage
from integrations.comment import Comment
from integrations.notification import Notification
from integrations.smtpclient import SMTPClient
from config import config
from logger import logger
from utils.templates import template_commentmail

class NotificationProcess:
    def process_bot_mention(self, notification:Notification, content_cleaned:str):
        ticket = Workpackage.getByID(notification.resourceID)
        opid = f"[OP#{ticket.id}]"
        logger.info(f"Mail mit Ticketcode {opid} an {notification.actor['title']}")
        soup = BeautifulSoup(content_cleaned)
        plaincontent = soup.get_text()
        subject, body_plain, body_html = template_commentmail(opid, ticket.title, plaincontent, notification.actor["title"])
        #Send mail
        SMTPClient.send_mail(ticket.clientmail,
                            subject,
                            notification.actor["title"],
                            content_html=body_html,
                            content_plain=body_plain)

    def notification_comment(self, notification:Notification):
        logger.info("Es könnte eine Kommentar-Benachrichtigung sein, rufe Aktivität ab...")
        #Convert comment from markdown to html for further processing and html mail
        comment = Comment.getByActivityID(notification.activityID)
        if comment == None:
            logger.info("Die Aktivität dieser Benachrichtigung ist kein Kommentar, überspringe...")
            return
        try:
            html = markdown(comment.rawtext, output_format="html5")
        except TypeError as e:
            logger.error("Fehler beim konvertieren der Nachricht, ist es ein gültiger Kommentar?:", e)
        logger.info("Es ist ein Kommentar")
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
        logger.debug(str(soup))

        #The botuser got mentioned in the comment
        if botfound:
            logger.info("Bot wurde markiert")
            self.process_bot_mention(notification, str(soup))
        else:
            logger.info("Bot wurde nicht markiert")

    def run(self):
        logger.info("Verarbeite neue OpenProject-Benachrichtigungen")
        notifications = Notification.getNotificationCollection()
        for notify in notifications:
            logger.info(f"Neue Benachrichtigung, ID: {notify.id}")
            if notify.reason in ["commented", "mentioned", "watched"]:
                try:
                    self.notification_comment(notify)
                except Exception as e:
                    logger.error(f"Fehler beim Bearbeiten der Benachrichtigung: {e}")
                else:
                    logger.info("Markiere Benachrichtigung als gelesen.")
                    notify.setRead()
            else:
                logger.info(f"Benachrichtigung ist kein Kommentar, Typ: {notify.reason}")
                logger.info("Markiere Benachrichtigung als gelesen.")
                notify.setRead()
