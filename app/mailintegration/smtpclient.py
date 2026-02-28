"""SMTP client – sends e-mails via the configured mail server."""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import config
from logger import logger

if config.get("SMTP", "encryption") == "ssl":
    from smtplib import SMTP_SSL as SMTP
else:
    from smtplib import SMTP

class SMTPClient:
    @staticmethod
    def send_mail(
        recipient: str,
        subject: str,
        sender_name: str,
        content_plain: str = "",
        content_html: str = "",
    ) -> None:
        if not recipient:
            logger.info("Keine Mailadresse im Arbeitspaket hinterlegt – Mail wird nicht gesendet.")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{config.get('SMTP', 'sender_mail')}>"
        msg["To"] = recipient

        if content_plain:
            msg.attach(MIMEText(content_plain.encode("utf-8"), "plain", "utf-8"))
        if content_html:
            msg.attach(MIMEText(content_html.encode("utf-8"), "html", "utf-8"))

        logger.info("Send mail to %s", recipient)

        encryption = config.get("SMTP", "encryption").lower()
        server = config.get("SMTP", "server")
        port = config.getint("SMTP", "port")
        user = config.get("SMTP", "user")
        password = config.get("SMTP", "password")

        try:
            with SMTP(server, port) as smtp:
                if encryption == "starttls":
                    smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.sendmail(
                    config.get("SMTP", "sender_mail"),
                    recipient,
                    msg.as_string(),
                )
                smtp.quit()
        except Exception as exc:
            raise IOError(f"Error sending mail: {exc}") from exc
