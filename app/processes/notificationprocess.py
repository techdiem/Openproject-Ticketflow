"""NotificationProcess – processes OpenProject notifications and dispatches e-mails."""
from string import Template

from bs4 import BeautifulSoup
from markdown import markdown

from config import config
from mailintegration.smtpclient import SMTPClient
from logger import logger
from openproject.activity import Activity
from openproject.comment import Comment
from openproject.notification import Notification
from openproject.workpackage import Workpackage


class NotificationProcess:
    @staticmethod
    def _render_template(
        subject_tmpl: str,
        plain_tmpl: str,
        html_tmpl: str,
        substitution: dict,
    ) -> tuple[str, str, str]:
        """Apply substitutions to all template strings"""
        return (
            Template(subject_tmpl).safe_substitute(substitution),
            Template(plain_tmpl).safe_substitute(substitution) if plain_tmpl else "",
            Template(html_tmpl).safe_substitute(substitution) if html_tmpl else "",
        )

    @staticmethod
    def _template_comment_mail(
        opid: str, subject: str, content: str, actor: str
    ) -> tuple[str, str, str] | None:
        """Build subject / plain / HTML for a comment notification mail."""
        tmpl_sub = config.get("Templates", "commentmail_subject")
        tmpl_plain = config.get("Templates", "commentmail_plain")
        tmpl_html = config.get("Templates", "commentmail_html").replace("\n", "")

        if not tmpl_plain and not tmpl_html:
            return None

        # Extract plain text from HTML content for the plain-text part
        plain_content = BeautifulSoup(content, "html.parser").get_text()

        subs = {"opid": opid, "subject": subject, "content": content, "actor": actor}
        # Plain part uses extracted text instead of raw HTML
        tmpl_plain_filled = Template(tmpl_plain).safe_substitute(
            {**subs, "content": plain_content}
        )
        return (
            Template(tmpl_sub).safe_substitute(subs),
            tmpl_plain_filled,
            Template(tmpl_html).safe_substitute(subs) if tmpl_html else "",
        )

    @staticmethod
    def _template_status_mail(
        opid: str, subject: str, statuschange: str
    ) -> tuple[str, str, str] | None:
        """Build subject / plain / HTML for a status-change notification mail."""
        tmpl_sub = config.get("Templates", "statusmail_subject")
        tmpl_plain = config.get("Templates", "statusmail_plain")
        tmpl_html = config.get("Templates", "statusmail_html").replace("\n", "")

        if not tmpl_plain and not tmpl_html:
            return None

        subs = {"opid": opid, "subject": subject, "statuschange": statuschange}
        return (
            Template(tmpl_sub).safe_substitute(subs),
            Template(tmpl_plain).safe_substitute(subs) if tmpl_plain else "",
            Template(tmpl_html).safe_substitute(subs) if tmpl_html else "",
        )

    # ------------------------------------------------------------------
    # Notification handlers
    # ------------------------------------------------------------------

    def _process_bot_mention(self, notification: Notification, content_cleaned: str) -> None:
        """Send the cleaned comment as an e-mail to the ticket's client address."""
        ticket = Workpackage.get_by_id(notification.resource_id)
        opid = f"[OP#{ticket.id}]"
        logger.info("Sending comment mail with ticket code %s.", opid)
        result = self._template_comment_mail(
            opid, ticket.title, content_cleaned, notification.actor["title"]
        )
        if result is None:
            logger.info("No comment mail template configured – skipping.")
            return
        subject, body_plain, body_html = result
        SMTPClient.send_mail(
            ticket.clientmail,
            subject,
            notification.actor["title"],
            content_html=body_html,
            content_plain=body_plain,
        )

    def _process_status_change(self, notification: Notification, statusmsg: str) -> None:
        """Send a status-change e-mail to the ticket's client address."""
        ticket = Workpackage.get_by_id(notification.resource_id)
        opid = f"[OP#{ticket.id}]"
        logger.info("Sending status mail with ticket code %s.", opid)
        result = self._template_status_mail(opid, ticket.title, statusmsg)
        if result is None:
            logger.info("No status mail template configured – skipping.")
            return
        subject, body_plain, body_html = result
        SMTPClient.send_mail(
            ticket.clientmail,
            subject,
            notification.actor["title"],
            content_html=body_html,
            content_plain=body_plain,
        )

    def _handle_comment(self, notification: Notification, activity: Activity) -> None:
        """Check whether the activity is a comment with a bot mention and handle it."""
        if notification.reason not in ("commented", "mentioned", "watched"):
            logger.info("Notification reason indicates no comment – skipping.")
            return

        logger.info("Possible comment notification – fetching activity …")
        comment = Comment.get_by_activity(activity)
        if comment is None:
            logger.info("Activity is not a comment – skipping.")
            return

        try:
            html = markdown(comment.rawtext, output_format="html5")
        except TypeError as exc:
            logger.error("Failed to convert comment to HTML – is it a valid comment? %s", exc)
            return

        logger.info("Comment found.")
        soup = BeautifulSoup(html, "html.parser")
        bot_handle = f"@{config.get('OpenProject', 'botuser_handle')}"
        bot_found = False

        for mention in soup.find_all("mention"):
            if mention.text == bot_handle:
                # Remove the bot mention from the outgoing mail content
                bot_found = True
                mention.decompose()
            else:
                # Flatten other mentions (users, tickets) to plain text
                mention.replace_with(mention.text)

        if bot_found:
            logger.info("Bot was mentioned – dispatching comment mail.")
            self._process_bot_mention(notification, str(soup))
        else:
            logger.info("Bot was not mentioned – nothing to send.")

    def _handle_status_change(self, notification: Notification, activity: Activity) -> None:
        """Check whether the activity contains a status change and send an e-mail if so."""
        logger.info("Checking activity for status change.")
        for action in activity.data.get("details", []):
            if action.get("raw", "").startswith("Status"):
                logger.info("Status change detected.")
                self._process_status_change(notification, action["raw"])
                return
        logger.info("No status change found in activity.")

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Fetch all unread OpenProject notifications and process each one."""
        logger.info("Processing new OpenProject notifications.")
        for notify in Notification.get_notification_collection():
            logger.info("New notification, ID: %s.", notify.id)
            try:
                activity = Activity.get_by_id(notify.activity_id)
                if config.getboolean("Workflow", "comment_to_mail"):
                    self._handle_comment(notify, activity)
                if config.getboolean("Workflow", "status_mail_info"):
                    self._handle_status_change(notify, activity)
            except Exception as exc:
                logger.error("Failed to handle notification %s: %s", notify.id, exc)
            else:
                logger.info("Marking notification %s as read.", notify.id)
                notify.set_read()
