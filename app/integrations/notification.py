import json
from integrations.apiconnection import get_request, post_request

class Notification():
    def __init__(self, id, reason, updated_at, actor, activity_id, resource_id) -> None:
        self.id = id
        self.reason = reason
        self.updated_at = updated_at
        self.actor = actor
        self.activity_id = activity_id
        self.resource_id = resource_id

    @staticmethod
    def get_notification_collection():
        parameters = {"filters": json.dumps([{ "readIAN": { "operator": "=", "values": ["f"] } }]) }
        result = get_request("/api/v3/notifications?offset=1&pageSize=100", params=parameters)
        data = json.loads(result.content)
        notifications = []
        if data["count"] > 0:
            for element in data["_embedded"]["elements"]:
                notify = Notification(element["id"],
                                      element["reason"],
                                      element["updatedAt"],
                                      element["_links"]["actor"],
                                      element["_links"]["activity"]["href"].split("/")[-1],
                                      element["_links"]["resource"]["href"].split("/")[-1])
                notifications.append(notify)
        return notifications

    def set_read(self):
        headers = {"Content-type": "application/json"}
        post_request(f"/api/v3/notifications/{self.id}/read_ian", headers=headers)

    @staticmethod
    def set_all_read():
        headers = {"Content-type": "application/json"}
        post_request("/api/v3/notifications/read_ian", headers=headers)
