from integrations.comment import Comment
from mailparser_reply import EmailReplyParser
import re
from utils.mail import create_workpackage
from integrations.imapclient import IMAPClient
from integrations.workpackage import Workpackage
from config import config
from logger import logger

class MailProcess:
    opid_regex = r"\[OP#(\d+)\]"

    def newComment(self, mail, opid):
        #If existent, it is a comment to an existing workpackage
        ticketid = opid.groups()[0]
        logger.info(f"Antwort für Ticket #{ticketid} empfangen.")

        #Check if ticket exists
        ticket = Workpackage.getByID(ticketid)
        if ticket != None:
            #Remove forwarded or reply mails
            mail_message = EmailReplyParser(languages=['en', 'de']).read(text=mail.text_plain)
            comment_text = f"_Antwort von {mail.sender.full}:_\n{mail_message.latest_reply}"
            #If ticket is closed, set to configured status
            if ticket.status == config.get("OpenProject", "ticket_closed_id"):
                ticket.set_status(config.get("OpenProject", "ticket_reopen_id"))
            comment = Comment(comment_text)
            comment.publish(ticketid)
        else:
            logger.info(f"Kommentar für Ticket #{ticketid} per Mail empfangen, es existiert aber nicht, erstelle neu...")
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
                if opid != None:
                    self.newComment(mail, opid)
                else:
                    #If not, create a new workpackage
                    create_workpackage(mail)
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten der Mails: {e}")
            else:
                #Delete Mail
                imapclient.mailbox.delete(mail.uid)
        #Close IMAP connection
        imapclient.mailbox.client.close()
