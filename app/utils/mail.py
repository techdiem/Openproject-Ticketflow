import json
from config import config
from logger import logger
from utils.templates import template_newmail
from model.mail_intern import MailIntern
from model.work_package_text import WorkPackageText
from integrations.workpackage import Workpackage
from integrations.smtpclient import SMTPClient

def mail_content_to_workpackage(mail:MailIntern) -> WorkPackageText:
    #Read config for mail senders which mails are imported as html
    mail_html_to_md = json.loads(config.get("Workflow", "mail_html_to_md"))

    #Check which text bodies exist
    text_bodies = {}
    text_message = ""
    if len(mail.text_plain) != 0:
        text_bodies["textile"] = mail.text_plain
    if len(mail.text_html) != 0:
        text_bodies["html"] = mail.text_html
    if len(text_bodies) == 0:
        text_bodies["textile"] = "Kein Text"

    #Select html on whitelisted addresses
    if ((len(text_bodies) == 2 and mail.sender.email in mail_html_to_md)
        or "textile" not in text_bodies):
        text_message = text_bodies["html"]
        text_format = "html"
    else:
        text_message = text_bodies["textile"]
        text_format = "textile"

    return WorkPackageText(text_message, text_format)

def create_workpackage(mail:MailIntern):
    #Add sender heading
    wpcontent = mail_content_to_workpackage(mail)
    message = f"_Absender: {mail.sender.full}_\n{wpcontent.content}"
    ticket = Workpackage(mail.subject, message, mail.sender.email, wpcontent.format)
    result = ticket.publish()
    try:
        ticket.id = json.loads(result.content)["id"]
        logger.info("Ticket %s erstellt, ID %s", ticket.title, ticket.id)
        if config.getboolean('Workflow', 'new_ticket_mail_info'):
            send_new_ticket_mail(ticket.id, ticket.title, mail.sender.email)
    except Exception as e:
        logger.error("Fehler beim Erstellen des Arbeitspaketes %s\n%s\n%s",
                     ticket.title,
                     result.content,
                     e)
        raise RuntimeError from e
    else:
        #Save attachments
        for attachment in mail.attachments:
            logger.info("Anhang %s vom Typ %s gefunden.",
                        attachment.filename,
                        attachment.content_type)
            try:
                result = ticket.add_attachment(attachment.filename, attachment.payload)
            except Exception as e:
                logger.error("Fehler beim hinzufügen des Anhangs %s!\n%s",
                             attachment.filename,
                             result.content)
                raise RuntimeError from e

def send_new_ticket_mail(ticketid:int, title:str, recipient:str):
    opid = f"[OP#{ticketid}]"
    subject, body_plain, body_html = template_newmail(opid, title)
    SMTPClient.send_mail(recipient, subject,
                         sender_name=config.get('Workflow', 'new_ticket_sendername'),
                         content_plain=body_plain,
                         content_html=body_html)
