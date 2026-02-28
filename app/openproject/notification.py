import json
from openproject.client import op_client


class Notification:
    def __init__(
        self,
        notification_id: int,
        reason: str,
        updated_at: str,
        actor: dict,
        activity_id: str,
        resource_id: str,
    ) -> None:
        self.id = notification_id
        self.reason = reason
        self.updated_at = updated_at
        self.actor = actor
        self.activity_id = activity_id
        self.resource_id = resource_id

    @staticmethod
    def get_notification_collection() -> list["Notification"]:
        """Returns all unread notifications (up to 100)."""
        parameters = {
            "filters": json.dumps(
                [{"readIAN": {"operator": "=", "values": ["f"]}}]
            )
        }
        result = op_client.get(
            "/api/v3/notifications?offset=1&pageSize=100",
            params=parameters,
        )
        data: dict = json.loads(result.content)
        notifications: list[Notification] = []
        if data["count"] > 0:
            for element in data["_embedded"]["elements"]:
                notifications.append(
                    Notification(
                        element["id"],
                        element["reason"],
                        element["updatedAt"],
                        element["_links"]["actor"],
                        element["_links"]["activity"]["href"].split("/")[-1],
                        element["_links"]["resource"]["href"].split("/")[-1],
                    )
                )
        return notifications

    def set_read(self) -> None:
        headers = {"Content-Type": "application/json"}
        op_client.post(f"/api/v3/notifications/{self.id}/read_ian", headers=headers)

    @staticmethod
    def set_all_read() -> None:
        headers = {"Content-Type": "application/json"}
        op_client.post("/api/v3/notifications/read_ian", headers=headers)
