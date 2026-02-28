import json
from openproject.client import op_client


class Activity:
    def __init__(self, activity_type: str, data: dict) -> None:
        self.type = activity_type
        self.data = data

    @staticmethod
    def get_by_id(activity_id: int | str) -> "Activity":
        result = op_client.get(f"/api/v3/activities/{activity_id}")
        data: dict = json.loads(result.content)
        return Activity(data["_type"], data)
