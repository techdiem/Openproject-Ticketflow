import json
from config import config
from integrations.apiconnection import get_request, post_request

class Activity():
    def __init__(self, type:str, data) -> None:
        self.type = type
        self.data = data
    
    @staticmethod
    def getByID(activityID):
        result = get_request(f"/api/v3/activities/{activityID}")
        data = json.loads(result.content)
        
        activity = Activity(data["_type"], data)
        return activity

