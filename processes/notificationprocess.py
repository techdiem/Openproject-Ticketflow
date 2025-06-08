from markdown import markdown
from bs4 import BeautifulSoup
from integrations.workpackage import Workpackage
from integrations.comment import Comment
from integrations.notification import Notification
from integrations.smtpclient import SMTPClient
from integrations.activity import Activity
from config import config
from logger import logger
from utils.templates import template_commentmail, template_statusmail

class NotificationProcess:
    def process_bot_mention(self, notification:Notification, content_cleaned:str):
        ticket = Workpackage.get_by_id(notification.resource_id)
        opid = f"[OP#{ticket.id}]"
        logger.info("Mail mit Ticketcode %s", opid)
        subject, body_plain, body_html = template_commentmail(opid,
                                                              ticket.title,
                                                              content_cleaned,
                                                              notification.actor["title"])
        #Send mail
        SMTPClient.send_mail(ticket.clientmail,
                            subject,
                            notification.actor["title"],
                            content_html=body_html,
                            content_plain=body_plain)

    def process_status_change(self, notification:Notification, statusmsg:str):
        ticket = Workpackage.get_by_id(notification.resource_id)
        opid = f"[OP#{ticket.id}]"
        logger.info("Mail mit Ticketcode %s", opid)
        subject, body_plain, body_html = template_statusmail(opid, ticket.title, statusmsg)
        #Send mail
        SMTPClient.send_mail(ticket.clientmail,
                            subject,
                            notification.actor["title"],
                            content_html=body_html,
                            content_plain=body_plain)

    def notification_comment(self, notification:Notification, activity:Activity):
        if not notification.reason in ["commented", "mentioned", "watched"]:
            logger.info("Notification reason gibt an, dass es kein Kommentar ist")
            return
        logger.info("Es könnte eine Kommentar-Benachrichtigung sein, rufe Aktivität ab...")
        comment = Comment.get_by_activity(activity)
        if comment is None:
            logger.info("Die Aktivität dieser Benachrichtigung ist kein Kommentar, überspringe...")
            return
        try:
            html = markdown(comment.rawtext, output_format="html5")
        except TypeError as e:
            logger.error("Fehler beim konvertieren der Nachricht, \
                         ist es ein gültiger Kommentar?: %s", e)
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

    def notification_processed(self, notification:Notification, activity:Activity):
        logger.info("Es ist eine Verarbeitungs-Benachrichtigung, Statusänderung?")
        details = activity.data["details"]
        if len(details) > 0:
            for action in details:
                detailsstr = action["raw"]
                if detailsstr.startswith("Status"):
                    logger.info("Es ist eine Statusänderung")
                    self.process_status_change(notification, detailsstr)
        else:
            logger.info("Keine Processed-Aktivität in Benachrichtigung enthalten")

    def run(self):
        logger.info("Verarbeite neue OpenProject-Benachrichtigungen")
        notifications = Notification.get_notification_collection()
        for notify in notifications:
            logger.info("Neue Benachrichtigung, ID: %s", notify.id)
            try:
                activity = Activity.get_by_id(notify.activity_id)
                if config.getboolean('Workflow', 'comment_to_mail'):
                    self.notification_comment(notify, activity)
                if config.getboolean('Workflow', 'status_mail_info'):
                    self.notification_processed(notify, activity)
            except Exception as e:
                logger.error("Fehler beim Bearbeiten der Benachrichtigung: %s", e)
            else:
                logger.info("Markiere Benachrichtigung als gelesen.")
                notify.set_read()
