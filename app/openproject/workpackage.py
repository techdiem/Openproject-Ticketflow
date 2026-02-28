import json
from markdownify import markdownify as md
from config import config
from openproject.client import op_client


class Workpackage:
    def __init__(
        self,
        title: str,
        text: str,
        clientmail: str,
        text_format: str = "textile",
        ticket_id: int | None = None,
        lock_version: int | None = None,
        status: str | None = None,
    ) -> None:
        self.id = ticket_id
        self.title = "No title" if title == "" else title
        self.text = text
        self.text_format = text_format
        self.clientmail = clientmail
        self.lock_version = lock_version
        self.status = status

        # Determine optional subfolder prefix for href paths (e.g. /openproject in base URL)
        url_parts = config.get("OpenProject", "base_url").split("/")
        self._install_subfolder = f"/{url_parts[3]}" if len(url_parts) > 3 else ""

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def publish(self) -> None:
        parameters: dict = {
            "subject": self.title,
            "description": {"format": "markdown"},
            "_links": {
                "type": {
                    "href": f"{self._install_subfolder}/api/v3/types/"
                            f"{config.get('OpenProject', 'ticket_type_id')}"
                },
                "status": {
                    "href": f"{self._install_subfolder}/api/v3/statuses/"
                            f"{config.get('OpenProject', 'ticket_status_id')}"
                },
                "priority": {
                    "href": f"{self._install_subfolder}/api/v3/priorities/"
                            f"{config.get('OpenProject', 'ticket_prio_id')}"
                },
            },
            config.get("OpenProject", "ticket_usermail_field"): self.clientmail,
        }

        parameters["description"]["raw"] = (
            md(self.text) if self.text_format == "html" else self.text
        )

        headers = {"Content-Type": "application/json"}
        result = op_client.post(
            f"/api/v3/projects/{config.get('OpenProject', 'ticket_project_id')}/work_packages",
            headers=headers,
            data=json.dumps(parameters),
        )
        return result

    def add_attachment(self, filename: str, filecontent: bytes) -> None:
        payload = {"fileName": filename, "description": {"raw": filename}}
        meta = {
            "file": ("attachment", filecontent),
            "metadata": (None, json.dumps(payload)),
        }
        return op_client.post(
            f"/api/v3/work_packages/{self.id}/attachments",
            files=meta,
        )

    def set_status(self, status_id: int | str) -> None:
        headers = {"Content-Type": "application/json"}
        data = {
            "_links": {
                "status": {
                    "href": f"{self._install_subfolder}/api/v3/statuses/{status_id}"
                }
            },
            "lockVersion": self.lock_version,
        }
        op_client.patch(
            f"/api/v3/work_packages/{self.id}",
            headers=headers,
            data=json.dumps(data),
        )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_id(workpackage_id: int | str) -> "Workpackage | None":
        result = op_client.get(f"/api/v3/work_packages/{workpackage_id}")
        if result.status_code != 200:
            return None
        data: dict = json.loads(result.content)
        return Workpackage(
            data["subject"],
            data["description"]["raw"],
            data.get(config.get("OpenProject", "ticket_usermail_field"), ""),
            ticket_id=data["id"],
            lock_version=data["lockVersion"],
            status=data["_links"]["status"]["href"].split("/")[-1],
        )
