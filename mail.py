from email.header import decode_header
from datetime import datetime

class Mail():
    def __init__(self, message, imappointer) -> None:
        self.sender = ""
        self.message = message
        self.subject = ""
        self.body = ""
        self.date = datetime.now()
        self.content_type = ""
        self.attachments = []
        self.imappointer = imappointer

        self._parse_mail()
    

    def _parse_mail(self):
        #Parser adapted from https://www.thepythoncode.com/article/reading-emails-in-python
        subject, encoding = decode_header(self.message["Subject"])[0]
        if isinstance(subject, bytes):
            # if it's a bytes, decode to str
            if(encoding == None):
                encoding = "utf-8"
            subject = subject.decode(encoding)
        From, encoding = decode_header(self.message.get("From"))[0]
        if isinstance(From, bytes):
            if(encoding == None):
                encoding = "utf-8"
            From = From.decode(encoding)

        if subject == "":
            #Empty subjects are not allowed for OpenProject work packages
            subject = "Kein Titel"
        
        self.subject = subject
        self.sender = From
        self.date = self.message['Date']


        if self.message.is_multipart():
            # multipart message with plain and html
            for part in self.message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                try:
                    body = part.get_payload(decode=True).decode()
                except:
                    pass
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    # print text/plain emails and skip attachments
                    self.body = body
                    self.content_type = content_type
                elif "attachment" in content_disposition:
                    # download attachment
                    filename = part.get_filename()
                    if filename:
                        buffer = part.get_payload(decode=True)
                        fileName = part.get_filename()
                        if bool(fileName):
                            self.attachments.append([filename, buffer])
        else:
            content_type = self.message.get_content_type()
            body = self.message.get_payload(decode=True).decode()
            self.body = body
            self.content_type = content_type
