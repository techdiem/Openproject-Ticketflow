import json
from config import config
from logger import logger
from model.mailintern import MailIntern
from model.workpackageText import WorkPackageText
from integrations.workpackage import Workpackage
from integrations.smtpclient import SMTPClient

def mailContentToWorkpackage(mail:MailIntern) -> WorkPackageText:
    #Read config for mail senders which mails are imported as html
    mail_html_to_md = json.loads(config.get("Workflow", "mail_html_to_md"))
    
    #Check which text bodies exist
    text_bodies = {}
    text_message = ""
    if len(mail.text_plain) != 0: text_bodies["textile"] = mail.text_plain
    if len(mail.text_html) != 0: text_bodies["html"] = mail.text_html
    if len(text_bodies) == 0: text_bodies["textile"] = "Kein Text"
    
    #Select html on whitelisted addresses
    if (len(text_bodies) == 2 and mail.sender.email in mail_html_to_md) or not "textile" in text_bodies:
        text_message = text_bodies["html"]
        text_format = "html"
    else:
        text_message = text_bodies["textile"]
        text_format = "textile"
    
    return WorkPackageText(text_message, text_format)

def create_workpackage(mail:MailIntern):
    #Add sender heading
    wpcontent = mailContentToWorkpackage(mail)
    message = f"_Absender: {mail.sender.full}_\n{wpcontent.content}"
    ticket = Workpackage(mail.subject, message, mail.sender.email, wpcontent.format)
    result = ticket.publish()
    try:
        ticket.id = json.loads(result.content)["id"]
        logger.info(f"Ticket {ticket.title} erstellt, ID {ticket.id}")
        if config.get('Workflow', 'new_ticket_mail_info') == "true":
            send_new_ticket_mail(ticket.id, ticket.title, mail.sender.email)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Arbeitspaketes {ticket.title}!\n{result.content}\n{e}")
        raise RuntimeError
    else:
        #Save attachments
        for attachment in mail.attachments:
            logger.info(f"Anhang {attachment.filename} vom Typ {attachment.content_type} gefunden.")
            try:
                result = ticket.add_attachment(attachment.filename, attachment.payload)
            except:
                logger.error(f"Fehler beim hinzufügen des Anhangs {attachment.filename}!\n{result.content}")
                raise RuntimeError

def send_new_ticket_mail(id:int, title:str, recipient:str):
    opid = f"[OP#{id}]"
    subject = f"{opid} Ihr Ticket \"{title}\""
    body = f"Ihr Ticket mit dem Titel \"{title}\" wurde erfasst."
    SMTPClient.send_mail(recipient, subject, sender_name=config.get('Workflow', 'new_ticket_sendername'), content_plain=body)
