# Changelog

## v0.2.4 - 2026-06-09

Experience polish and bug-fix release.

### Changed

- Renamed the cover translation page to cover title configuration.
- Cover title mappings now support both a custom main title and a custom subtitle per Emby library name.
- Existing subtitle-only translation data remains compatible and is interpreted as an empty custom main title plus the previous subtitle.

### Fixed

- Cover uploads now prefer Emby's base64 image upload path, which remains effective when StrmAssistant notification enhancement is enabled.
- Cover upload verification now reads CollectionFolder Primary tags through the user item API before reporting success, avoiding the direct `/Items/{id}` 404 trap.

### Verified

- `.venv/bin/python -m unittest tests.test_emby_cover_upload`
- `.venv/bin/python -m unittest tests.test_title_mapping`
- `.venv/bin/python -m unittest discover tests`
- `npm run build`
- `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py`
- `git diff --check`
- Reversible live check against one Emby media-library cover: base64 upload changed the Primary tag and restoring the previous image succeeded.

## v0.2.3 - 2026-06-06

Patch release for the header log shortcut and TMDB ranking subscription fetch sizes.

### Changed

- TMDB RSS ranking subscriptions now fetch fixed backend page counts without exposing extra user-facing controls.
- Movie popular, movie top-rated, TV popular, and TV top-rated fetch 5 TMDB pages each, yielding up to 100 unique normalized items after de-duplication.
- Movie now-playing, TV on-the-air, trending movie week, and trending TV week fetch 2 TMDB pages each, yielding up to 40 unique normalized items after de-duplication.

### Fixed

- The top-right header log button opens the lightweight log quick-window again instead of navigating directly to the full bottom-nav log center.

### Verified

- `npm run build`
- `.venv/bin/python -m unittest tests.test_tmdb_ranking_service`
- `.venv/bin/python -m compileall app core main.py`
- `docker compose -f docker-compose.example.yml config`
- `git diff --check`
- Local health endpoint returns `0.2.3`

## v0.2.2 - 2026-06-06

Hotfix release for RSS task visibility after browser refresh.

### Fixed

- Directly loading or refreshing `#rss` now fetches RSS task data during initial route hydration, so persisted tasks no longer appear empty until the user clicks through the bottom tool menu.
- Consolidated route-specific initial data loading for RSS, Webhook, diagnostics, logs, config assistant, notification config, and Emby helper pages to reduce the same refresh-only failure class.

### Verified

- `node --check static/app.js`
- `.venv/bin/python -m compileall -q -x '(^|/)\\.venv/' .`
- `git diff --check`
- Local API check for `/api/rss/tasks` with a temporary RSS task fixture
- Browser direct-load smoke check for `#rss` with a temporary RSS task fixture

## v0.2.1 - 2026-06-05

Patch release focused on extending RSS real-library subscriptions with TMDB ranking sources.

### Added

- Added TMDB as a third RSS real-library task source alongside ordinary RSS/Douban and JavDB.
- Added eight explicit TMDB ranking options: movie popular, movie top rated, movie now playing, TV popular, TV top rated, TV on the air, trending movies weekly, and trending TV weekly.
- Added direct TMDB ranking normalization so TMDB tasks use returned TMDb IDs instead of the RSS/Douban title-to-TMDb matching path.
- Added regression tests for TMDB ranking option mapping, movie/TV normalization, and endpoint invocation.

### Changed

- RSS task cards and configuration checks now understand TMDB tasks and no longer report them as missing an RSS URL.
- TMDB RSS form mode hides RSS URL and JavDB/Flaresolverr fields, then locks media type from the selected TMDB list.
- Updated app, frontend, package, README, compose comment, and static cache markers to `v0.2.1`.

### Verified

- `python -m unittest tests.test_tmdb_ranking_service`
- `node --check static/app.js`
- `npm run build`
- `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py`
- `docker compose -f docker-compose.example.yml config`
- `git diff --check`
- Local API and browser smoke checks for the RSS page and health endpoint

## v0.2.0 - 2026-06-04

Release focused on operations tooling around the stable cover and real-library workflows.

### Added

- Webhook debug helper with enable-state visibility, template/layout/capture-mode checks, template-file validation, Emby config completeness checks, recent Webhook logs, recent task logs, recommended Emby events, payload examples, and local Payload parsing preview.
- Tools overview page with RSS, Webhook debug, diagnostics, log center, and config assistant cards.
- Diagnostics assistant checks for Emby config, template/font/layout resources, Webhook state, automatic-cover task links, RSS paths, and Cron format.
- Log center filters for errors, warnings, recent 24 hours, full logs, expandable details, repeated issue hotspots, and common explanations for 401, cover upload failure, missing templates, and Cron issues.
- Config assistant for read-only grouped configuration readiness across Emby, metadata, RSS, cover resources, Webhook, and notification scope.
- Minimal `npm run build` script for static frontend release checks.

