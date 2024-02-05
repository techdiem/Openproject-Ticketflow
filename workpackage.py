import requests
import json
from config import config

class Workpackage():
    def __init__(self, message) -> None:
        self.message = message
        self.id = None
        text = f"Absender: {message.sender}\n---------------\n{message.body}"
        self.parameters = {"subject": message.subject, 
                "description": {
                "format": "textile",
                "raw": text
            },"_links": {
                "type": {
                "href": "/openproject/api/v3/types/8"
                },
                "status": {
                "href": "/openproject/api/v3/statuses/1"
                },
                "priority": {
                "href": "/openproject/api/v3/priorities/8"
                }
            },
            "customField1": {
                "href": "/openproject/api/v3/custom_options/6"
            }
        } 

    def post_request(self, context, data=None, files=None, headers=None):
        r = requests.post(f'{config.get("OpenProject", "base_url")}{context}', 
                          auth=('apikey', config.get("OpenProject", "api_key")), 
                          data=data, 
                          verify=False, 
                          headers=headers,
                          files=files) 
        return r

    def publish(self):
        headers = {"Content-type": "application/json"}
        r = self.post_request("/api/v3/projects/5/work_packages", headers=headers, data=json.dumps(self.parameters))
        return r
    
    def add_attachment(self, filename, filecontent):
        payload = {"fileName": filename, 
                   "description": {"raw": filename}}
        meta = {"file": ("attachment", filecontent), 
                       "metadata": (None, json.dumps(payload))}
        r = self.post_request(f"/api/v3/work_packages/{self.id}/attachments", files=meta)
        return r
