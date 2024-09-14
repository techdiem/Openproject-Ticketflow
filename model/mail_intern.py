from dataclasses import dataclass
from imap_tools import EmailAddress, MailAttachment

@dataclass
class MailIntern():
    uid:int
    subject:str
    text_plain:str
    text_html:str
    sender:EmailAddress
    attachments:list[MailAttachment]
