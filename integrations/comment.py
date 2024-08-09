import requests
import json
from config import config
from integrations.apiconnection import get_request, post_request

class Comment():
    def __init__(self, format, rawtext) -> None:
        self.format = format
        self.rawtext = rawtext

    @staticmethod
    def getByActivityID(activityID):
        result = get_request(f"/api/v3/activities/{activityID}")
        data = json.loads(result.content)
        if (data["_type"] == "Activity::Comment"):
            comment = Comment(data["comment"]["format"],
                            data["comment"]["raw"])
            return comment
        else:
            return None
