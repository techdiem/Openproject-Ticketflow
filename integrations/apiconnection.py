import requests
from config import config

def post_request(context, data=None, files=None, headers=None):
    r = requests.post(f'{config.get("OpenProject", "base_url")}{context}',
                        auth=('apikey', config.get("OpenProject", "api_key")),
                        data=data,
                        verify=config.get("OpenProject", "https_verification") == "true",
                        headers=headers,
                        files=files,
                        timeout=30)
    return r

def get_request(context, headers=None, params=None):
    r = requests.get(f'{config.get("OpenProject", "base_url")}{context}',
                     auth=('apikey', config.get("OpenProject", "api_key")),
                     verify=config.get("OpenProject", "https_verification") == "true",
                     headers=headers,
                     params=params,
                     timeout=30)
    return r

def patch_request(context, headers=None, data=None):
    r = requests.patch(f'{config.get("OpenProject", "base_url")}{context}',
                     auth=('apikey', config.get("OpenProject", "api_key")),
                     verify=config.get("OpenProject", "https_verification") == "true",
                     headers=headers,
                     data=data,
                     timeout=30)
    return r
