import json
from config import config
from integrations.activity import Activity
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
        #Fetch activity details and return comment object
        activity = Activity.getByID(activityID)
        if (activity.type == "Activity::Comment"):
            comment = Comment(activity.data["comment"]["raw"],
                            activity.data["comment"]["format"])
            return comment
        else:
            return None
