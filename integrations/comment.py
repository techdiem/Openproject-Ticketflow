import json
from config import config
from integrations.apiconnection import get_request, post_request

class Comment():
    def __init__(self, rawtext, format="markdown") -> None:
        self.format = format
        self.rawtext = rawtext

    def publish(self, workpackageID):
        headers = {"Content-type": "application/json"}
        data = {
            "comment": {
                    "raw": self.rawtext
            }
        }
        result = post_request(f"/api/v3/work_packages/{workpackageID}/activities",data=json.dumps(data), headers=headers)
        return result

    @staticmethod
    def getByActivityID(activityID):
        result = get_request(f"/api/v3/activities/{activityID}")
        data = json.loads(result.content)
        if (data["_type"] == "Activity::Comment"):
            comment = Comment(data["comment"]["raw"],
                            data["comment"]["format"])
            return comment
        else:
            return None
