import json
from config import config
from integrations.apiconnection import get_request, post_request

class Notification():
    def __init__(self, id, reason, updatedAt, actor, activityID, resourceID) -> None:
        self.id = id
        self.reason = reason
        self.updatedAt = updatedAt
        self.actor = actor
        self.activityID = activityID
        self.resourceID = resourceID

    @staticmethod
    def getNotificationCollection():
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

    def setRead(self):
        headers = {"Content-type": "application/json"}
        post_request(f"/api/v3/notifications/{self.id}/read_ian", headers=headers)

    @staticmethod
    def setAllRead():
        headers = {"Content-type": "application/json"}
        post_request("/api/v3/notifications/read_ian", headers=headers)
