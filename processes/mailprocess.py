from integrations.comment import Comment
from mailparser_reply import EmailReplyParser
import re
from utils.mail import create_workpackage
from integrations.imapclient import IMAPClient

def mail_process():
    print("Verarbeite eingehende Mails via IMAP")
    imapclient = IMAPClient()
    newmails = imapclient.check_mail()

    for mail in newmails:
        try:
            #Search for opid in subject
            opid = re.search(r"\[OP#(\d+)\]", mail.subject)
            if opid != None:
                #If existent, it is a comment to an existing workpackage
                ticketid = opid.groups()[0]
                print(f"Antwort für Ticket #{ticketid} empfangen.")
                #Remove forwarded or reply mails
                mail_message = EmailReplyParser(languages=['en', 'de']).read(text=mail.text_plain)
                comment_text = f"_Antwort von {mail.sender.full}:_\n{mail_message.latest_reply}"

                comment = Comment(comment_text)
                comment.publish(ticketid)
            else:
                #If not, create a new workpackage
                create_workpackage(mail)
        except Exception as e:
            print("Fehler beim Verarbeiten der Mails: ", e)
        else:
            #Delete Mail
            imapclient.mailbox.delete(mail[0])
    #Close IMAP connection
    imapclient.mailbox.client.close()