import json
from integrations.apiconnection import get_request

class Activity():
    def __init__(self, activitiy_type:str, data) -> None:
        self.type = activitiy_type
        self.data = data

    @staticmethod
    def get_by_id(activity_id):
        result = get_request(f"/api/v3/activities/{activity_id}")
        data = json.loads(result.content)

        activity = Activity(data["_type"], data)
        return activity
