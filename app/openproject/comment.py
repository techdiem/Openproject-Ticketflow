import json
from openproject.activity import Activity
from openproject.client import op_client


class Comment:
    def __init__(self, rawtext: str, textformat: str = "markdown") -> None:
        self.format = textformat
        self.rawtext = rawtext

    def publish(self, workpackage_id: int | str) -> None:
        headers = {"Content-Type": "application/json"}
        data = {"comment": {"raw": self.rawtext}}
        op_client.post(
            f"/api/v3/work_packages/{workpackage_id}/activities",
            data=json.dumps(data),
            headers=headers,
        )

    @staticmethod
    def get_by_activity(activity: Activity) -> "Comment | None":
        """Returns a Comment object if the activity is a comment, otherwise None."""
        if activity.type == "Activity::Comment":
            return Comment(
                activity.data["comment"]["raw"],
                activity.data["comment"]["format"],
            )
        return None
