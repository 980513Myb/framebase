# FrameBase

FrameBase is a local Emby cover-generation service with manual design, scheduled cover updates, Webhook-triggered automation, resource management, and enterprise WeChat notifications.

## Local Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Open `http://localhost:5256/static/index.html`. The default login is `admin` / `password`.

## Docker

Build and start the local FrameBase image:

```bash
docker compose up -d --build
```

The Compose service and container are both named `framebase`; the image tag is `framebase:local`.

When replacing an existing `alsemby` deployment, stop and remove only the old container first. Keep the existing host directories mounted to `/app/config`, `/app/backups`, `/app/fonts`, `/app/templates`, and `/app/layouts` so your settings and cover resources are retained.

## Included Features

- Manual and custom Emby cover generation
- Scheduled and Webhook-triggered automatic covers
- Cover backups, templates, layouts, fonts, and library title mappings
- Emby, TMDB, proxy, and account settings
- Enterprise WeChat notification configuration and test messages
