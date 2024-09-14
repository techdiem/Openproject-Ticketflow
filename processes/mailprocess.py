import re
from mailparser_reply import EmailReplyParser
from utils.mail import create_workpackage
from integrations.imapclient import IMAPClient
from integrations.workpackage import Workpackage
from integrations.comment import Comment
from config import config
from logger import logger

class MailProcess:
    opid_regex = r"\[OP#(\d+)\]"

    def new_comment(self, mail, opid):
        #If existent, it is a comment to an existing workpackage
        ticketid = opid.groups()[0]
        logger.info("Antwort für Ticket #%s empfangen.", ticketid)

        #Check if ticket exists
        ticket = Workpackage.get_by_id(ticketid)
        if ticket is not None:
            #Remove forwarded or reply mails
            mail_message = EmailReplyParser(languages=['en', 'de']).read(text=mail.text_plain)
            comment_text = f"_Antwort von {mail.sender.full}:_\n{mail_message.latest_reply}\n"
            if len(mail.attachments) > 0:
                for attachment in mail.attachments:
                    logger.info("Anhang %s vom Typ %s gefunden.",
                                attachment.filename,
                                attachment.content_type)
                    try:
                        result = ticket.add_attachment(attachment.filename, attachment.payload)
                        comment_text += f"\n_Anhang: {attachment.filename}_"
                    except Exception as e:
                        logger.error("Fehler beim Hinzufügen des Anhangs %s!\n%s",
                                     attachment.filename,
                                     result.content)
                        raise RuntimeError from e

            #If ticket is closed, set to configured status
            if ticket.status == config.get("OpenProject", "ticket_closed_id"):
                ticket.set_status(config.get("OpenProject", "ticket_reopen_id"))
            comment = Comment(comment_text)
            comment.publish(ticketid)
        else:
            logger.info("Kommentar für Ticket #%s per Mail empfangen, es existiert aber nicht,\
                         erstelle neu...", ticketid)
            #Remove opid from subject for cleaner ticket title
            mail.subject = re.sub(fr"{self.opid_regex}\s*", "", mail.subject)
            create_workpackage(mail)

    def run(self):
        logger.info("Verarbeite eingehende Mails via IMAP")
        imapclient = IMAPClient()
        newmails = imapclient.check_mail()

        for mail in newmails:
            try:
                #Search for opid in subject
                opid = re.search(self.opid_regex, mail.subject)
                if opid is not None:
                    self.new_comment(mail, opid)
                else:
                    #If not, create a new workpackage
                    create_workpackage(mail)
            except Exception as e:
                logger.error("Fehler beim Verarbeiten der Mails: %s", e)
            else:
                #Delete Mail
                imapclient.mailbox.delete(mail.uid)
        #Close IMAP connection
        imapclient.mailbox.client.close()
