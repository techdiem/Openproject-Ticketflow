"""MailProcess – fetches new e-mails and processes them as work packages or comments."""
import json
import re
import threading
from string import Template

from mailparser_reply import EmailReplyParser

from config import config
from mailintegration.imapclient import IMAPClient
from mailintegration.smtpclient import SMTPClient
from logger import logger
from model.mail_intern import MailIntern
from model.work_package_text import WorkPackageText
from openproject.comment import Comment
from openproject.workpackage import Workpackage

# Reconnect wait in seconds after an IDLE connection error
_IDLE_RECONNECT_DELAY = 30.0


class MailProcess:
    _OPID_REGEX = r"\[OP#(\d+)\]"

    @staticmethod
    def _mail_content_to_workpackage(mail: MailIntern) -> WorkPackageText:
        """Select the best text body from a mail and return it as a WorkPackageText."""
        # Addresses whose HTML body should be converted to Markdown instead of using plain text
        html_to_md_addresses: list[str] = json.loads(config.get("Workflow", "mail_html_to_md"))

        bodies: dict[str, str] = {}
        if mail.text_plain:
            bodies["textile"] = mail.text_plain
        if mail.text_html:
            bodies["html"] = mail.text_html
        if not bodies:
            bodies["textile"] = "Kein Text"

        # Prefer HTML body for whitelisted senders or when no plain text is available
        if (len(bodies) == 2 and mail.sender.email in html_to_md_addresses) or (
            "textile" not in bodies
        ):
            return WorkPackageText(bodies["html"], "html")

        return WorkPackageText(bodies["textile"], "textile")

    @staticmethod
    def _template_new_ticket(opid: str, subject: str) -> tuple[str, str, str] | None:
        """Build subject / plain / HTML for the new-ticket confirmation mail."""
        tmpl_sub = config.get("Templates", "newticket_subject")
        tmpl_plain = config.get("Templates", "newticket_plain")
        tmpl_html = config.get("Templates", "newticket_html")

        if not tmpl_plain and not tmpl_html:
            return None

        subs = {"opid": opid, "subject": subject}
        return (
            Template(tmpl_sub).safe_substitute(subs),
            Template(tmpl_plain).safe_substitute(subs) if tmpl_plain else "",
            Template(tmpl_html).safe_substitute(subs) if tmpl_html else "",
        )

    def _send_new_ticket_mail(self, ticket_id: int, title: str, recipient: str) -> None:
        """Send a confirmation e-mail to the original sender after ticket creation."""
        opid = f"[OP#{ticket_id}]"
        result = self._template_new_ticket(opid, title)
        if result is None:
            return
        subject, body_plain, body_html = result
        SMTPClient.send_mail(
            recipient,
            subject,
            sender_name=config.get("Workflow", "new_ticket_sendername"),
            content_plain=body_plain,
            content_html=body_html,
        )

    def _create_workpackage(self, mail: MailIntern) -> None:
        """Create a new work package from an incoming e-mail."""
        wpcontent = self._mail_content_to_workpackage(mail)
        # Prepend sender information as a note inside the description
        message = f"_Sender: {mail.sender.full}_\n{wpcontent.content}"
        ticket = Workpackage(mail.subject, message, mail.sender.email, wpcontent.format)
        result = ticket.publish()

        # --- Step 1: verify ticket creation ---
        # Raises so the caller skips mail deletion when the API rejected the request.
        try:
            ticket.id = json.loads(result.content)["id"]
        except Exception as exc:
            logger.error(
                "Failed to create work package '%s': %s\n%s",
                ticket.title,
                result.content,
                exc,
            )
            raise RuntimeError("Work package creation failed.") from exc

        logger.info("Work package '%s' created, ID %s.", ticket.title, ticket.id)

        # --- Step 2: send confirmation mail ---
        # A failure here is logged but does NOT propagate – the ticket already exists
        # and the source mail must be deleted to avoid duplicate tickets.
        if config.getboolean("Workflow", "new_ticket_mail_info"):
            try:
                self._send_new_ticket_mail(ticket.id, ticket.title, mail.sender.email)
            except Exception as exc:
                logger.error(
                    "Work package '%s' (ID %s) was created but the confirmation mail "
                    "could not be sent: %s",
                    ticket.title,
                    ticket.id,
                    exc,
                )

        # --- Step 3: upload attachments ---
        self._upload_attachments(ticket, mail)

    def _upload_attachments(self, ticket: Workpackage, mail: MailIntern) -> str:
        """Uploads all mail attachment to an existing ticket"""
        attachment_notes = ""
        for attachment in mail.attachments:
            logger.info(
                "Attachment '%s' (%s) found.", attachment.filename, attachment.content_type
            )
            try:
                ticket.add_attachment(attachment.filename, attachment.payload)
                attachment_notes += f"\n_Attachment: {attachment.filename}_"
            except Exception as exc:
                logger.error(
                    "Failed to upload attachment '%s': %s", attachment.filename, exc
                )
                raise RuntimeError("Attachment upload failed.") from exc
        return attachment_notes

    # ------------------------------------------------------------------
    # Mail processing
    # ------------------------------------------------------------------

    def _new_comment(self, mail: MailIntern, opid: re.Match) -> None:
        """Process an incoming mail as a comment on an existing work package."""
        ticket_id = opid.group(1)
        logger.info("Reply for ticket #%s received.", ticket_id)

        ticket = Workpackage.get_by_id(ticket_id)
        if ticket is None:
            # Ticket does not exist – create a new one instead
            logger.info(
                "Reply for ticket #%s received but ticket does not exist – creating new one.",
                ticket_id,
            )
            mail.subject = re.sub(rf"{self._OPID_REGEX}\s*", "", mail.subject)
            self._create_workpackage(mail)
            return

        # Strip quoted / forwarded content from the reply
        parsed = EmailReplyParser(languages=["en", "de"]).read(text=mail.text_plain)
        reply_body = parsed.latest_reply
        use_clean_body = config.getboolean("Workflow", "clean_mail_body_comments", fallback=False)
        replies = getattr(parsed, "replies", None)
        if replies and len(replies) > 0 and use_clean_body:
            first_reply_body = getattr(replies[0], "body", None)
            if first_reply_body:
                reply_body = first_reply_body

        comment_text = f"_Reply from {mail.sender.full}:_\n{reply_body}\n"
        comment_text += self._upload_attachments(ticket, mail)

        # Reopen the ticket if it is currently in a closed state
        if ticket.status == config.get("OpenProject", "ticket_closed_id"):
            ticket.set_status(config.get("OpenProject", "ticket_reopen_id"))

        Comment(comment_text).publish(ticket_id)

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def _process_inbox(self, imapclient: IMAPClient) -> int:
        """Fetch and process all pending e-mails using an existing *imapclient* connection.

        Returns the number of e-mails found in the inbox.
        """
        mails = imapclient.check_mail()
        for mail in mails:
            try:
                opid = re.search(self._OPID_REGEX, mail.subject)
                if opid is not None:
                    self._new_comment(mail, opid)
                else:
                    self._create_workpackage(mail)
            except Exception as exc:
                logger.error("Failed to process mail '%s': %s", mail.subject, exc)
            else:
                # Delete the mail only after successful processing
                imapclient.mailbox.delete(mail.uid)
        return len(mails)

    @staticmethod
    def probe_idle_support() -> bool:
        """Check whether IDLE is enabled in config and supported by the IMAP server.

        Opens a short-lived connection solely to read the server capabilities, then
        closes it immediately.  Returns True when IDLE should be used.
        """
        if not config.getboolean("IMAP", "idle_enabled", fallback=True):
            logger.info("[IMAP] IDLE disabled by configuration – using polling.")
            return False

        logger.info("[IMAP] Probing server for IDLE support …")
        try:
            client = IMAPClient()
            supported = client.supports_idle()
            client.close()
        except Exception as exc:
            logger.warning(
                "[IMAP] Could not probe IDLE support: %s – falling back to polling.", exc
            )
            return False

        if supported:
            logger.info("[IMAP] Server supports IDLE – push mode enabled.")
        else:
            logger.info("[IMAP] Server does not support IDLE – falling back to polling.")
        return supported

    def run(self) -> None:
        """Poll the inbox once (used for periodic polling mode)."""
        logger.info("[MailProcess/Poll] Checking inbox …")
        imapclient = IMAPClient()
        try:
            count = self._process_inbox(imapclient)
            logger.info("[MailProcess/Poll] %d mail(s) processed.", count)
        finally:
            imapclient.close()

    def run_idle_loop(self, stop_event: threading.Event) -> None:
        """Persistent IMAP IDLE loop: waits for server push notifications and processes mails.

        The connection is refreshed every ``idle_refresh_seconds`` (default 1500 s / 25 min)
        per the RFC 2177 recommendation.  Each refresh also fetches the full inbox so no
        messages are missed even if a push was silently dropped.

        Runs until *stop_event* is set.
        """
        refresh = config.getfloat("IMAP", "idle_refresh_seconds", fallback=1500.0)
        logger.info(
            "[MailProcess/IDLE] Starting IDLE loop (connection refresh every %.0f s).", refresh
        )

        while not stop_event.is_set():
            imapclient = None
            try:
                imapclient = IMAPClient()
                logger.info("[MailProcess/IDLE] Connected to IMAP server.")

                while not stop_event.is_set():
                    # Always check the inbox before (re-)entering IDLE to catch messages
                    # that arrived during a reconnect or were not signalled via push.
                    count = self._process_inbox(imapclient)
                    if count:
                        logger.info(
                            "[MailProcess/IDLE] Inbox check: %d mail(s) processed.", count
                        )
                    else:
                        logger.debug("[MailProcess/IDLE] Inbox check: no new messages.")

                    logger.debug("[MailProcess/IDLE] Entering IDLE (timeout %.0f s) …", refresh)
                    try:
                        got_push = imapclient.idle_wait(timeout=refresh)
                    except Exception as exc:
                        logger.error(
                            "[MailProcess/IDLE] IDLE wait failed: %s – reconnecting …", exc
                        )
                        break  # exit inner loop to reconnect

                    if got_push:
                        logger.info(
                            "[MailProcess/IDLE] Push notification received – fetching inbox."
                        )
                    else:
                        logger.info(
                            "[MailProcess/IDLE] IDLE refresh timeout – re-checking inbox."
                        )

            except Exception as exc:
                logger.error(
                    "[MailProcess/IDLE] Connection error: %s – retrying in %.0f s.",
                    exc,
                    _IDLE_RECONNECT_DELAY,
                )
            finally:
                if imapclient is not None:
                    imapclient.close()

            if not stop_event.is_set():
                stop_event.wait(timeout=_IDLE_RECONNECT_DELAY)

        logger.info("[MailProcess/IDLE] IDLE loop stopped.")
