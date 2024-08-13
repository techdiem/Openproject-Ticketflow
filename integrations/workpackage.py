import json
from config import config
from integrations.apiconnection import post_request, get_request, patch_request
from markdownify import markdownify as md

class Workpackage():
    def __init__(self, title, text, clientmail, text_format="textile", id=None, lockVersion=None, status=None) -> None:
        self.id = id
        self.title = title
        self.text = text
        self.text_format = text_format
        self.clientmail = clientmail
        self._base_url = config.get("OpenProject", "base_url")
        self.lockVersion = lockVersion
        self.status = status

        #Detect subfolder in base URL
        url_parts = self._base_url.split("/")
        if (len(url_parts) > 3):
            self._install_subfolder = f"/{url_parts[2]}"
        else:
            self._install_subfolder = ""

    def publish(self):
        self.parameters = {"subject": self.title, 
            "description": {
                "format": "markdown",
            },
            "_links": {
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
            config.get("OpenProject", "ticket_usermail_field"): self.clientmail
        }
        
        if(self.text_format == "html"):
            self.parameters["description"]["raw"] = md(self.text)
        else:
            self.parameters["description"]["raw"] = self.text

        headers = {"Content-type": "application/json"}
        r = post_request(f"/api/v3/projects/{config.get('OpenProject', 'ticket_project_id')}/work_packages", headers=headers, data=json.dumps(self.parameters))
        return r
    
    def add_attachment(self, filename, filecontent):
        payload = {"fileName": filename, 
                   "description": {"raw": filename}}
        meta = {"file": ("attachment", filecontent), 
                       "metadata": (None, json.dumps(payload))}
        r = post_request(f"/api/v3/work_packages/{self.id}/attachments", files=meta)
        return r
    
    def set_status(self, status_id):
        headers = {"Content-type": "application/json"}
        data = {
            "_links": {
                "status": {
                        "href": f"{self._install_subfolder}/api/v3/statuses/{status_id}"
                }
            },
            "lockVersion": self.lockVersion
        }
        result = patch_request(f"/api/v3/work_packages/{self.id}",
                               headers=headers,
                               data=json.dumps(data))
        return result

    @staticmethod
    def getByID(workpackage_id):
        result = get_request(f"/api/v3/work_packages/{workpackage_id}")
        if result.status_code == 200:
            data = json.loads(result.content)
            ticket = Workpackage(data["subject"],
                                data["description"]["raw"],
                                data[config.get("OpenProject", "ticket_usermail_field")],
                                id=data["id"],
                                lockVersion=data["lockVersion"],
                                status=data["_links"]["status"]["href"].split("/")[-1])
            return ticket
        else:
            return None
