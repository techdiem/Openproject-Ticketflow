# OpenProject Ticketflow
OpenProject mail bridge for use as a support ticket application.

- Create OpenProject work packages from mails fetched via IMAP
- Send mail notifications on ticket creation or status change
- Bridge OpenProject comments to mail
- Bridge mail replies to OpenProject comments

Tested on Debian 13, Python 3.14, OpenProject 17.

## Installation

### Option A: Docker

A ready-to-use [`docker-compose.yaml`](docker-compose.yaml) is provided.

1. Place your `settings.conf` and the mail templates in a local `config/` directory (see [Configuration](#configuration) below).
2. Build the image and start the container:

```bash
docker compose up -d --build
```

The container runs as an unprivileged user, mounts the config directory read-only, and drops all Linux capabilities by default.

### Option B: Manual installation with venv
```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r app/requirements.txt

# Run the application
python app/ticketflow.py
```

#### Logfile

By default, Ticketflow logs to stdout only. To enable file logging, set the `logfile` path in `settings.conf`:

```ini
[General]
logfile = /var/log/ticketflow.log
```

Make sure the user running Ticketflow has write permissions to that path. A logrotate configuration for `/var/log/ticketflow.log` is recommended for production use.

#### systemd service

To run Ticketflow as a system service, create `/etc/systemd/system/ticketflow.service`, e.g.:

```ini
[Unit]
Description=Ticketflow
After=network.target

[Service]
Type=simple
User=ticketflow
WorkingDirectory=/opt/ticketflow
ExecStart=/opt/ticketflow/venv/bin/python app/ticketflow.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
systemctl daemon-reload
systemctl enable --now ticketflow
```

## Configuration

### settings.conf

Copy the example configuration to `settings.conf` and edit it to match your environment. All options are documented by inline comments in the file. The most important settings:

- **[IMAP]** / **[SMTP]**: mail server credentials and encryption
- **[OpenProject]**: `base_url`, `api_key`, project/type/status IDs, and the bot user handle
- **[Workflow]**: enable or disable comment-to-mail, new-ticket notifications, and status-change mails

To obtain the `api_key`, log in to OpenProject with the bot user, go to **My Account > Access Tokens**, and generate a new API token.

The `botuser_handle` can be determined by trying to mention the bot user in a work package comment field from another account.

### Mail templates

The HTML mail templates for the three notification types are located in the `config/` directory:

- `newticket.html` - sent to the reporter when a new ticket is created
- `commentmail.html` - sent when a work package comment is forwarded by mail
- `statusmail.html` - sent when the work package status changes

Edit these files to match your branding. Each template supports placeholder variables (e.g. `$subject`, `$opid`, `$content`) that are documented in `settings.conf` under the `[Templates]` section. Plain-text fallbacks for each mail type are also configured there.
