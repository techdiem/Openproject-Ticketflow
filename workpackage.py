import requests
import json
from config import config

class Workpackage():
    def __init__(self, title, text) -> None:
        self.id = None
        self.title = title
        self.text = text
        self._base_url = config.get("OpenProject", "base_url")

        #Detect subfolder in base URL
        url_parts = self._base_url.split("/")
        if (len(url_parts) > 3):
            self._install_subfolder = f"/{url_parts[2]}"
        else:
            self._install_subfolder = ""

        self.parameters = {"subject": self.title, 
                "description": {
                "format": "textile",
                "raw": self.text
            },"_links": {
                "type": {
                "href": f"{self._install_subfolder}/api/v3/types/{config.get('OpenProject', 'ticket_type_id')}"
                },
                "status": {
                "href": f"{self._install_subfolder}/api/v3/statuses/{config.get('OpenProject', 'ticket_status_id')}"
                },
                "priority": {
                "href": f"{self._install_subfolder}/api/v3/priorities/{config.get('OpenProject', 'ticket_prio_id')}"
                }
            },
            "customField1": {
                "href": f"{self._install_subfolder}/api/v3/custom_options/{config.get('OpenProject', 'ticket_customField1_id')}"
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
        r = self.post_request(f"/api/v3/projects/{config.get('OpenProject', 'ticket_project_id')}/work_packages", headers=headers, data=json.dumps(self.parameters))
        return r
    
    def add_attachment(self, filename, filecontent):
        payload = {"fileName": filename, 
                   "description": {"raw": filename}}
        meta = {"file": ("attachment", filecontent), 
                       "metadata": (None, json.dumps(payload))}
        r = self.post_request(f"/api/v3/work_packages/{self.id}/attachments", files=meta)
        return r
