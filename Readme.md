# Course App

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p var/cache var/generated
```

The process user must have write access to `var/cache` and `var/generated`.

## Run Locally

Run with the remote Google Sheets config:

```bash
.venv/bin/python app.py
```

Run with the local fixture config:

```bash
.venv/bin/python app.py --config config/config.local.ini
```

## Run In Production

Production should run the Flask app behind Gunicorn and nginx.

`wsgi.py` loads the application with the default config, so production settings should be stored in `config/config.ini`.

Example direct start:

```bash
.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 wsgi:app
```

## systemd

Create `/etc/systemd/system/course.service`:

```ini
[Unit]
Description=Course Flask application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/course
Environment="PATH=/opt/course/.venv/bin"
ExecStart=/opt/course/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Reload and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now course.service
sudo systemctl status course.service
```

## nginx

Create `/etc/nginx/sites-available/course`:

```nginx
server {
    listen 80;
    server_name example.com;

    location /static/ {
        alias /opt/course/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and reload nginx:

```bash
sudo ln -s /etc/nginx/sites-available/course /etc/nginx/sites-enabled/course
sudo nginx -t
sudo systemctl reload nginx
```

Replace `/opt/course` and `example.com` with your real deployment path and hostname.
