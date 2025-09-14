from string import Template
from bs4 import BeautifulSoup
from config import config

def template_general(subject, plain, html, substitution:dict):
    sub = Template(subject).safe_substitute(substitution)

    if plain != "":
        plain = Template(plain).safe_substitute(substitution)
    else:
        plain = ""
    if html != "":
        html = Template(html).safe_substitute(substitution)
    else:
        html = ""

    return sub, plain, html


def template_newmail(opid:str, subject:str):
    sub = config.get("Templates", "newticket_subject")
    plain = config.get("Templates", "newticket_plain")
    html = config.get("Templates", "newticket_html")

    #At least one template must be used
    if plain == "" and html == "":
        return None

    substitution = {
        "opid": str(opid),
        "subject": subject,
    }
    return template_general(sub, plain, html, substitution)

def template_commentmail(opid:str, subject:str, content:str, actor:str):
    sub = config.get("Templates", "commentmail_subject")
    plain = config.get("Templates", "commentmail_plain")
    html = config.get("Templates", "commentmail_html").replace("\n", "")

    #At least one template must be used
    if plain == "" and html == "":
        return None

    soup = BeautifulSoup(content, "html.parser")
    plaincontent = soup.get_text()

    substitution = {
        "opid": str(opid),
        "subject": subject,
        "content": content,
        "actor": actor
    }
    return template_general(sub, plaincontent, html, substitution)

def template_statusmail(opid:str, subject:str, statuschange:str):
    sub = config.get("Templates", "statusmail_subject")
    plain = config.get("Templates", "statusmail_plain")
    html = config.get("Templates", "statusmail_html").replace("\n", "")

    #At least one template must be used
    if plain == "" and html == "":
        return None

    substitution = {
        "opid": str(opid),
        "subject": subject,
        "statuschange": statuschange
    }
    return template_general(sub, plain, html, substitution)
