from config import config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

if (config.get("SMTP", "encryption") == "ssl"):
    from smtplib import SMTP_SSL as SMTP
else:
    from smtplib import SMTP

class SMTPClient():
    @staticmethod
    def send_mail(recipient, subject, sender_name, content_plain="", content_html=""):
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = f"{sender_name} <{config.get('SMTP', 'sender_mail')}>"
        msg['To'] = recipient
        text = content_plain
        html = content_html

        if text != "":
            part1 = MIMEText(text.encode('utf-8'), 'plain', 'utf-8')
            msg.attach(part1)
        if html != "":
            part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')
            msg.attach(part2)

        #fp = open('logo.png', 'rb')
        #msgImage = MIMEImage(fp.read())
        #fp.close()
        # Image ID for usage in mail body content
        #msgImage.add_header('Content-ID', '<my-logo>')
        #msg.attach(msgImage)

        print(f"Sende Mail an {recipient}")
        
        try:
            with SMTP(config.get("SMTP", "server"), config.get("SMTP", "port")) as smtp:
                if (config.get("SMTP", "user") != ""):
                    smtp.login(config.get("SMTP", "user"), config.get("SMTP", "password"))
                try:
                    smtp.sendmail(config.get("SMTP", "sender_mail"), recipient, msg.as_string())
                finally:
                    smtp.quit()
        except Exception as e:
            raise Exception(f"Fehler beim Absenden der Mail: {e}")
