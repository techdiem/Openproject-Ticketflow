"""IMAP client – establishes an IMAP connection and fetches new e-mails."""
from imap_tools import MailBox, MailBoxUnencrypted, MailBoxStartTls
from config import config
from model.mail_intern import MailIntern
from logger import logger


class IMAPClient:
    """Manages the IMAP connection and returns new e-mails as MailIntern objects."""

    def __init__(self) -> None:
        self.mailbox = self._connect()

    def _connect(self):
        encryption = config.get("IMAP", "encryption").lower()
        if encryption == "tls":
            box_cls = MailBoxStartTls
        elif encryption == "ssl":
            box_cls = MailBox
        else:
            box_cls = MailBoxUnencrypted

        return box_cls(config.get("IMAP", "server")).login(
            config.get("IMAP", "user"),
            config.get("IMAP", "password"),
        )

    def supports_idle(self) -> bool:
        """Return True if the IMAP server advertises the IDLE push capability."""
        try:
            caps = self.mailbox.client.capabilities or ()
            return "IDLE" in caps
        except Exception:
            return False

    def idle_wait(self, timeout: float) -> bool:
        """Enter IMAP IDLE and block until the server signals new messages or *timeout* elapses.

        Returns True when the server sent a push notification (new messages likely available),
        False when the timeout expired without a push.
        Raises an exception on connection errors so the caller can reconnect.
        """
        responses = self.mailbox.idle.wait(timeout=timeout)
        return bool(responses)

    def check_mail(self) -> list[MailIntern]:
        """Return all unseen messages from the inbox without marking them as read."""
        mails: list[MailIntern] = []
        for msg in self.mailbox.fetch(mark_seen=False):
            logger.info(
                "%s | %s | %s bytes | %s attachment(s)",
                msg.date,
                msg.subject,
                len(msg.text or msg.html or ""),
                len(msg.attachments),
            )
            subject = msg.subject or "Kein Titel"
            mails.append(
                MailIntern(
                    uid=msg.uid,
                    subject=subject,
                    text_plain=msg.text or "",
                    text_html=msg.html or "",
                    sender=msg.from_values,
                    attachments=list(msg.attachments),
                )
            )
        return mails

    def close(self) -> None:
        """Close the IMAP connection."""
        try:
            self.mailbox.client.close()
            self.mailbox.logout()
        except Exception:
            pass
