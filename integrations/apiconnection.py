from config import config
import requests

def post_request(context, data=None, files=None, headers=None):
    r = requests.post(f'{config.get("OpenProject", "base_url")}{context}', 
                        auth=('apikey', config.get("OpenProject", "api_key")), 
                        data=data, 
                        verify=False, 
                        headers=headers,
                        files=files) 
    return r

def get_request(context, headers=None, params=None):
    r = requests.get(f'{config.get("OpenProject", "base_url")}{context}',
                     auth=('apikey', config.get("OpenProject", "api_key")),
                     verify=False,
                     headers=headers,
                     params=params)
    return r

def patch_request(context, headers=None, data=None):
    r = requests.patch(f'{config.get("OpenProject", "base_url")}{context}',
                     auth=('apikey', config.get("OpenProject", "api_key")),
                     verify=False,
                     headers=headers,
                     data=data)
    return r
