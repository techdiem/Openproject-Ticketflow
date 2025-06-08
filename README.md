# OpenProject_Ticketflow
OpenProject-Mail bridge for usage as a support ticket application

- Create OpenProject Workpackages from Mails fetched via IMAP
- Mail info on ticket creation or status change
- Bridge OpenProject comments to mail
- Bridge mail answers to OpenProject comments

## Installation
Tested on Debian 12, Python 3.13, OpenProject 16
- Create a service user to run the application, e.g. `adduser ticketflow --system`
- Clone the repo to a local folder, e.g. `/opt/openproject-ticketflow` and switch into this directory
- Create a virtual environment for dependencies: `python3 -m venv .\venv`
- Install dependencies: `venv\bin\pip3 install -r requirements.txt`
- Create a config and edit the values to your environment: `cp settings.example.conf settings.conf`
- Make sure that the service user has read permissions on all the files in the software folder and write permissions to the logfile destination configured in settings.conf (Recommended: `/var/log/ticketflow.log` including logrotate config)
- Call the script: `venv\bin\python3 ticketflow.py`
- Put it into a crontab: `/etc/cron.d/ticketflow`: `*/5 * * * * ticketflow cd /opt/openproject-ticketflow && ./venv/bin/python3 ticketflow.py 2&>1 >/dev/null`

## Configuration
- Create a user in OpenProject, IT-Support or similar
- Login with this user, switch to My Account via the profile icon in the upper right corner
- Generate an API Token using the access tokens menu
- Insert it as `api_key` in the config file
- The bot handle config can be determined easily by trying to mention the bot user in a comment field by another user
- Configure the other settings guided by the comments in the settings file

## Upgrading
- Replace all files in `/opt/openproject-ticketflow` by the new files, keep only settings.conf
- Adapt your config file to the newest version based on the release notes
- Run `venv\bin\pip3 install -r requirements.txt` to update dependencies
