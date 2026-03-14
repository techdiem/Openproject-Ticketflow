"""Shared mail template builders and send helpers for ticket-related mails."""
from string import Template

from bs4 import BeautifulSoup

from config import config, get_html_template
from mailintegration.smtpclient import SMTPClient
from logger import logger


def _render_template(
    subject_tmpl: str,
    plain_tmpl: str,
    html_tmpl: str,
    substitution: dict,
    plain_substitution: dict | None = None,
) -> tuple[str, str, str]:
    """Apply substitutions to all template strings."""
    effective_plain_substitution = plain_substitution or substitution
    return (
        Template(subject_tmpl).safe_substitute(substitution) if subject_tmpl else "",
        Template(plain_tmpl).safe_substitute(effective_plain_substitution)
        if plain_tmpl
        else "",
        Template(html_tmpl).safe_substitute(substitution) if html_tmpl else "",
    )


def _template_new_ticket(opid: str, subject: str) -> tuple[str, str, str] | None:
    """Build subject / plain / HTML for the new-ticket confirmation mail."""
    tmpl_sub = config.get("Templates", "newticket_subject")
    tmpl_plain = config.get("Templates", "newticket_plain")
    tmpl_html = get_html_template("newticket")

    if not tmpl_plain and not tmpl_html:
        return None

    subs = {"opid": opid, "subject": subject}
    return _render_template(tmpl_sub, tmpl_plain, tmpl_html, subs)


def _template_comment_mail(
    opid: str, subject: str, content: str, actor: str
) -> tuple[str, str, str] | None:
    """Build subject / plain / HTML for a comment notification mail."""
    tmpl_sub = config.get("Templates", "commentmail_subject")
    tmpl_plain = config.get("Templates", "commentmail_plain")
    tmpl_html = get_html_template("commentmail")

    if not tmpl_plain and not tmpl_html:
        return None

    # Extract plain text from HTML content for the plain-text part
    plain_content = BeautifulSoup(content, "html.parser").get_text()

    subs = {"opid": opid, "subject": subject, "content": content, "actor": actor}
    plain_subs = {**subs, "content": plain_content}
    return _render_template(
        tmpl_sub,
        tmpl_plain,
        tmpl_html,
        subs,
        plain_substitution=plain_subs,
    )


def _template_status_mail(
    opid: str, subject: str, statuschange: str
) -> tuple[str, str, str] | None:
    """Build subject / plain / HTML for a status-change notification mail."""
    tmpl_sub = config.get("Templates", "statusmail_subject")
    tmpl_plain = config.get("Templates", "statusmail_plain")
    tmpl_html = get_html_template("statusmail")

    if not tmpl_plain and not tmpl_html:
        return None

    subs = {"opid": opid, "subject": subject, "statuschange": statuschange}
    return _render_template(tmpl_sub, tmpl_plain, tmpl_html, subs)


def send_new_ticket_mail(ticket_id: int, title: str, recipient: str):
    """Send a confirmation e-mail to the original sender after ticket creation."""
    opid = f"[OP#{ticket_id}]"
    result = _template_new_ticket(opid, title)
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


def send_comment_mail(clientmail: str, ticket_id: int, title: str, content: str, actor: str):
    """Send a comment notification e-mail to the ticket's client address."""
    opid = f"[OP#{ticket_id}]"
    logger.info("Sending comment mail with ticket code %s.", opid)
    result = _template_comment_mail(opid, title, content, actor)
    if result is None:
        logger.info("No comment mail template configured – skipping.")
        return
    subject, body_plain, body_html = result
    SMTPClient.send_mail(
        clientmail,
        subject,
        actor,
        content_html=body_html,
        content_plain=body_plain,
    )


def send_status_mail(clientmail: str, ticket_id: int, title: str, statusmsg: str, actor: str):
    """Send a status-change e-mail to the ticket's client address."""
    opid = f"[OP#{ticket_id}]"
    logger.info("Sending status mail with ticket code %s.", opid)
    result = _template_status_mail(opid, title, statusmsg)
    if result is None:
        logger.info("No status mail template configured – skipping.")
        return
    subject, body_plain, body_html = result
    SMTPClient.send_mail(
        clientmail,
        subject,
        actor,
        content_html=body_html,
        content_plain=body_plain,
    )
