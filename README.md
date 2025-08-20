# OpenProject_Ticketflow
OpenProject-Mail bridge for usage as a support ticket application

- Create OpenProject Workpackages from Mails fetched via IMAP
- Mail info on ticket creation or status change
- Bridge OpenProject comments to mail
- Bridge mail answers to OpenProject comments

## Installation / Update
Tested on Debian 12, Python 3.13, OpenProject 16
Use the provided script to install/uninstall/update the software:
- `chmod +x ticketflow_installer.sh`
- `./ticketflow_installer.sh install Openproject-Ticketflow-1.1.0.zip`
Usage: `./ticketflow_installer.sh {install|update|uninstall} [Application-ZIP-File]`

The script creates a service user, crontab configuration, python-venv, copys the application files and sets permissions.

Make sure that the service user has write permissions to the logfile destination configured in settings.conf (Recommended: `/var/log/ticketflow.log` including logrotate config)

## Configuration
- Create a user in OpenProject, IT-Support or similar
- Login with this user, switch to My Account via the profile icon in the upper right corner
- Generate an API Token using the access tokens menu
- Insert it as `api_key` in the config file
- The bot handle config can be determined easily by trying to mention the bot user in a comment field by another user
- Configure the other settings guided by the comments in the settings file
