import json
from integrations.activity import Activity
from integrations.apiconnection import post_request

class Comment():
    def __init__(self, rawtext, textformat="markdown") -> None:
        self.format = textformat
        self.rawtext = rawtext

    def publish(self, workpackage_id):
        headers = {"Content-type": "application/json"}
        data = {
            "comment": {
                    "raw": self.rawtext
            }
        }
        result = post_request(f"/api/v3/work_packages/{workpackage_id}/activities",
                              data=json.dumps(data),
                              headers=headers)
        return result

    @staticmethod
    def get_by_activity_id(activity_id):
        #Fetch activity details and return comment object
        activity = Activity.get_by_id(activity_id)
        if activity.type == "Activity::Comment":
            comment = Comment(activity.data["comment"]["raw"],
                            activity.data["comment"]["format"])
            return comment
        else:
            return None
