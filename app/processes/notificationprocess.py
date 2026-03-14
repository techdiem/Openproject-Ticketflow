"""NotificationProcess – processes OpenProject notifications and dispatches e-mails."""
from bs4 import BeautifulSoup
from markdown import markdown

from config import config
from logger import logger
from openproject.activity import Activity
from openproject.comment import Comment
from openproject.notification import Notification
from openproject.workpackage import Workpackage
from processes.ticketmails import send_comment_mail, send_new_ticket_mail, send_status_mail


class NotificationProcess:
    # ------------------------------------------------------------------
    # Notification handlers
    # ------------------------------------------------------------------

    def _process_bot_mention(self, notification: Notification, content_cleaned: str) -> None:
        """Send the cleaned comment as an e-mail to the ticket's client address."""
        ticket = Workpackage.get_by_id(notification.resource_id)
        send_comment_mail(
            ticket.clientmail, ticket.id, ticket.title, content_cleaned, notification.actor["title"]
        )

    def _process_status_change(self, notification: Notification, statusmsg: str) -> None:
        """Send a status-change e-mail to the ticket's client address."""
        ticket = Workpackage.get_by_id(notification.resource_id)
        send_status_mail(
            ticket.clientmail, ticket.id, ticket.title, statusmsg, notification.actor["title"]
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

    def _handle_manual_ticket_creation(self, notification: Notification) -> None:
        if notification.reason != "created":
            logger.info("Notification reason indicates no ticket creation – skipping.")
            return
        else:
            logger.info("New ticket creation detected – fetching ticket …")
        ticket = Workpackage.get_by_id(notification.resource_id)
        if ticket is None:
            logger.info("Could not fetch ticket for created notification – skipping.")
            return
        if not ticket.clientmail:
            logger.info("Created ticket has no client mail – skipping.")
            return
        try:
            send_new_ticket_mail(ticket.id, ticket.title, ticket.clientmail)
            return True
        except Exception as exc:
            logger.error(
                "Could not send new-ticket confirmation mail for ticket %s: %s", ticket.id, exc
            )
        return False


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
                newticket = False
                if config.getboolean("Workflow", "comment_to_mail"):
                    self._handle_comment(notify, activity)
                if config.getboolean("Workflow", "manual_ticket_mail_info"):
                    newticket = self._handle_manual_ticket_creation(notify)
                if config.getboolean("Workflow", "status_mail_info") and not newticket:
                    self._handle_status_change(notify, activity)
            except Exception as exc:
                logger.error("Failed to handle notification %s: %s", notify.id, exc)
            else:
                logger.info("Marking notification %s as read.", notify.id)
                notify.set_read()