### Changed

- Promoted app and frontend version markers to `v0.2.0`.
- Refreshed static asset cache keys for the v0.2.0 frontend.

### Fixed

- Fixed the tools overview API when internally aggregating log summary data.
- Webhook Payload preview now accepts both raw JSON objects and frontend text-payload preview requests.

### Verified

- `node --check static/app.js`
- `npm run build`
- `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py`
- `docker compose -f docker-compose.example.yml config`
- `git diff --check`
- Local API checks for `/api/health`, `/api/tools/summary`, `/api/webhook/debug/summary`, `/api/webhook/debug/parse`, `/api/diagnostics/summary`, `/api/logs/summary`, and `/api/config_assistant/summary`

## v0.1.1 - 2026-06-03

Stable patch release after NAS/local validation.

### Fixed

- Bottom navigation now stays within a compact floating boundary and no longer covers page content with a full-width dark frame.
- Webhook enable/disable state persists after save and page refresh.

### Verified

- `node --check static/app.js`
- `.venv/bin/python -m compileall main.py app core config_manager.py constants.py`
- `docker compose -f docker-compose.example.yml config`
- Local health endpoint: `/api/health`

## v0.1.0 - 2026-06-03

First stable ALSemby release.

### Included

- Complete media-library cover system: manual cover generation, cover design, automatic cover tasks, cover backup/restore, font management, template management, and translation config.
- Tool system focused on RSS real-library subscriptions and Webhook event intake.
- Settings focused on Emby, notification, proxy, TMDB, and account management.
- RSS real-library support for ordinary RSS/Douban-style media feeds and the built-in JavDB ranking source.
- Chill-style direct Emby media-library cover upload flow, shared by manual cover, automatic tasks, saved/scheduled tasks, backup restore, and Webhook-triggered cover generation.
- Persistent Docker compose layout with `./config:/app/config` and user-mounted Emby media paths for `/strm`, `/strm1`, and `/strm2`.

### Fixed

- Webhook enable/disable state now persists correctly after save and page refresh.
- Bottom navigation now renders as a compact frosted floating dock instead of a heavy black content-covering block.

### Verified

- `node --check static/app.js`
- `.venv/bin/python -m compileall main.py app core config_manager.py constants.py`
- `docker compose -f docker-compose.example.yml config`
- Local Webhook config persistence loop
- Local browser refresh check for Webhook enabled state
- Local health endpoint: `/api/health`

## v0.1.0-beta.2 - 2026-06-03

NAS retest release focused on restoring the Chill-style Emby cover upload flow.

### Changed

- Restored cover application to the early Chill Poster method: direct binary upload, Base64 fallback, then real-ID fallback.
- Removed the temporary ALSemby-hosted cover URL flow and Primary image-change verification from cover application.
- Kept manual cover, automatic cover, saved/scheduled tasks, Webhook-triggered cover generation, and backup restore on the same direct upload path.
- Removed Dockerfile app name/version env defaults and default credential env overrides.

### Verified

- `node --check static/app.js`
- `.venv/bin/python -m compileall main.py app core config_manager.py constants.py`
- `docker compose -f docker-compose.example.yml config`
- Local health endpoint: `/api/health`

## v0.1.0-beta.1 - 2026-06-02

First ALSemby test release for local/NAS deployment trials.

### Included

- Focused product scope: Emby library cover system, RSS real-library workflow, Webhook, and core settings.
- Complete cover-system navigation: manual cover, cover design, automatic cover, cover backup, font management, template management, and translation config.
- Tool system reduced to RSS real library and Webhook.
- Settings reduced to Emby, notification, proxy, TMDB, and account management.
- RSS real-library support for normal media RSS/Douban-style feeds and built-in JavDB ranking source.
- Bottom dock navigation with grouped cover/tool/settings popovers.
- Local action confirmations for operations that may connect to Emby, refresh cover backups, create snapshots, send notification tests, or clear logs.
- Docker Hub image `aliaosha2521/alsemby` with `latest` and `v0.1.0-beta.1` tags.
- Docker compose example with persistent volumes, media-library path mounts, and service healthcheck.

### Safety Notes

- Opening the UI does not connect to Emby and does not scan media directories.
- Real RSS/Webhook/media-library jobs should be tested only after paths and credentials are configured.
- This beta was verified locally without connecting to Emby, scanning NAS/CD2/media directories, or running real RSS/Webhook/media tasks.

### Verified

- `node --check static/app.js`
- `python3 -m compileall main.py app core`
- `docker compose -f docker-compose.example.yml config`
- Browser route checks for dashboard, cover pages, RSS, Webhook, and settings pages
- Local health endpoint: `/api/health`
