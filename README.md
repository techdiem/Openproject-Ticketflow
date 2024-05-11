# OpenProject_Mailfetch
Tool to create Workpackages in OpenProject from Mails fetched via IMAP.

## Installation & Usage
- Clone the repo to a local folder, e.g. `/opt/openproject_mailfetch`
- Install dependencies: `pip3 install -r requirements.txt`
- Create a config and edit the values to your environment: `cp settings.conf.example settings.conf`
- Call the script: `python3 openproject_mailfetch.py`, put this command into a crontab for periodic mail check
