# ALSemby Build Log

## 2026-06-01 Chill Source Baseline

- Rebuilt ALSemby from `/Users/aliaosha/Desktop/macmini/chillposter_source/app`.
- Previous ALSemby backed up at `/Users/aliaosha/Desktop/macmini/ALSemby_backup_20260601-211408`.
- Switched to Python 3.12 virtualenv because the extracted source requires newer FastAPI/Uvicorn dependencies.
- Restored the original full startup behavior so we can inspect the complete app before deleting modules.
- Verified local compile with `.venv/bin/python -m compileall .`.
- Started the app from `main.py`; UI is listening on `http://localhost:5256/static/index.html`, gateway on `8011`.
- Smoke checked `/static/index.html`, `/api/load`, `/api/templates_v2`, and `/api/layouts`.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-running-20260601-2128.png`.

## 2026-06-01 First Trim Pass

- Kept the complete cover system navigation: manual cover, cover design, auto cover, cover backup, fonts, templates, translations, RSS real library, and Webhook.
- Removed the visible "netdisk one-stop" navigation group and mobile shortcuts: discovery, resource transfer, media organize, STRM generation, and 302 entry.
- Removed Yingchao and MoviePilot from core configuration navigation and deleted their hidden page templates.
- Unmounted Yingchao, MoviePilot, discovery, transfer, STRM, and media-organize routers from the main UI app.
- Kept Emby config, 115 config, notification config, proxy config, TMDB config, and account management.
- Recompiled `main.py`, `app`, and `static`; restarted the local service on `5256`/`8011`.
- Verified hidden modules now return 404 for representative API paths and the cover template/layout APIs still respond.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-trimmed-nav-20260601-2229.png`.

## 2026-06-01 Bottom Dock Pass

- Removed the 115 config entry from visible navigation and deleted the placeholder 115 config page.
- Unmounted the 302/115 helper router from `main.py`; `/api/config_302/get` now returns 404.
- Reworked navigation into a Chill-style bottom dock with four primary groups: home, cover system, tool system, and settings.
- Cover system popover keeps all seven cover modules: manual cover, cover design, auto cover, cover backup, fonts, templates, and translations.
- Tool system popover currently contains RSS real library and Webhook.
- Settings popover contains Emby config, notification config, proxy config, TMDB config, and account management.
- Added cache-busted CSS/JS links so the browser picks up the bottom dock styling immediately.
- Recompiled `main.py`, `app`, and `static`; restarted the local service on `5256`/`8011`.
- Smoke checked `/static/index.html`, `/api/templates_v2`, `/api/layouts`, and `/api/config_302/get`.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-bottom-dock-20260601-2254.png`.

## 2026-06-01 Premium UI Pass

- Refined the global dark visual system with a softer high-end console surface, glass header, upgraded cards, and stronger spacing.
- Reworked the dashboard hero into a two-column control panel with status cards on the right.
- Added a dashboard command grid for the core routes: manual cover, auto task, RSS real library, and Webhook.
- Improved the empty media-library preview area so it looks intentional before Emby is configured.
- Polished buttons, inputs, cards, and the bottom dock with more consistent radius, contrast, borders, and depth.
- Cache-busted the static CSS/JS links for the premium pass.
- Recompiled `main.py`, `app`, and `static`; smoke checked the static page and core template/layout APIs.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-premium-home-20260601-2310.png`.

## 2026-06-01 Cleanup And Consistency Pass

- Simplified the launcher so ALSemby starts only the management UI on `5256`; the old 302/115 gateway service on `8011` is no longer exposed.
- Removed the STRM monitor shutdown hook from the active lifespan because STRM generation is no longer part of the visible product scope.
- Hardened Telegram notification polling shutdown so an unconfigured notification service can stop cleanly.
- Kept notification polling, RSS task loading, and cover task loading intact.
- Refreshed static cache keys to `alsemby-cleanup-20260601`.
- Added a retained-page visual consistency layer for settings, Webhook, RSS, templates, fonts, and modal/card surfaces.
- Recompiled `main.py`, `app`, and `static`.
- Restarted the local service and smoke checked `/static/index.html`, `/api/templates_v2`, `/api/layouts`, and `/api/config_302/get`; confirmed only `5256` is listening.
- Browser checked the bottom dock menus, Emby settings page, Webhook page, and absence of visible 115/netdisk one-stop entries.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-cleanup-home-20260601-2319.png`.

## 2026-06-01 RSS Path Override Pass

- Kept RSS real-library path controls on the RSS page and added per-subscription Source/Destination override fields.
- Added UI copy for the NAS layout requirement: different subscriptions can point to `/strm`, `/strm1`, or `/strm2` instead of relying only on global paths.
- Extended RSS task schemas and save/edit flows with `source_root` and `link_root`.
- Updated RSS sync execution so each task can instantiate its hard-link manager with its own link root and source-root guard.
- Added source-root filtering in the hard-link manager to avoid matching media from the wrong STRM tree.
- Updated RSS delete cleanup to prefer the task-specific link root before falling back to the global RSS link root.
- Removed hidden legacy page templates for the old subscribe, transfer, media organize, STRM generation, and 302 pages.
- Disabled WeChat/Telegram text callbacks from processing 115/netdisk transfer links; notifications now keep only playback, media-added, and task-complete categories.
- Refreshed static cache keys to `alsemby-rss-paths-20260601`.
- Recompiled `main.py`, `app`, and `core`; restarted the local service on `5256`.
- Smoke checked `/static/index.html`, `/api/templates_v2`, `/api/layouts`, and `/api/config_302/get`; confirmed `8011` is not listening.
- Browser checked the RSS create form, settings popover, absence of visible 115/netdisk/MoviePilot entries, and console errors.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-rss-path-overrides-20260601-2347.png`.

## 2026-06-02 JavDB Ranking RSS Pass

- Added a second RSS real-library task source: `JavDB 榜单`, alongside the existing ordinary RSS/Douban flow.
- Kept the task-level Source/Destination override model so ordinary media can use `/strm` and JAV ranking tasks can use `/strm1`.
- Added JavDB task fields for ranking period and Flaresolverr URL.
- Implemented local JavDB ranking service:
  - fetches ranking codes through Flaresolverr,
  - indexes code-like folders under the configured source root,
  - supports fuzzy matching such as `300MIUM-1336` against `MIUM-1336`,
  - hard-links matched folders into the configured destination root,
  - cleans stale ranking folders from that task destination.
- Wired the RSS executor so `source_type=javdb` bypasses TMDB matching and uses code-based local path matching instead.
- Updated the RSS form UI with source type selection, JavDB period selection, Flaresolverr address, and `/strm1` guidance.
- Refreshed static cache keys to `alsemby-javdb-rss-20260602`.
- Recompiled `main.py`, `app`, and `core`; restarted the local service on `5256`.
- Smoke checked `/static/index.html`, `/api/templates_v2`, `/api/rss/tasks`, and confirmed `8011` is not listening.
- Ran a local temp-folder matcher test only; no JavDB request, Emby connection, NAS scan, or media-directory scan was performed.
- Browser checked the RSS create form in both ordinary RSS and JavDB modes; no console errors.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-javdb-rss-20260602-0010.png`.

## 2026-06-02 RSS Path UI Simplification

- Removed the top-level "路径映射基础配置" card from the RSS real-library page because task-level paths now carry the real `strm` / `strm1` / `strm2` distinction.
- Reworded the task path section to match the old clear Source/Destination style while keeping the per-task model.
- Changed labels to `本订阅源媒体库根目录 (Source)` and `本订阅链接库根目录 (Destination)`.
- Removed the old "留空使用上方基础路径配置" copy from the visible form so operators are guided to fill per-task paths directly.
- Refreshed static cache keys to `alsemby-rss-path-ui-20260602`.
- Recompiled `main.py`, `app`, and `core`; smoke checked `/static/index.html`.
- Browser checked the RSS create form and confirmed the global path block is gone, task-level path fields remain, and no console errors were emitted.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-rss-path-ui-20260602-0022.png`.

## 2026-06-02 JavDB Period Directory Pass

- Confirmed JavDB `daily` ranking can be fetched through Flaresolverr and returns 49 codes.
- Checked the raw JavDB `p=all` page: it returns HTTP 200 and 49 codes, but currently matches the same ordered code list as `daily`.
- Kept all four period options in the UI: daily, weekly, monthly, and all.
- Changed JavDB output behavior so the configured Destination is the ranking root, for example `/strm1/javdb榜单`.
- Added automatic period subdirectories:
  - `daily` -> `日榜`
  - `weekly` -> `周榜`
  - `monthly` -> `月榜`
  - `all` -> `总榜`
- Updated delete cleanup for JavDB tasks to target the same period subdirectory.
- Updated RSS form copy and placeholders to recommend `/strm1` as Source and `/strm1/javdb榜单` as Destination for JavDB tasks.
- Refreshed static cache keys to `alsemby-javdb-period-dirs-20260602`.
- Recompiled `main.py`, `app`, and `core`; smoke checked `/static/index.html`.
- Browser checked the JavDB form and confirmed period options, root output guidance, automatic subdirectory copy, and no console errors.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-javdb-period-dirs-20260602-0034.png`.

## 2026-06-02 JavDB Task-Name Directory Correction

- Superseded the previous period-directory behavior after operator review.
- Changed JavDB real-library output back to the same rule as ordinary RSS tasks: final output path is `Destination / 订阅名称`.
- Kept `daily`, `weekly`, `monthly`, and `all` as ranking-source options only; the selected period no longer controls the folder name.
- Updated RSS execution and delete cleanup to use `link_root/task.name` for JavDB and normal RSS tasks alike.
- Updated UI copy and task-card path display so `/strm1/javdb榜单` is treated as the root and examples show `/strm1/javdb榜单/JavDB周榜`.
- Refreshed static cache keys to `alsemby-javdb-task-name-dirs-20260602`.
- Recompiled `main.py`, `app`, and `core`; restarted the local service on `5256`.
- Browser checked the JavDB create form, confirmed the old automatic period-directory wording is gone, and found no console errors.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-javdb-task-name-dirs-20260602-0043.png`.

## 2026-06-02 JavDB Single Built-In Ranking Pass

- Removed the visible JavDB period selector because anonymous JavDB access only exposes one stable useful ranking surface in practice.
- Standardized JavDB RSS tasks on the built-in monthly ranking internally.
- Forced JavDB task create/update and execution paths to use `jav_period=monthly`, so older hidden values such as daily, weekly, or all cannot leak into runtime behavior.
- Updated the RSS form placeholder, task source display, and usage copy to show only `JavDB 榜单`.
- Kept the output path rule unchanged: `Destination / 订阅名称`.
- Refreshed static cache keys to `alsemby-javdb-monthly-hidden-20260602`.
- Recompiled `main.py`, `app`, and `core`; restarted the local service on `5256`.
- Browser checked the JavDB create form and confirmed no 日榜/周榜/月榜/总榜 selector or wording remains, with no console errors.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-javdb-monthly-hidden-20260602-0053.png`.

## 2026-06-02 Scope Cleanup Pass

- Removed the active 115 cleanup scheduler startup from `main.py` and deleted the old cleanup registration methods from `app/services/task_service.py`.
- Removed unused legacy routers and services for 302/115 gateway, STRM generation, media organize, resource transfer, Yingchao, MoviePilot, and discovery recommendation.
- Removed old frontend state/functions/exports for 302/115, STRM, media organize, resource transfer, Yingchao, MoviePilot, and discovery recommendation from `static/app.js`.
- Removed p115 and Yingchao browser automation dependencies from `requirements.txt`.
- Removed the unused old media organizer core module.
- Reworded RSS task paths to `原始资源目录 (Source)` and `真实库输出目录 (Destination)`; Source, Destination, and Flaresolverr now have no stored default and must be filled by the user.
- Refreshed static cache keys to `alsemby-scope-cleanup-20260602`.
- Recompiled `main.py`, `app`, and `core`; `node --check static/app.js` passed.
- Restarted the local service on `5256`; confirmed only `5256` is listening and old endpoints `/api/config_302/get`, `/api/hdhive/config`, and `/api/moviepilot/config` return `404`.
- Searched `main.py`, `app`, `static`, `core`, and `requirements.txt`; no old 115/p115, Yingchao, MoviePilot, STRM, media-organize, or transfer keywords remain.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-scope-cleanup-20260602-0112.png`.

## 2026-06-02 Designer Panel Polish

- Reworked the manual cover and custom cover designer layout so the left parameter area uses the same restrained dark panel language as the rest of ALSemby instead of the old full-height blue sidebar.
- Fixed the custom cover designer target accordion: it now consistently uses `c_target_obj` for open state, click handling, and content visibility.
- Adjusted default accordion state so both designer pages open with the key setup sections visible while heavier parameter/material sections stay collapsed.
- Added a manual generation workflow card and a custom material-status card so the left column no longer feels like it is missing a section.
- Added a clearer empty preview state for both manual and custom designers.
- Refreshed static cache keys to `alsemby-designer-panel-20260602`.
- `node --check static/app.js` passed; `/static/index.html` returned HTTP `200`.
- Browser checked manual designer rendering: grid layout active, dark side panel width 348px, workflow card visible, and no stale custom accordion target binding remained.
- Browser render captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-designer-panel-20260602-manual-v2.png`.

## 2026-06-02 Shell Navigation Cleanup

- Removed the hidden legacy side navigation DOM and the old immersive sidebar toggle state from `static/index.html` and `static/app.js`.
- Removed the unused mobile liquid-nav DOM, touch-swipe tab code, and inactive indicator state so all widths now use the same bottom 4-entry shell: 主页、封面系统、工具系统、设置.
- Removed sidebar/mobile-nav CSS residue and refreshed static cache keys to `alsemby-shell-cleanup-20260602`.
- `node --check static/app.js` passed; `.venv/bin/python -m compileall main.py app core` passed.
- Searched `main.py`, `app`, `static`, `core`, and `requirements.txt`; no legacy sidebar/mobile-nav residue and no old 115, MoviePilot, Yingchao, netdisk one-stop, discovery, transfer, media-organize, STRM, or 302 keywords remain.
- Browser checked the dashboard shell: visible bottom entries are exactly 主页、封面系统、工具系统、设置; no hidden sidebar/mobile nav nodes remain; no console errors were emitted.
- Browser checked the cover menu and confirmed the seven cover modules remain: 手动封面、封面设计、自动封面、封面备份、字体管理、模板管理、翻译配置.
- Browser checked the RSS form: the top path mapping card is absent, Source/Destination are task-level fields, and JavDB has no visible 日榜/周榜/月榜/总榜 wording.
- Browser renders captured at `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-shell-cleanup-20260602-dashboard.png` and `/Users/aliaosha/Desktop/macmini/ALSemby/docs/alsemby-shell-cleanup-20260602-cover-menu.png`.

## 2026-06-02 Route Stability And Residue Pass

- Removed the main content-area Vue transition wrapper after browser testing showed route body transitions could stall and leave the previous page in the DOM.
- Kept the smaller menu/modal transitions intact; only the full-page route switch was made immediate for stability.
- Refreshed static cache keys to `alsemby-route-stable-20260602`.
- Re-ran `node --check static/app.js` and `.venv/bin/python -m compileall main.py app core`; both passed.
- Re-ran old-scope residue search across `static/index.html`, `static/app.js`, `app`, `core`, `main.py`, and `requirements.txt`; no 115, one-stop netdisk, MoviePilot, Yingchao, 302, transfer, media-organize, old RSS global config, Maoyan, or JavDB period UI residue remained.
- Browser checked `#dashboard`, `#manual`, `#custom`, and `#rss` with the new cache key:
  - Dashboard renders as the only route body and shows the 4 bottom entries: 主页、封面系统、工具系统、设置.
  - Manual cover renders as the only route body with `手动封面生成` left panel and `生成流程` note card.
  - Custom cover renders as the only route body with `封面素材设计`, `素材状态`, and `生成流程`.
  - RSS renders as the only route body with no global path card and no visible 日榜/周榜/月榜/总榜 wording.
- Browser also switched from dashboard to manual by hash navigation and confirmed there are no stuck `fade-*` classes and no old dashboard body left behind.

## 2026-06-02 UI Refinement Pass

- Removed decorative emoji labels from the cover badge selectors so manual/custom design controls read as clean product options: 不显示/无角标、缎带样式、徽章样式.
- Replaced the RSS task-card media-type emoji text with a styled `rss-type-pill` component using Font Awesome icons and scoped variants for movies, tvshows, and JavDB ranking tasks.
- Refreshed static cache keys to `alsemby-ui-refine-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Browser checked `#dashboard`, `#manual`, `#custom`, and `#rss`; each route rendered as a single active page body with no stuck fade classes, no old visible scope terms, and no old UI emoji labels in those views.
- Left notification-template emoji untouched because those are outbound message templates, not navigation or design-page chrome.

## 2026-06-02 Header Polish Pass

- Moved the top header action cluster, status chevron, task-log close/clear actions, empty states, progress text, stop icon, and log message truncation out of inline styles and into named CSS classes.
- Refreshed static cache keys to `alsemby-header-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Re-ran visible old-scope residue search across the app code; no 115, netdisk one-stop, MoviePilot, Yingchao, 302, old RSS global config, Maoyan, or JavDB period UI residue appeared.
- Browser checked `#dashboard`, `#manual`, `#custom`, `#rss`, and `#server`; header classes were present, each route rendered as a single active page body, there were no stuck fade classes, and no old visible scope terms appeared.

## 2026-06-02 Upload Control Refinement Pass

- Replaced remaining native `onclick="document.getElementById(...).click()"` upload triggers with Vue refs and a shared `triggerFileInput` helper.
- Applied the ref-driven upload flow to custom cover background upload, custom poster upload, direct cover upload, and font upload.
- Added reusable upload preview styling for local background/direct-cover previews.
- Refreshed static cache keys to `alsemby-upload-refine-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no upload `onclick` handlers remain and no old 115/netdisk/MoviePilot/Yingchao/302/RSS-global-config/JavDB-period UI scope terms reappeared.
- Browser checked `#custom`, `#fonts`, `#manual`, and `#rss`; visible routes rendered as a single active page body with no stuck fade classes and no visible old scope terms. The font upload entry remained visible; custom cover upload controls stay inside their collapsed material/upload sections until opened.

## 2026-06-02 RSS Layout Polish Pass

- Moved the RSS real-library page shell, toolbar, create form grids, alert headings, task-card actions, path rows, empty state, and usage block out of inline styles and into named CSS classes.
- Kept the user-owned Source/Destination wording intact and preserved the JavDB rule that output is `Destination / 订阅名称` with no visible 日榜/周榜/月榜/总榜 selector.
- Refreshed static cache keys to `alsemby-rss-layout-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no upload `onclick` handlers, old upload cache key, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared.
- Browser checked `#rss`: the RSS shell and toolbar render through the new classes, the collapsed page has one active route body, and the expanded create form exposes three `.rss-form-grid` sections with no visible JavDB period wording.
- Browser rechecked `#dashboard`, `#manual`, `#custom`, and `#rss`; no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Webhook Layout Polish Pass

- Moved the Webhook page shell, configuration card, enable switch wrapper, receive URL block, form grid, mode row, and save action row out of inline styles and into named CSS classes.
- Replaced the Webhook readonly URL inline input styling with a reusable `.readonly-input` class.
- Normalized the manual cover tip card margin with `.designer-tip-card` so the left designer panel continues matching the newer dark-card style.
- Refreshed static cache keys to `alsemby-webhook-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no upload `onclick` handlers, old RSS layout cache key, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared.
- Browser checked `#webhook`, `#manual`, `#rss`, and `#dashboard`; Webhook renders with the new shell/grid classes, manual keeps the designer tip card, and no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Settings Layout Polish Pass

- Moved the proxy and TMDB settings page shells, toolbars, heading icon colors, TMDB info card spacing, and account page shell/actions/header styling out of inline styles and into named CSS classes.
- Replaced the TMDB API link inline color with `.accent-link`.
- Reused `.settings-info-card` for TMDB/account tips and `.rss-alert-title` for account safety heading, keeping the settings pages visually consistent with RSS/Webhook polish.
- Refreshed static cache keys to `alsemby-settings-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no upload `onclick` handlers, old Webhook cache key, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared.
- Browser checked `#config_proxy`, `#config_tmdb`, `#account`, `#webhook`, and `#rss`; settings shells render through the new classes, each route has one active body, and no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Notification Layout Polish Pass

- Moved the notification settings shell, toolbar, Telegram card spacing, secret input rows, notification type sections, template panels, variable chips, action rows, and WeChat callback/form layout into named CSS classes.
- Replaced template-test inline accent button styles with `.accent-outline` and added reusable template textarea/code styling.
- Fixed the notification route title mapping so `#config_notification` now displays `通知配置` instead of falling back to `仪表盘`.
- Reworded Telegram proxy guidance from the removed `基本配置` wording to the current `代理配置` wording, including the backend Telegram connectivity message.
- Refreshed static cache keys to `alsemby-notification-title-fix-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no `基本配置` wording, upload `onclick` handlers, old settings cache key, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared.
- Browser checked `#config_notification`: the page title is `通知配置`, four notification sections and two type grids render through the new classes, no stale `基本配置` text appears, and no visible old scope terms appeared.

## 2026-06-02 Emby Settings Layout Polish Pass

- Moved the Emby settings page shell, toolbar, server action row, card action row, ID text, and info stack out of inline styles and into named CSS classes.
- Replaced the static `YOUR_NAS_IP` Webhook hint with the current local `webhookUrl` binding so the instruction matches the running ALSemby address without connecting to Emby.
- Reused `.rss-alert-title` and `.subtle-note` for Emby settings guidance cards.
- Refreshed static cache keys to `alsemby-emby-settings-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no `YOUR_NAS_IP`, upload `onclick` handlers, old notification cache key, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared.
- Browser checked `#server`, `#config_notification`, `#webhook`, and `#rss`; Emby settings render through the new shell/toolbar/info classes, the Webhook hint uses `/api/webhook`, and no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Auto Cover Layout Polish Pass

- Moved the automatic cover page shell, toolbar, create-card border, form grid, target section heading, media-library empty/load rows, task actions, task metadata, empty state, and usage block out of inline styles and into named CSS classes.
- Reused `.rss-alert-title`, `.accent-link`, `.strong-text`, and `.accent-text` for consistent help-card and metadata styling across cover/tool/settings pages.
- Reworded the automatic task note from automatic scanning to reading recent media items, keeping the UI calmer while preserving the cover-task behavior.
- Refreshed static cache keys to `alsemby-auto-cover-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no `YOUR_NAS_IP`, old cache keys, stale `基本配置` wording, upload `onclick` handlers, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared in source code.
- Browser checked `#auto`, `#manual`, `#custom`, `#server`, and `#rss`; the automatic cover page renders through the new shell/toolbar/usage classes, the create form expands with the new form/action classes, and no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Translation Config Layout Polish Pass

- Moved the translation config page shell, server selector row, translation list scroll area, translation row grid, add-row action, dashed full-width add button, and info card spacing out of inline styles and into named CSS classes.
- Reused `.rss-alert-title` for the translation matching note so the cover-system help cards stay visually aligned.
- Refreshed static cache keys to `alsemby-translations-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no old cache keys, `YOUR_NAS_IP`, stale `基本配置` wording, upload `onclick` handlers, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared in source code.
- Browser checked `#translations`, `#auto`, `#config_tmdb`, and `#rss`; the translation page renders through the new shell/server/list/add-row classes, no stuck `fade-*` classes or visible old scope terms appeared, and the Emby-reading `读取` action was not clicked.

## 2026-06-02 Font And Template Layout Polish Pass

- Moved the font and template management page containers, font upload action row, font/template help-card spacing, template group rows, template count chips, and template preview image sizing out of inline styles and into named CSS classes.
- Reused `.rss-alert-title` for font/template help cards so the cover-system admin pages match the rest of ALSemby.
- Renamed the `#fonts` page title mapping from `字体库` to `字体管理` to match the bottom navigation and page card title.
- Refreshed static cache keys to `alsemby-font-template-title-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no `YOUR_NAS_IP`, stale `基本配置` wording, upload `onclick` handlers, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared in source code.
- Browser checked `#fonts`, `#templates`, `#translations`, `#auto`, and `#rss`; font/template pages render through the new asset admin classes, `#fonts` now shows `字体管理`, and no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Cover Backup Layout Polish Pass

- Moved the cover backup page shell, snapshot action cards, control rows, suite list scroll area, suite metadata, empty state, library-card titles, info block, and suite-view toolbar/actions out of inline styles and into named CSS classes.
- Removed the automatic `fetchLibraryCovers()` call when entering `#library_preview`; cover backup now waits for the user to explicitly click `刷新`, preventing silent Emby contact during local UI review.
- Removed the automatic refresh on server-select change in the cover backup page for the same reason.
- Reused `.rss-alert-title` for the cover backup mechanism note.
- Refreshed static cache keys to `alsemby-cover-backup-polish-20260602`.
- `node --check static/app.js` passed.
- `.venv/bin/python -m compileall main.py app core` passed.
- `/static/index.html` returned HTTP `200`.
- Residue search confirmed no automatic `library_preview` fetch watcher, no `@change="fetchLibraryCovers"`, and no `YOUR_NAS_IP`, stale `基本配置` wording, upload `onclick` handlers, old RSS global config, 115/netdisk one-stop, MoviePilot, Yingchao, 302, Maoyan, or JavDB period UI scope terms reappeared in source code.
- Browser checked `#library_preview`, `#fonts`, and `#rss`; cover backup renders through the new backup classes, opening the page produced no `/api/library_covers` resource request, and no stuck `fade-*` classes or visible old scope terms appeared.

## 2026-06-02 Project Icon Generation Pass

- Generated a new original ALSemby project icon with the built-in imagegen tool, using layered media-card, play-triangle, and chain-link imagery in the current dark teal visual style.
- Saved the workspace-bound icon as `static/alsemby-icon.png` and resized it to `1024x1024`.
- Updated `static/index.html` and `static/login.html` favicon/apple-touch links to use `/static/alsemby-icon.png`.
- Left the old `static/favicon.png` untouched as a fallback asset.
- Verified `/static/alsemby-icon.png` returns HTTP `200 image/png`, `static/alsemby-icon.png` is a `1024x1024` PNG, and both `/static/index.html` and `/static/login.html` return HTTP `200`.

## 2026-06-02 Release Readiness Pass

- Added release packaging files: `Dockerfile`, `.dockerignore`, `docker-compose.example.yml`, and `README.md`.
- Extended `.gitignore` for local compose overrides and common tooling caches.
- Changed fallback login credentials to support `ALSEMBY_DEFAULT_USERNAME` and `ALSEMBY_DEFAULT_PASSWORD` environment overrides.
- Replaced remaining runtime `ChillPoster`/`Chill` branding residue in notification text, logger name, login footer, and template-test data with ALSemby.
- Hardened notification schema defaults with `Field(default_factory=...)` for dict fields.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Verified `/`, `/static/index.html`, `/static/login.html`, `/api/load`, `/api/templates_v2`, and `/api/layouts` returned expected HTTP responses.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Browser checked `#dashboard`, `#rss`, `#webhook`, `#server`, `#manual`, `#custom`, `#auto`, `#library_preview`, `#fonts`, `#templates`, `#translations`, `#config_notification`, `#config_proxy`, `#config_tmdb`, and `#account`; all rendered with the bottom dock, no visible old-scope entries, and no console errors.
- Release note: the directory is not currently a local Git repository, so upload/commit still needs `git init` or cloning the newly-created remote.

## 2026-06-02 External Review Triage Pass

- Read `/Users/aliaosha/Desktop/macmini/ALSemby_review.md` and triaged its release suggestions against the current code instead of applying them blindly.
- Accepted the low-risk release fixes: removed unused `websockets` dependency, localized Vue/Axios/Font Awesome assets under `static/vendor/`, moved tracked `docs/*.png` screenshots out of Git while keeping them locally, and added Douban API environment-variable overrides.
- Declined the high-churn suggestions for now: auth token expiration and splitting `static/app.js` into modules remain follow-up work, not release blockers for this local-first tool.
- Deleted `/Users/aliaosha/Desktop/macmini/ALSemby_review.md` after review, per user request.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Verified `/static/index.html`, `/static/login.html`, `/static/vendor/vue.global.prod.js`, `/static/vendor/axios.min.js`, `/static/vendor/fontawesome/css/all.min.css`, `/static/vendor/fontawesome/webfonts/fa-solid-900.woff2`, and `/static/alsemby-icon.png` all returned HTTP `200`.
- Residue search confirmed no external CDN references, `websockets`, ChillPoster, MoviePilot, Yingchao, netdisk one-stop, p115, or CloudDrive scope terms reappeared outside vendored assets and ignored docs images.
- Browser checked `/static/index.html` and `/static/login.html`; both use local vendor assets, expose no external CDN references in DOM, and showed no console errors.

## 2026-06-02 UI System Suggestion Triage Pass

- Read `/Users/aliaosha/Desktop/macmini/ALSemby_UI_improvements.md` and accepted its direction as a layered UI checklist, while avoiding a risky full mechanical rewrite of every hardcoded color in the 3000-line stylesheet.
- Expanded the root CSS token system with background, border, text, accent, radius, spacing, shadow, font, and transition variables while preserving the old ChillPoster-era variable aliases for compatibility.
- Added global polish for typography, selection, scrollbars, focus outlines, inputs, buttons, cards, empty states, help cards, and shared hover/active microinteractions.
- Refined the bottom dock toward the requested Chill-style four-group shell: smaller 600px dock, 66px visual height, icon/text vertical layout, active cyan indicator bar, and tighter mobile behavior.
- Updated the dashboard shortcut grid to a calmer 2-column layout on desktop and kept mobile responsive fallbacks.
- Refreshed static cache keys to `alsemby-ui-system-polish-20260602` for `style.css`, `app.js`, and the login stylesheet.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Verified `/static/index.html` and `/static/style.css?v=alsemby-ui-system-polish-20260602` returned HTTP `200`.
- Residue search confirmed no old cache key, netdisk one-stop, MoviePilot, Yingchao, 115 config, CloudDrive, or p115 scope terms reappeared in active source.
- Browser checked `#dashboard`, `#rss`, `#webhook`, `#server`, `#config_tmdb`, `#account`, and `#manual` through a fresh cache-busted URL; all loaded the new CSS, retained the bottom dock, showed no visible old-scope terms, and produced no console errors.

## 2026-06-02 React Bits Inspired Visual Pass

- Reviewed `DavidHDev/react-bits` and its official Vue port direction; decided not to add React or a new build chain, and instead translated the useful visual language into native CSS/Vue markup.
- Added a React Bits-inspired dashboard layer: animated aurora background, hero cover-card stack, glass engine chip, spotlight-card hover glow, and an animated media-wall empty-state cover ribbon.
- Strengthened the bottom dock glass surface with an inner highlight layer while preserving the existing four-group navigation behavior.
- Refreshed static cache keys to `alsemby-react-bits-visual-polish-20260602`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Verified `/static/index.html` and `/static/style.css?v=alsemby-react-bits-visual-polish-20260602` returned HTTP `200`.
- Residue search confirmed no old cache key, netdisk one-stop, MoviePilot, Yingchao, 115 config, CloudDrive, or p115 scope terms reappeared in active source.
- Browser checked `#dashboard`, `#manual`, `#custom`, `#rss`, `#webhook`, `#server`, and `#config_notification`; all loaded with the enhanced visual layer, retained header/dock visibility, showed no visible old-scope terms, and produced no console errors.

## 2026-06-02 Cover Workbench Polish Pass

- Reworked the manual cover and custom cover pages into a more complete cover workbench: stage header, status pills, ambient light layer, richer empty preview art, and unified action bar styling.
- Removed old inline action-bar divider and warning-button styles from the cover workbench templates in favor of reusable CSS classes.
- Enlarged and repositioned the preview canvas so the left control panel, canvas, and preview/apply actions read as one coherent editing surface instead of disconnected blocks.
- Refreshed static cache keys to `alsemby-cover-workbench-polish-20260602`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Residue search confirmed no old cache key, netdisk one-stop, MoviePilot, Yingchao, 115 config, CloudDrive, or p115 scope terms reappeared in active source.
- Browser checked `#manual`, `#custom`, `#rss`, and `#server`; the cover pages loaded the new workbench elements, retained header/dock visibility, and showed no visible old-scope terms.

## 2026-06-02 Static Background Pass

- Removed the decorative floating background animations from the dashboard and cover workbench after visual review.
- Removed now-unused keyframes for the aurora drift, hero-card float, empty-ribbon drift, designer orbit, and stage-card float effects.
- Refreshed static cache keys to `alsemby-static-background-polish-20260602`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Browser checked `#dashboard`, `#manual`, and `#custom`; the decorative background/card animation names now compute to `none`.

## 2026-06-02 Remove Color Card Decorations

- Removed the colorful decorative rectangle/card groups from the dashboard hero, dashboard empty media-wall state, manual cover preview empty state, and custom cover preview empty state.
- Removed the corresponding unused CSS selectors for hero poster cards, cover ribbons, stage cards, and their responsive rules.
- Refreshed static cache keys to `alsemby-remove-color-cards-20260602`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core` passed.
- Browser checked `#dashboard`, `#manual`, `#custom`, and `#auto`; no colorful decoration selectors remain in the active DOM.

## 2026-06-02 Product Shell Completion Pass

- Added unified intro/status panels to RSS real library, Webhook, automatic cover tasks, Emby config, notification config, proxy config, TMDB config, and account management.
- Kept RSS real-library paths subscription-scoped: users still fill Source and Destination per subscription, with output resolved as `Destination / subscription name`.
- Strengthened automatic cover task UI with selected-library counts, clearer empty state, stacked form fields, and no default cron value; users must fill the schedule themselves.
- Added a local Webhook event-record card that only reflects local backend log state and does not trigger real Webhook events.
- Removed the remaining dashboard aurora and cover workbench ambient layers from active markup/CSS so the previous colorful/floating visual residue cannot reappear.
- Cleaned stale title-map keys for old standalone notification pages.
- Refreshed static cache keys to `alsemby-product-polish-20260602`.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core` passed.
- Residue search confirmed no dashboard aurora, designer ambient, old cache key, colorful card selectors, old notification route keys, netdisk one-stop, MoviePilot, Yingchao, or 115 config terms remain in active source.
- Browser checked `#dashboard`, `#manual`, `#custom`, `#auto`, `#rss`, `#webhook`, `#server`, `#config_notification`, `#config_proxy`, `#config_tmdb`, and `#account`; all opened without console errors, horizontal overflow, or removed visual selectors.
- Safety note: this pass did not connect to Emby, did not scan NAS/CD2/media directories, and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Release Boundary Pass

- Added confirmation boundaries for local operation log clearing, backend log clearing, Emby connection tests, cover backup list refresh, cover snapshot creation, and Telegram/WeChat test notifications.
- Added hash-route aliases so intuitive URLs such as `#backup`, `#proxy`, and `#tmdb` resolve to the correct internal pages.
- Added `/api/health` for Docker healthcheck and local deployment checks; it only reports service availability and does not trigger business tasks.
- Expanded README deployment notes with persistent directories, media mount mapping rules, and explicit safety boundaries.
- Updated `docker-compose.example.yml` with optional Douban API environment variables and a healthcheck.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Residue search confirmed old 115/MoviePilot/Yingchao/netdisk-one-stop/CloudDrive scope terms did not reappear in active source.
- Restarted the local service with `.venv/bin/python main.py`, verified `http://localhost:5256/api/health` returned `{"status":"ok","app":"ALSemby"}`, and confirmed the browser dashboard still renders with the bottom dock.

## 2026-06-02 v0.1.0-beta.1 Release Prep

- Promoted the project to `v0.1.0-beta.1` for the first local/NAS deployment test release.
- Unified version metadata across FastAPI, health response, frontend display, static cache keys, Dockerfile, and compose example.
- Added `docs/CHANGELOG.md` with included scope, safety notes, and verification checklist.
- Updated README with current test-release version and beta publish notes.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed with image/env version `0.1.0-beta.1`.
- Verified `http://localhost:5256/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.1.0-beta.1"}`.
- Browser checked the cache-busted dashboard and confirmed the frontend displays `ALSemby v0.1.0-beta.1` with the expected static asset cache keys.
- Built local Docker image `alsemby:v0.1.0-beta.1` successfully. Current image includes both runtime and default font/template resources so mounted empty volumes can self-restore; image slimming can be handled in a later release pass.
- Aligned Docker Hub publishing with the `madou-next` pattern: multi-arch `linux/amd64,linux/arm64` image tags will be `aliaosha2521/alsemby:v0.1.0-beta.1` and `aliaosha2521/alsemby:latest`.
- Updated the compose example to pull from Docker Hub directly instead of requiring a local build.
- Pushed Docker Hub images `aliaosha2521/alsemby:v0.1.0-beta.1` and `aliaosha2521/alsemby:latest`; both tags resolve to manifest digest `sha256:01d05091e515a3f00ff9d4e04a37bfbd1d5cd25498a0ad2b3e48a3d5b92f3ef6`.
- Verified the pushed manifest includes `linux/amd64` and `linux/arm64`.
- Safety note: this release prep did not connect to Emby, did not scan NAS/CD2/media directories, and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Local Branding And Proxy Scope Fix

- Updated the login page branding from the old `Poster Pro` copy to `ALSemby`, using the project icon at `/static/alsemby-icon.png`.
- Reworded the proxy settings page as an external-service proxy only: TMDb, Douban, Telegram and similar outbound HTTP calls; it does not affect Emby, local media paths, RSS hard links, or other network requests.
- Replaced the Telegram proxy note and generic save toast so the UI no longer presents this setting as a system/global proxy.
- Renamed related backend comments/log wording from generic proxy/global wording to external-service/core-configuration wording without changing runtime behavior.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core config_manager.py constants.py` passed.
- Verified local HTML served by `http://localhost:5256/static/login.html` contains `ALSemby` and no old login brand copy.
- Verified local HTML served by `http://localhost:5256/static/index.html` contains the new external-service proxy scope text and no misleading global-proxy copy in active source.
- Safety note: this local fix did not republish DockerHub images, did not connect to Emby, did not scan NAS/CD2/media directories, and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Dashboard Refresh And Cover Apply Feedback Fix

- Split media-library loading from the explicit Emby connection test, so page refresh no longer triggers the `测试 Emby 连接` confirmation dialog.
- Removed automatic `fetchLibs(0)` calls from startup and local fallback loading; dashboard cover loading may still refresh its own preview data, but it no longer opens a confirmation modal.
- Kept the settings-page `测试连接` button protected by confirmation.
- Added clear guardrails for manual/custom cover apply: missing media library and missing preview image now show immediate toast messages.
- Added loading text and spinner state to the manual/custom `预览` and `应用` buttons so a real apply request no longer looks like no response.
- Added API error-detail propagation for preview/apply/library-read failures, making backend errors visible in the UI toast.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core config_manager.py constants.py` passed.
- Residue search confirmed the old `fetchLibs(0)` startup trigger and `fetchLibs -> testConnection` alias are gone.
- Safety note: this pass did not republish DockerHub images, did not connect to Emby, did not scan NAS/CD2/media directories, and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Emby 401 Diagnostics

- Confirmed the locally saved Emby API key is present and not being cleared or masked by the frontend before connection testing.
- Changed `/api/connect` to validate Emby by media-library read access instead of `System/Info`, because the latter can reject valid library-capable keys with 401.
- Added structured Emby connection diagnostics so `/api/connect` now returns clear 401/403/network failure details instead of a generic `Fail`.
- Updated the translation-library import toast to display backend error detail when Emby rejects a connection.
- Verified real Emby upload with an unchanged existing library cover: both binary and base64 upload paths returned 204.
- Fixed the manual cover page footer buttons, which were incorrectly bound to the custom-design preview/apply handlers.
- Added manual cover guards for missing media library and missing preview image, plus backend error-detail toasts for manual preview/apply failures.
- Updated the `app.js` cache key in `index.html` so browsers load the corrected manual apply handler.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core config_manager.py constants.py` passed.
- Safety note: this pass touched Emby only to verify connection and re-upload the same existing library cover; it did not scan NAS/CD2/media directories and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Emby 401 Log Follow-Up

- Confirmed the visible `System/Info` 401 was an old `config/app.log` entry from 21:53:08, not a fresh request from the current code.
- Restarted the local ALSemby server with the project virtual environment inside a detached `screen` session: `alsemby-local`.
- Verified `http://localhost:5256/api/health` returns ok after restart.
- Verified `/api/connect` returns 200 and reads the Emby media-library list through the current backend.
- Confirmed no new `System/Info` 401 entries appeared after the 22:38 restart; current connection validation uses `Library/VirtualFolders`.
- Cleared old system logs through `/api/clear_system_logs` so the UI no longer replays stale 401 records.
- Safety note: this pass touched Emby only through the connection/library-list check; it did not scan NAS/CD2/media directories and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Cover Apply Runtime Fix

- Removed the final confirmation modal from manual/custom cover apply so clicking `应用` immediately enters an applying state and sends the upload request.
- Added immediate frontend feedback for cover apply: `正在应用封面...` toast plus manual-page operation log entry before the request starts.
- Added backend cover-apply logs for start, frontend image parse failure, upload success, and upload failure so the system log is no longer silent during cover upload.
- Updated the `app.js` cache key in `index.html` so browsers load the latest cover-apply handler.
- Found that port `5256` was still held by an old Python process, so frontend updates were being served while backend logging changes were not loaded.
- Replaced the stale local process with a fresh `screen` session process and verified `http://localhost:5256/api/health` returns ok from PID `51527`.
- Verified `/api/apply` directly by re-uploading the existing `豆瓣TOP250` library cover; the request returned 200 and system logs recorded both `[Cover] 开始应用媒体库封面` and `[Cover] 媒体库封面应用成功`.
- Verified `node --check static/app.js` passed.
- Verified `python -m compileall main.py app core config_manager.py constants.py` passed.
- Safety note: this pass touched Emby only to re-upload the same existing library cover for apply verification; it did not scan NAS/CD2/media directories and did not run real RSS/Webhook/media tasks.

## 2026-06-02 Media Library Cover Apply Verification Fix

- Re-read the extracted early Chill Poster source for cover apply and confirmed its `upload_cover` path directly posts to `/emby/Items/{id}/Images/Primary` and treats HTTP 200/204 as success.
- Diagnosed the ALSemby manual-cover false-success bug against the real Emby media-library object: CollectionFolder uploads can return 204 while the library cover tag/hash remains unchanged.
- Updated `EmbyClient.upload_cover` to record the current Primary image tag/hash before upload, verify the image changed after upload, and reject false-success 204 responses.
- Added a CollectionFolder-specific URL pull upload path through `/emby/Items/{id}/Images/Primary/0/Url`, with `/api/apply` publishing the generated cover through a temporary ALSemby static URL that Emby can fetch.
- Added `static/tmp/` to `.gitignore` so runtime-published temporary cover files are never committed.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall main.py app core config_manager.py constants.py` passed.
- Restarted the local service in `screen` session `alsemby-local` and verified `http://localhost:5256/api/health` returns ok.
- Verified `/api/apply` against the JAV media library: the request returned 200 and the Emby Primary image tag/hash changed, confirming the cover was actually applied instead of only returning a fake success.
- Safety note: this pass touched Emby only through media-library cover read/write verification; it did not scan NAS/CD2/media directories and did not run RSS/Webhook/media tasks.

## 2026-06-02 Auto And Webhook Cover Upload Parity Fix

- Audited every `upload_cover` caller and confirmed manual cover, cover restore, automatic cover tasks, saved task runs, scheduled tasks, and Webhook-triggered tasks now share the same verified media-library upload behavior.
- Added `core/cover_publish.py` to publish generated covers under `/static/tmp/covers/` and build an Emby-reachable temporary URL from the request base URL, saved task base URL, or LAN fallback.
- Updated automatic cover task execution to pass that temporary image URL into `EmbyClient.upload_cover`, so CollectionFolder covers use Emby's URL-pull upload path and are verified by Primary tag/hash change.
- Updated Webhook targets and debounced Webhook task scheduling to carry the current ALSemby public base URL into the same task execution path.
- Updated cover backup restore to use the same temporary URL and verified upload path, preventing false restore success on media-library folders.
- Confirmed all active cover-write entrypoints pass `image_url` to `upload_cover`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core config_manager.py constants.py` passed.
- Restarted the local service in `screen` session `alsemby-local` and verified `http://localhost:5256/api/health` returns ok.
- Safety note: this pass did not run automatic cover tasks, RSS tasks, Webhook events, or NAS/CD2/media scans; it only performed local code checks and static temporary URL publication checks.

## 2026-06-03 Restore Chill-Style Cover Upload For Beta Packaging

- Reverted the media-library cover upload path back to the early Chill Poster method: direct binary upload first, Base64 upload second, then real-ID fallback when needed.
- Removed the temporary static cover URL publishing path from manual cover apply, backup restore, automatic cover tasks, scheduled tasks, saved task runs, and Webhook-triggered tasks.
- Deleted the temporary cover publisher module and removed the `static/tmp/` ignore rule because the release no longer creates ALSemby-hosted temporary cover files.
- Removed the Primary tag/hash verification helper code so `upload_cover` once again treats Emby HTTP 200/204 responses as success, matching Chill's practical behavior.
- Confirmed no active business code references `cover_publish`, `write_temp_cover_url`, `alsemby_public_base_url`, static temporary cover paths, or Primary image-change verification.
- Removed Dockerfile-level app name/version environment defaults so the release image does not expose extra version env configuration.
- Removed default username/password environment override support; first-run credentials are now directly built in as `admin` / `password` until changed from the account page.
- Corrected the changelog compose description to match the current persistent volumes, media path mounts, and healthcheck example.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core config_manager.py constants.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Residue search confirmed no active references to removed temporary cover publishing or default credential/version environment variables.
- Safety note: this pass did not run automatic cover tasks, RSS tasks, Webhook events, Emby writes, or NAS/CD2/media scans; it only changed local code and performed static checks.

## 2026-06-03 v0.1.0-beta.2 DockerHub Release

- Published `aliaosha2521/alsemby:v0.1.0-beta.2` and `aliaosha2521/alsemby:latest` to DockerHub.
- Verified both tags point to manifest digest `sha256:7a357c0437c40fe450dfbdb3cb6d2c2f82321e5d45764866b270ab1d831c68d9`.
- Verified the release image includes `linux/amd64` and `linux/arm64` manifests.
- Release notes: this build keeps the Chill-style direct Emby cover upload path after confirming the failed cover update was caused by an Emby-side plugin setting.
- Safety note: this release build did not run RSS tasks, Webhook events, media scans, or NAS/CD2 scans; it only performed local build checks and DockerHub publish.

## 2026-06-03 Bottom Navigation Visual Fix

- Reduced the bottom navigation from a heavy black footer block to a compact floating frosted dock.
- Removed visible background and shadow from the navigation shell so only the dock itself is visible.
- Reduced bottom content padding from the oversized release layout to a smaller floating-navigation reserve.
- Updated the stylesheet cache key to `alsemby-v0.1.0-beta.2-nav-glass` so browsers load the corrected navigation CSS.
- Verified the local RSS and manual-cover pages in the in-app browser; the dock now renders as a narrow floating control instead of a wide black content-covering block.
- Safety note: this pass only changed frontend CSS/static cache wiring and did not run RSS tasks, Webhook events, media scans, Emby writes, or NAS/CD2 scans.

## 2026-06-03 Sleep Handoff Notes

- Current ALSemby scope is intentionally paused after the `v0.1.0-beta.2` test build and bottom-navigation visual cleanup.
- Core completed scope: media-library cover system and RSS/JavDB real-library workflows are working in local/NAS user testing; Webhook remains the only untested major path but shares the same cover-task pipeline.
- User preference for the next release: likely formal `0.1.0` style versioning, but confirm tag format against madou-next before publishing.
- Keep current Docker compose guidance minimal and general-purpose: `./config:/app/config`, user-mounted Emby media paths for `/strm`, `/strm1`, `/strm2`, and healthcheck as optional.
- Do not publish another image until the user explicitly asks; current beta should stay available for continued testing.
- Safety note: this handoff only updated documentation and memory notes. It did not run RSS tasks, Webhook events, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 Webhook Enable Persistence Fix

- Compared ALSemby Webhook config flow with the extracted Chill source and confirmed the backend config endpoint already persists `enabled`, `engine`, `preset`, and `mode` correctly.
- Fixed the Webhook page switch by exposing `toggleWebhookStatus` to the Vue template return object; before this, the visual switch could move without updating the reactive config saved by the page.
- Hardened Webhook config save/toggle calls to send a plain payload and immediately reload `/api/webhook/config` after saving, keeping the top status card, switch, and persisted JSON in sync.
- Updated the frontend cache key to `alsemby-webhook-persist-20260603`.
- Verified `node --check static/app.js` passed.
- Verified the local API persistence loop: POST enabled true -> GET true, POST enabled false -> GET false.
- Browser-verified the local Webhook page: after enabling and saving, the page showed `ON`; after reload, the switch and status still showed `ON`.
- Safety note: this pass did not trigger real Webhook events, RSS tasks, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 v0.1.0 Stable DockerHub Release

- Promoted ALSemby from `v0.1.0-beta.2` to stable `v0.1.0`.
- Updated UI version badge, backend `/api/health` version, static cache keys, README, and changelog.
- Rechecked the Webhook config persistence fix before release.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core config_manager.py constants.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Restarted the local `alsemby-local` service and verified `/api/health` returns `{"version":"0.1.0"}`.
- Published DockerHub tags `aliaosha2521/alsemby:v0.1.0` and `aliaosha2521/alsemby:latest`.
- Verified both tags point to manifest digest `sha256:27255a25158416f0eed1bc6948541637a198bc48d20a369aa0da08ef1e814926`.
- Verified the release image includes `linux/amd64` and `linux/arm64` manifests.
- Safety note: this release did not trigger real Webhook events, RSS tasks, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 Bottom Navigation Frame Rollback

- Reverted the attempted `bottom-frame-fix` CSS because it changed the exposed bottom color but did not solve the actual content-covering problem.
- Restored static cache keys from `alsemby-v0.1.0-bottom-frame-fix` back to `alsemby-v0.1.0`.
- Next diagnosis should focus on layout height, scroll container sizing, and fixed dock overlap instead of recoloring the bottom background.
- Safety note: this rollback only changed frontend CSS/static cache wiring and documentation; it did not trigger real Webhook events, RSS tasks, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 Floating Dock Boundary Fix

- Reworked the bottom navigation as a true bounded floating dock instead of relying on a full-page reserved bottom band.
- Removed global `content-area` bottom reservation and moved safe bottom padding to normal `.scroll-view` pages only.
- Reduced manual/custom designer bottom padding from the oversized full-width reserve to a local layout-safe margin.
- Forced `.bottom-shell` to fit its own content, stay transparent, and avoid creating a full-width visual or hit-test layer.
- Updated static cache keys to `alsemby-v0.1.0-floating-dock-boundary`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core config_manager.py constants.py` passed.
- Safety note: this pass only changed frontend CSS/static cache wiring and documentation; it did not trigger real Webhook events, RSS tasks, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 v0.1.1 Stable Patch Release Prep

- Promoted the current confirmed local/NAS stable state from `v0.1.0` to `v0.1.1`.
- Included the Webhook enable persistence fix and the floating dock boundary fix in the stable patch release.
- Updated backend `/api/health` version, frontend version badge, static cache keys, README, and changelog.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall main.py app core config_manager.py constants.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Planned DockerHub tags: `aliaosha2521/alsemby:v0.1.1` and `aliaosha2521/alsemby:latest`.
- Next feature track after publishing: start `v0.2.0` research with Emby health/diagnostics and log-center style tools as the leading candidates.
- Safety note: this release-prep pass did not trigger real Webhook events, RSS tasks, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 v0.1.1 Stable DockerHub Release

- Published `aliaosha2521/alsemby:v0.1.1` and `aliaosha2521/alsemby:latest` to DockerHub.
- Verified both tags point to manifest digest `sha256:653ecea57692355787919b7ff39c2e45049490d8cbef6210ca9ee736c73131e8`.
- Verified the release image includes `linux/amd64` and `linux/arm64` manifests.
- Temporarily started the local ALSemby service on port `5256` and verified `/api/health` returns `{"version":"0.1.1"}` plus the `v0.1.1` static asset cache keys.
- Release notes: this patch preserves the validated cover/RSS/Webhook behavior and adds the confirmed floating dock boundary fix.
- Safety note: this release did not trigger real Webhook events, RSS tasks, Emby writes, media scans, NAS writes, or CD2 scans.

## 2026-06-03 v0.2.0 Step 1 Baseline

- Created local development branch `feature/v0.2.0` from the stable `v0.1.1` tag.
- Confirmed active source scope remains focused: cover system, RSS/Webhook tools, and Emby/notification/proxy/TMDB/account settings.
- Checked for old active-scope residue such as 115, MoviePilot, shadow media tools, and cloud-drive workflows; no active source hits were found outside historical docs/vendor noise.
- Added `docs/v0.2.0-plan.md` to pin the next cycle around read-only diagnostics, local log visibility, config assistance, and Webhook helper improvements.
- Cleaned safe local cache artifacts from the project source tree.
- Fixed a harmless but noisy Python regex escape warning in `core/meta/string.py` without changing behavior.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 2 Diagnostics Helper

- Added a new read-only `诊断助手` tool page as the first v0.2.0 feature slice.
- Added `/api/diagnostics/summary` to summarize local configuration health, RSS/Webhook state, and local asset counts without exposing API keys.
- Added `/api/diagnostics/emby_readonly` as an explicit button-only Emby read check; it reads connection/library metadata only and does not upload covers, scan directories, or run tasks.
- Added the diagnostics entry to the dashboard quick actions and the tool-system popover.
- Adjusted frontend startup so the dashboard poster wall initializes only on the dashboard route, keeping direct diagnostics entry local-only by default.
- Added a narrow-screen breakpoint so the diagnostics cards collapse cleanly to one column.
- Browser-verified direct navigation to `#diagnostics`: configuration checks, local resources, and the Emby read-only boundary render automatically.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Safety note: this pass did not click the Emby read-only check, package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 3 Log Center

- Added a new read-only `日志中心` tool page as the second v0.2.0 tool card.
- Added `/api/logs/summary` to read `config/app.log`, redact obvious secrets, and summarize logs by category and level.
- Added filters for system, cover, RSS, Webhook, notification, Emby, and other log categories.
- Added the log center entry to the dashboard quick actions and the tool-system popover.
- Browser-verified direct navigation to `#logs`: the log intro, filters, overview cards, and recent log list render correctly with no console errors.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Restarted the local service on port `5256` and verified `/api/health` plus `/api/logs/summary`.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 4 Config Assistant

- Added a new read-only `配置助手` tool page as the third v0.2.0 tool card.
- Added `/api/config_assistant/summary` to inspect local settings, RSS tasks, auto-cover tasks, Webhook config, notification config, templates, fonts, and layouts.
- The config assistant groups checks by Emby, external metadata, RSS real library, cover resources, Webhook, and notifications, with severity labels and direct jumps to the relevant local page.
- The API response only returns safe status facts such as `has_key` and file sizes; it does not return API keys, passwords, cookies, or tokens.
- Added the config assistant entry to the dashboard quick actions and the tool-system popover.
- Browser-verified direct navigation to `#config_assistant`: the intro, score panel, grouped checks, jump buttons, and local file status render correctly.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Restarted the local service on port `5256` and verified `/api/health` plus `/api/config_assistant/summary`.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 5 Webhook Debug Helper

- Added a read-only Webhook debug helper API with `/api/webhook/debug/summary` and `/api/webhook/debug/parse`.
- The summary shows Webhook enablement, template, layout, capture mode, template file existence, Emby config completeness, recommended Emby events, safe server summaries, recent Webhook logs, and recent task logs.
- The Payload preview only parses pasted JSON and returns `Event`, `Library Name`, and `Item Name`; it does not call the real Webhook handler, generate covers, run tasks, or write Emby.
- Reworked the Webhook page so local debug checks, recommended events, payload preview, Webhook logs, and task logs are shown separately instead of borrowing the task log list as a fake event feed.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `/api/health`, `/api/webhook/debug/summary`, and `/api/webhook/debug/parse` locally.
- Browser-verified direct navigation to `#webhook`: the debug cards render, and the sample Payload preview displays Event, Library Name, and Item Name.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 6 Tools Overview

- Added a read-only `工具系统` overview page as the top-level tools landing view.
- Added `/api/tools/summary` to aggregate RSS, Webhook debug, diagnostics, logs, and config assistant status into five local tool cards.
- Changed the bottom `工具系统` navigation entry to open the overview page directly instead of a small popover menu.
- Added dashboard access to the tools overview so the new v0.2.0 tool cards are discoverable from the home page.
- Added responsive styling so the tools cards collapse from two columns to one column on narrow screens.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Restarted the local service on port `5256` and verified `/api/health` plus `/api/tools/summary`.
- Browser-verified direct navigation to `#tools`: five tool cards render, the bottom nav highlights `工具系统`, and `#webhook` still renders the Webhook debug helper.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 7 Diagnostics and Logs Polish

- Enhanced `/api/diagnostics/summary` with local file status, local resource status, and next-step recommendations.
- The diagnostics helper now surfaces core config, RSS task config, auto-cover task config, Webhook config, app log, font/template/layout/backup resources, and safe recommendations.
- Enhanced `/api/logs/summary` with repeated WARNING/ERROR hotspots and the latest issue marker.
- The log center now shows a `问题热区` panel so repeated failures are easier to spot before reading the full log stream.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Restarted the local service on port `5256` and verified `/api/diagnostics/summary` plus `/api/logs/summary`.
- Browser-verified direct navigation to `#diagnostics` and `#logs`: the new diagnostics insight cards and log hotspots render correctly.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 8 Local Dev Wrap

- Updated the local development version marker to `0.2.0-dev` in the FastAPI health response and frontend badge.
- Kept README, changelog, and compose examples on the current stable `v0.1.1` release wording because `v0.2.0` has not been packaged or published.
- Updated `docs/v0.2.0-plan.md` with the completed local tool set and the remaining release/deferred boundaries.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Restarted the local service on port `5256` and verified `/api/health` returns `{"version":"0.2.0-dev"}`.
- Browser-verified direct navigation to `#tools`: the page badge displays `ALSemby v0.2.0-dev` and the tools overview renders.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 9 Diagnostics and Logs Completion

- Enhanced diagnostics with Cron expression validation for RSS and automatic cover tasks.
- Enhanced diagnostics with automatic cover task relationship checks for template, Cron, target library, and target Emby config completeness.
- Adjusted empty RSS/automatic-cover states to `info` instead of warning when no task exists.
- Added log center time-range filtering with an all-log view and a recent-24-hours view.
- Added common error explanations for Emby 401, cover upload anomalies, missing templates, and Cron problems.
- Added expandable log-entry details showing the raw line, parsed category, and parsed level.
- Verified `/api/diagnostics/summary`, `/api/logs/summary?hours=24`, and `/api/logs/summary?hours=0` locally.
- Browser-verified `#diagnostics` shows the Cron and automatic-cover checks, and `#logs` shows the time-range filter plus detail controls.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 10 Release Checklist Draft

- Added `docs/v0.2.0-release-checklist.md` to separate local readiness from actual Docker release work.
- Recorded the current state as `0.2.0-dev`, with stable published wording still on `v0.1.1`.
- Marked `npm run build` as not applicable because the project has no `package.json` and the frontend is plain static HTML/CSS/JS served by FastAPI.
- Listed release-time-only edits: version promotion, README, changelog, static cache keys, Docker build, and Docker push.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 11 Scope Residue Scan

- Scanned active frontend/backend files for removed module wording such as 115, MoviePilot, shadow-nest, one-stop cloud-drive flows, pan115, p115, and old transfer routes.
- Confirmed those old scopes are not exposed by the active UI or backend route code.
- Remaining matches are limited to `docs/v0.2.0-plan.md` safety exclusions and unrelated local variable/icon names.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 12 Release Candidate Prep

- Promoted FastAPI and frontend display version markers from `0.2.0-dev` to `0.2.0`.
- Refreshed static asset cache keys to `alsemby-v0.2.0`.
- Added a minimal `npm run build` script that performs the release frontend syntax check with `node --check static/app.js`.
- Updated README, changelog, compose comments, the v0.2.0 plan, and release checklist for the prepared release candidate state.
- Release boundary: Docker packaging and DockerHub push are still intentionally deferred until the user explicitly asks.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 13 Release Gate Fixes

- Fixed `/api/tools/summary` 500 errors caused by direct internal reuse of the log summary route with FastAPI `Query` defaults.
- Hardened `/api/webhook/debug/parse` so the local preview accepts both frontend `payload_text` requests and raw JSON Payload objects.
- Verified Payload parsing preview returns only `Event`, `Library Name`, and `Item Name`, with the explicit no-task/no-cover/no-processing note.
- Verified `/api/tools/summary`, `/api/diagnostics/summary`, `/api/webhook/debug/summary`, `/api/webhook/debug/parse`, `/api/logs/summary`, `/api/config_assistant/summary`, and `/api/health` all return HTTP 200 locally.
- Browser-smoked `#dashboard`, `#tools`, `#webhook`, `#diagnostics`, `#logs`, `#config_assistant`, `#manual`, `#auto`, `#server`, and `#settings`; each route showed `ALSemby v0.2.0` with no console errors.
- Confirmed the bottom navigation is a compact fixed `bottom-shell` dock and no oversized bottom block is detected on the checked routes.
- Verified `node --check static/app.js`, `npm run build`, Python compile checks, `docker compose -f docker-compose.example.yml config`, and `git diff --check` passed.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 14 Tool and Log Navigation Rework

- Split the log center out of the tool scope and added a dedicated bottom navigation entry for `日志`.
- Changed the bottom `工具系统` button back to a floating chooser instead of routing straight into the large tools overview page.
- Kept the tool chooser focused on the two practical tools, `RSS 真实库` and `Webhook`, with diagnostics and configuration checks demoted to auxiliary entries.
- Reworked the top-right realtime log button into a NanShare-style categorized log modal backed by `/api/logs/summary`.
- Added realtime log category tabs for all/system/cover/RSS/Webhook/notification/Emby/other and synchronized empty, loading, and clear states.
- Added compact styling for the revised tool drawer and realtime log modal.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Browser-verified the bottom `工具系统` opens the chooser without changing the URL, the bottom `日志` entry opens `#logs`, and the top-right realtime log modal switches to the Webhook category with no console errors.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 15 Webhook Page Polish

- Fixed Webhook debug card headers where the eyebrow/title text could visually overlap.
- Replaced developer-facing `Readonly` and `Emby Events` labels with localized, quieter labels.
- Changed the Payload local parser from an always-open large debug panel into a collapsed advanced-debug card.
- Clarified the Payload parser purpose: it only parses Emby Webhook JSON fields and does not execute tasks, generate covers, or write Emby.
- Verified `node --check static/app.js` passed.
- Verified `python3 -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Browser-verified the Webhook page no longer shows the English debug labels, the Payload textarea is hidden by default, and expanding the advanced-debug card still exposes the example and parse controls with no console errors.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 16 Claude Review Triage

- Reviewed `CLAUDE_REVIEW.md` and accepted the data-safety finding around RSS task deletion.
- Fixed RSS task deletion so deleting only the subscription no longer attempts to delete the matching Emby library; Emby library deletion and linked-file deletion now only run when `delete_files` is explicitly true.
- Added the missing `[v-cloak]` CSS rule to prevent Vue template flash during startup.
- Invalidated the `config_manager` settings cache after `/api/save` writes, keeping TMDB/proxy reads consistent immediately after saving settings.
- Adjusted the dashboard stats label from `自动任务` to `定时任务` because the count includes both automatic-cover and RSS schedules.
- Changed the dashboard `工具系统` command card to open the bottom tool drawer instead of navigating to the transitional `#tools` compatibility page.
- Rejected/deferred the lower-risk review items for now: ACTIVE_TASKS locking, CSS/JS splitting, compose media mount comment changes, fetchFonts refactor, and broad EmbyClient context-manager cleanup.
- Verified `node --check static/app.js`, Python compile checks, `docker compose -f docker-compose.example.yml config`, and `git diff --check` passed.
- Browser-verified the dashboard shows `定时任务`, the dashboard tool card opens the bottom tool drawer without leaving the dashboard route, and no console errors were reported.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 17 Emby Tool Interfaces

- Added three practical tool entries for the v0.2.0 line: `媒体库维护`, `Emby 任务`, and `合集检查`.
- Added read-only backend endpoints for media search, scheduled task listing, and collection summaries under `/api/emby_tools/*`.
- Added frontend workbench pages for the three tools with explicit user-triggered buttons; no page load automatically starts Emby reads.
- Updated the bottom `工具系统` drawer and `/api/tools/summary` compatibility data so the new tools appear before RSS/Webhook and the auxiliary diagnostics/config entries.
- Restarted the local service with `.venv/bin/python main.py` after confirming the default system Python was missing project dependencies.
- Verified `curl http://localhost:5256/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Verified `/api/tools/summary` now returns cards for `media_maintenance`, `emby_tasks`, and `collections`.
- Verified `node --check static/app.js`, `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py`, and `git diff --check` passed.
- Browser-verified `#media_maintenance`, `#emby_tasks`, `#collections`, and the bottom tool drawer render the new interfaces with no visible error toast.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 18 Emby Tool Functional Pass

- Expanded `媒体库维护` from a read-only shell into a practical maintenance workbench with result summaries, issue aggregation, CSV export, path copy, Emby item jump, and single-item metadata refresh.
- Added `/api/emby_tools/media/refresh` for explicitly confirmed single-item Emby metadata refresh requests; no batch refresh path was added.
- Improved media search results with scanned counts, issue summaries, size/resolution metadata, and Emby web URLs.
- Expanded `Emby 任务中心` with confirmed single-task run and stop actions through `/api/emby_tools/tasks/run` and `/api/emby_tools/tasks/stop`.
- Expanded `合集检查器` with collection-specific issue tags, empty-collection counts, Emby jump links, member inspection, and single-collection refresh.
- Added `/api/emby_tools/collections/items` to inspect one collection's members on demand.
- Restarted the local service with `.venv/bin/python main.py` and verified `/api/health` returned `ALSemby` version `0.2.0`.
- Verified new action routes are registered by confirming empty POST requests return validation errors instead of 404.
- Verified `node --check static/app.js`, `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py`, and `git diff --check` passed.
- Browser-smoked `#media_maintenance`, `#emby_tasks`, and `#collections`; all pages rendered the expected controls with no visible error toast.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, scan NAS/CD2, or scan media directories. Browser checks did not click Emby read/run/refresh buttons.

## 2026-06-04 v0.2.0 Step 19 Emby Task Grouping Polish

- Reworked `Emby 任务中心` from a flat task list into Emby-like grouped sections.
- Added backend task category detection and ordering, with `神医助手` tasks separated from Library/Application/Database/Downloads and other groups.
- Added task progress display support from Emby `CurrentProgressPercentage` when available.
- Renamed `媒体库维护` to `元数据体检` and clarified it is an auxiliary issue-finding tool, not a replacement for Emby metadata management.
- Renamed `合集检查器` to `合集体检` and clarified it is a low-frequency collection metadata check tool.
- Updated bottom tool drawer labels and the corresponding page titles/descriptions to match the new positioning.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#emby_tasks`, `#media_maintenance`, and `#collections` loaded `alsemby-apple-20260605ac`, had no horizontal overflow, showed no visible errors, and kept their expected preflight/problem-map copy.
- Browser-verified the same three routes at 390px width: no horizontal overflow and the shared preflight/blueprint components remain readable.
- Safety note: browser checks only navigated local pages; they did not click `读取任务列表`, `开始检索`, `读取合集`, refresh controls, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.
- Restarted the local service with `.venv/bin/python main.py` and verified `/api/health` returned `ALSemby` version `0.2.0`.
- Browser-smoked `#emby_tasks`, `#media_maintenance`, `#collections`, and the bottom tool drawer without clicking Emby read/run/refresh actions.
- Safety note: this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-04 v0.2.0 Step 20 Tool Usability Polish

- Updated remaining tool entry copy so old `媒体库维护` and `合集检查器` labels no longer appear in the active UI.
- Added purpose chips to `元数据体检` and `合集体检` so their output and boundaries are clear: issue list/CSV/single-item refresh and collection member/empty collection/single-collection refresh.
- Added Emby scheduled-task category filters to the task center UI; after reading tasks, users can focus on `全部`, `神医助手`, Library, Application, and other returned groups.
- Added backend scheduled-task trigger summaries, translating common Emby triggers into readable text such as daily, weekly, interval, startup, or manual run.
- Added frontend task-row schedule metadata so task timing and last execution result are visible together.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Restarted the local service in the background and verified `/api/health` returned `ALSemby` version `0.2.0`.
- Browser-smoked `#media_maintenance`, `#emby_tasks`, `#collections`, and the compatibility `#tools` route with cache busting; no visible error toast, exceptions, or old active UI labels were found.
- Safety note: browser checks did not click Emby read/run/refresh controls; this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, scan NAS/CD2, or scan media directories.

## 2026-06-05 v0.2.0 Step 21 Apple-Style UI Foundation

- Added an Apple-inspired product design override layer in `static/style.css`.
- Unified final UI tokens around graphite surfaces, Apple-blue accent, restrained blur, 8px card radius, and clearer system font hierarchy.
- Unified global card, button, form, toast, confirmation modal, empty-state, and info/error hint styling across the admin pages.
- Refined the manual/custom cover studio into a cleaner inspector-and-canvas workspace with quieter panels, tighter controls, and a floating action bar.
- Unified page shells and card density for dashboard, RSS, Webhook, settings, logs, and tool workbench pages.
- Added a small workspace-height refinement so the cover studio no longer relies on the old full-height page stretch.
- Figma connector was not logged in during this pass, so the product-design changes were implemented directly in code rather than synced to a Figma canvas.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `npm run build` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-smoked `#dashboard`, `#manual`, `#webhook`, `#server`, and `#logs` with cache busting; no visible error toast or browser console errors were found.
- Safety note: browser checks did not click Emby read/run/refresh controls; this pass did not package, tag, push Docker images, run RSS/Webhook/media tasks, write Emby, scan NAS/CD2, or scan media directories.

## 2026-06-05 v0.2.0 Step 22 Visible Settings UI Refresh

- Bumped the stylesheet cache key in `static/index.html` from `alsemby-v0.2.0` to `alsemby-apple-20260605` so browsers reliably load the current UI pass.
- Added a more visible Apple-style settings center layer for `Emby 配置`, proxy, TMDB, and account pages.
- Strengthened the settings intro panel with a larger title hierarchy, frosted metric tiles, softer background lighting, and clearer section kicker styling.
- Refined settings cards, server cards, form inputs, status badges, action bars, and info/error hints so the configuration pages no longer look like the previous build.
- Browser-verified `#server` loads `/static/style.css?v=alsemby-apple-20260605` and shows the new settings visual layer with no visible runtime error.
- Verified `node --check static/app.js` passed.
- Verified `git diff --check` passed.
- Safety note: this pass changed UI/CSS only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 23 Settings Standard Refinement

- Tightened the settings page into the current UI reference standard before propagating the design to other pages.
- Reduced the desktop settings shell to a focused 980px center column and changed the server form body to a denser two-column layout.
- Added a mobile settings safety pass: smaller intro hierarchy, tighter card spacing, stronger bottom dock safe area, and single-column form actions.
- Restored a clear app-shell height model so `#app`, `.main`, `.content-area`, and page scroll containers behave like a fixed admin workspace instead of a stretched document.
- Bumped the stylesheet cache key to `alsemby-apple-20260605b` so the refined UI loads without stale browser CSS.
- Browser-verified the `#server` page at desktop and 390px mobile widths: no horizontal overflow, desktop form columns resolve to two tracks, and the mobile `scroll-view` is the active scroll container.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed UI/CSS and docs only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 24 UI Design System Draft

- Added `docs/ui-design-system-v0.2.0.md` as the working UI standard for the v0.2.0 product pass.
- Captured the current product tone: Apple-style admin workstation, graphite surfaces, restrained blue accent, compact utility-first information hierarchy.
- Documented layout-shell rules for fixed app height, bounded content areas, scroll-view pages, mobile safe area, and bottom dock behavior.
- Documented component rules for typography, cards, buttons, forms, empty/error states, logs, tools, and page rollout order.
- Set the rollout priority for the next phase: Home, RSS, Webhook, Logs, Tools, and then fine-tune Cover Studio.
- Verified `node --check static/app.js` passed.
- Verified `git diff --check` passed.
- Safety note: this pass changed docs only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 25 Dashboard Workbench Rollout

- Applied the v0.2.0 UI standard to the dashboard/home page as the first page rollout after the settings baseline.
- Reframed the home page from a decorative landing surface into a quieter workbench overview.
- Reduced the hero section height and visual decoration, keeping the title, description, and primary actions readable.
- Tightened dashboard stat cards and quick command cards into compact graphite workbench controls.
- Converted the media poster wall from a huge flexible display block into a bounded preview area: 360px desktop and 260px mobile.
- Added dashboard scroll-shell rules so the home page uses the same bounded app workspace behavior as settings pages.
- Browser-verified `#dashboard` at desktop and 390px mobile widths: no horizontal overflow, mobile content scrolls, and the bottom dock remains floating.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed UI/CSS and docs only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 26 RSS Page Standard Rollout

- Applied the v0.2.0 UI standard to `RSS 真实库` without changing subscription behavior or path override logic.
- Restored RSS task cards to a desktop two-column grid after the settings grid rules had forced shared `.server-grid-layout` surfaces into one column.
- Kept mobile RSS task cards single-column with a larger bottom safe area for the floating dock.
- Refined RSS task cards, form card, empty state, type pills, path/source rows, and usage block into the graphite Apple-style component language.
- Bumped the stylesheet cache key to `alsemby-apple-20260605d`.
- Browser-verified `#rss` at desktop and 390px mobile widths: desktop grid resolves to two tracks, mobile resolves to one track, no horizontal overflow, and mobile scroll-view remains active.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed UI/CSS and docs only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 27 Webhook Page Standard Rollout

- Applied the v0.2.0 UI standard to the `Webhook` page without changing saved configuration, event intake, or cover-generation behavior.
- Compacted the Webhook intro/status panel so the current enabled state, preset, and layout read like dashboard metrics instead of large debug blocks.
- Unified Webhook config, read-only checks, recommended Emby events, local event records, and payload preview cards into the graphite Apple-style component language.
- Kept `Payload 本地解析预览` as an advanced local debug utility: it only parses pasted JSON locally, does not execute tasks, does not generate covers, and does not call the actual Webhook flow.
- Bumped the stylesheet cache key to `alsemby-apple-20260605e`.
- Browser-verified `#webhook` at desktop and 390px mobile widths: no horizontal overflow, compact debug card headers, active scroll container, and no browser console errors.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed UI/CSS and docs only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 28 Logs Center Standard Rollout

- Promoted `日志中心` as its own bottom navigation section and aligned the right-top log button with the same category model.
- Renamed log categories to module-readable labels: `全部日志`, `系统日志`, `封面系统`, `RSS真实库`, `Webhook`, `通知日志`, `Emby`, and `其他日志`.
- Rebuilt the right-top log modal into a compact log center panel with module tabs, summary metrics, local log file metadata, and a direct jump to the full log page.
- Kept the log modal and log page read-only: they only read `config/app.log`, do not trigger Emby, RSS, Webhook, cover generation, or media tasks.
- Bumped the stylesheet cache key to `alsemby-apple-20260605f` and the app script cache key to `alsemby-v0.2.0-ui20260605a`.
- Browser-verified `#logs` at desktop and 390px mobile widths: no horizontal overflow, active scroll container, module category labels visible, log modal responsive, and no browser console errors.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed UI/CSS and docs only; it did not run Emby tests, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 29 Tool Structure Clarification

- Repositioned `工具系统` as a bottom drawer / launcher instead of a large dashboard-like page.
- Split tool entries into primary tools and auxiliary checks: primary tools are `Emby 任务中心`, `RSS 真实库`, `Webhook`, `媒体问题清单`, and `合集问题清单`; auxiliary checks are `诊断助手` and `配置助手`.
- Renamed `元数据体检` to `媒体问题清单` and clarified that it reads a bounded list of Emby items, marks metadata/image/path issues, supports CSV export, and only submits single-item refresh requests after user confirmation.
- Renamed `合集体检` to `合集问题清单` and clarified that it focuses on empty collections, missing poster/overview, member counts, and low-frequency collection troubleshooting.
- Updated the compatibility `#tools` route, bottom tool drawer labels, page title mapping, and tools summary API naming to use the same product language.
- Browser-verified the bottom tool drawer at desktop and 390px mobile widths: core/auxiliary entries are visible, the drawer stays bounded, and there is no horizontal overflow.
- Browser-verified `#tools`, `#media_maintenance`, and `#collections`: page titles and intro copy match the new tool positioning, and no browser console errors were found.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed naming, UI structure, CSS, and docs only; browser checks did not click Emby read/run/refresh controls and did not run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 30 CSS Scope Cleanup

- Scoped the new Apple-style settings grid rules to `.server-page-shell` so shared `.server-grid-layout` usage no longer leaks into RSS task grids or other legacy card groups.
- Kept the settings page layout contract intact: desktop settings remain a single centered configuration card, with the card body using a two-column form grid.
- Kept the RSS layout contract intact: desktop subscription cards remain a two-column task grid, while mobile resolves to a single column.
- Bumped the stylesheet cache key to `alsemby-apple-20260605g`.
- Browser-verified `#server` and `#rss` at 1440px and 390px widths: no horizontal overflow, settings grid/RSS grid columns are correct, and no browser console errors were found.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Safety note: this pass changed CSS scoping, cache keys, and docs only; it did not click Emby read/run/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 31 UI Refactor Report

- Added `docs/v0.2.0-ui-refactor-report.md` to summarize the current v0.2.0 UI state, verification evidence, remaining useful work, and items not recommended right now.
- Captured the current conclusion: there are no UI/code blockers from the final checks, but real v0.2.0 value should come from improving practical maintenance tools rather than adding more diagnostic-only cards.
- Reconfirmed the release boundary: do not package or publish until the user explicitly asks.

## 2026-06-05 v0.2.0 Step 32 Naming And Report Audit

- Rewrote `docs/v0.2.0-ui-refactor-report.md` around the required seven delivery sections: design system, modified pages, CSS refactor content, component unification, product structure, mobile adaptation, and follow-up recommendations.
- Audited current CSS debt and documented the remaining `!important` burden honestly instead of claiming the CSS architecture is fully clean.
- Updated active runtime labels from the older `元数据体检` / `合集体检` wording to `媒体问题清单` / `合集问题清单`.
- Updated `docs/ui-design-system-v0.2.0.md` so the tool categories match the current product structure.
- Safety note: this pass changed docs and display/error labels only; it did not run Emby reads, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 33 CSS Priority Cleanup Pass

- Removed unnecessary page-level `!important` overrides from the RSS and Webhook standard rollout blocks, letting the shared component layer own card radius, background, border, and shadow where possible.
- Bumped the stylesheet cache key to `alsemby-apple-20260605l`.
- Browser-checked `#rss` and `#webhook` after the cleanup: both loaded the new cache key, kept grid layout, avoided horizontal overflow, and retained the shared 8px card radius from the design-system variable layer.
- Reduced `static/style.css` from 782 to 718 `!important` declarations in this pass; further cleanup should continue by moving old broad overrides into reusable component rules.
- Safety note: this pass changed CSS and docs only; it did not run Emby reads, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 34 Dashboard Priority Cleanup And Route Regression

- Removed unnecessary page-level `!important` overrides from the dashboard workbench standard block.
- Bumped the stylesheet cache key to `alsemby-apple-20260605l`.
- Browser-checked `#dashboard` after the cleanup: the hero, poster wall, stat cards, command cards, and bottom dock retained their gradients, borders, shadows, and shared 8px card radius with no console errors.
- Read-only desktop route regression covered `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#tools`, `#logs`, `#server`, and `#settings`: all loaded the current stylesheet key, had no horizontal overflow, showed no old `元数据体检` / `合集体检` labels, and had no browser console errors.
- Read-only mobile route regression used a temporary 390px Chrome profile with local login state only: the same nine routes loaded internal pages, had no horizontal overflow, and kept the bottom dock within the viewport.
- Reduced `static/style.css` further from 718 to 614 `!important` declarations.
- Safety note: browser checks were read-only; they did not click Emby read/run/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 35 Manual And Settings Priority Cleanup

- Removed unnecessary page-level `!important` overrides from the manual cover studio block while preserving the finalized workbench layout, preview canvas, left inspector, and floating action bar.
- Removed unnecessary page-level `!important` overrides from the settings center blocks, then restored only the two width rules needed to keep settings pages from being stretched by older global page shell rules.
- Bumped the stylesheet cache key to `alsemby-apple-20260605m`.
- Browser-verified `#manual` after cleanup: the workbench layout stayed stable, no horizontal overflow was found, and no browser console errors were found.
- Browser-verified `#server`, `#settings`, and `#account` after cleanup: Emby/settings shells stay centered at 980px on desktop, account stays at 580px, all load the new cache key, and no horizontal overflow or console errors were found.
- Read-only mobile route regression used a temporary 390px Chrome profile with local login state only for `#server`, `#settings`, `#account`, `#manual`, `#tools`, and `#logs`: all routes stayed within viewport, and the bottom dock remained bounded and floating.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 614 to 395 `!important` declarations in this pass; the remaining count is still technical debt but no longer concentrated in the latest manual/settings rollout.
- Safety note: browser checks were read-only; they did not click Emby read/run/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 36 Page Consistency Priority Cleanup

- Removed unnecessary `!important` overrides from the `Apple-inspired page consistency pass` block, moving that layer closer to normal component precedence instead of forced page overrides.
- Bumped the stylesheet cache key to `alsemby-apple-20260605n`.
- Browser-verified desktop routes `#dashboard`, `#manual`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks`: all loaded the new stylesheet key, showed no horizontal overflow, kept bounded bottom navigation, and produced no browser console errors.
- Read-only mobile route regression used a temporary 390px Chrome profile with local login state only for the same twelve routes: all stayed within viewport, and the bottom dock remained bounded and floating.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 395 to 363 `!important` declarations; the remaining largest groups are older premium/mobile/bottom-dock blocks and should be handled in smaller verified waves.
- Safety note: browser checks were read-only; they did not click Emby read/run/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 37 Tool And Product Polish Priority Cleanup

- Removed the remaining forced overrides from the `Emby tool workbenches` block so the tool workbench mobile grid and bottom dock use normal cascade order.
- Removed legacy `Product polish pass` forced overrides that duplicated newer dashboard/manual/auto page standards, letting the later Apple-style page rules own the final visual output.
- Removed several obsolete accent-border forced overrides from older Webhook/account/auto/settings helper rules so those pages fall back to the unified v0.2.0 card border language.
- Bumped the stylesheet cache key to `alsemby-apple-20260605p`.
- Browser-verified desktop `#tools`, `#media_maintenance`, `#collections`, and `#emby_tasks`: tool shells, workbench grids, and five-column bottom dock stayed stable with no horizontal overflow or console errors.
- Browser-verified desktop `#dashboard`, `#manual`, and `#auto`: dashboard poster wall, manual preview canvas, and automatic cover empty state retained the unified 8px card radius and no horizontal overflow.
- Read-only mobile route regression used a temporary 390px Chrome profile with local login state only for `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks`: all routes stayed within viewport, and the bottom dock remained five-column, bounded, and floating.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 363 to 342 `!important` declarations.
- Safety note: browser checks were read-only; they did not click Emby read/run/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 38 Dialog And CSS Audit Sync

- Removed forced overrides from the older `ALSemby UI system consolidation pass` block so the current Apple-style component layer can own the final card, button, and form rendering.
- Renamed the old mobile fallback section to `Legacy mobile adaptation pass` so CSS debt audits no longer misattribute mobile `!important` rules to the confirm dialog section.
- Bumped the stylesheet cache key to `alsemby-apple-20260605q`.
- Verified the `测试 Emby 连接` confirm dialog with a cancel-only browser interaction: the dialog opens with the expected title/actions, keeps an 8px radius, has no horizontal overflow, and closes after clicking `取消`.
- Browser-verified desktop routes `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks`: all loaded `alsemby-apple-20260605q`, had no horizontal overflow, and produced no browser console errors.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 342 to 320 `!important` declarations.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current cache key, CSS debt count, confirm dialog check, and desktop route coverage.
- Safety note: this pass changed CSS classification, docs, and cache keys only; the browser interaction clicked `取消` in the confirm dialog and did not run Emby reads, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 39 Legacy Responsive Cleanup

- Removed nonessential `!important` declarations from the old responsive layout fallback that handled manual designer, dashboard, and poster-wall mobile rules.
- Added the `Legacy responsive layout pass` section marker so future CSS debt audits can distinguish this responsive fallback from the `Tools overview` block.
- Bumped the stylesheet cache key to `alsemby-apple-20260605r`.
- Browser-verified desktop routes `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks`: all loaded `alsemby-apple-20260605r`, had no horizontal overflow, showed the five bottom entries, and produced no browser console errors.
- Browser-verified the same thirteen routes at 390px mobile width with a temporary local Chrome profile: all loaded `alsemby-apple-20260605r`, had no horizontal overflow, and kept the bottom entries `主页|封面系统|工具系统|日志|设置`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 320 to 309 `!important` declarations.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current cache key, CSS debt count, and full desktop/mobile route coverage.
- Safety note: browser checks only logged into the local UI and navigated routes; they did not click Emby read/run/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 40 Apple Component Cascade Cleanup

- Removed normal-cascade-safe `!important` declarations from the current Apple design layer for shared cards, hover states, Toast messages, and Confirm dialogs.
- Kept form, primary button, and bottom dock forced overrides in place for now because older global rules still compete with those components.
- Bumped the stylesheet cache key to `alsemby-apple-20260605s`.
- Browser-verified desktop routes `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks`: all loaded `alsemby-apple-20260605s`, had no horizontal overflow, showed the five bottom entries, and produced no browser console errors.
- Verified the `测试 Emby 连接` confirm dialog with a cancel-only browser interaction after the cascade cleanup: it opened at 420px width, kept an 8px radius, had no horizontal overflow, and closed after clicking `取消`.
- Browser-verified the same thirteen routes at 390px mobile width with a temporary local Chrome profile: all loaded `alsemby-apple-20260605s`, had no horizontal overflow, and kept the bottom entries `主页|封面系统|工具系统|日志|设置`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 309 to 284 `!important` declarations.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current cache key and CSS debt count.
- Safety note: browser checks only logged into the local UI, navigated routes, and clicked `取消` in the confirm dialog; they did not run Emby reads, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 41 Premium Visual Layer Cleanup

- Removed no-longer-needed forced overrides from the older premium visual layer before the cover-designer structural block: background, status pill, legacy cards, legacy modals, legacy buttons, and legacy Toast rules now rely on normal cascade or the later Apple component layer.
- Preserved the cover designer structural `!important` rules in the same premium block because they still override older layout rules and keep the manual cover workbench bounded.
- Bumped the stylesheet cache key to `alsemby-apple-20260605t`.
- Browser-verified desktop routes `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks`: all loaded `alsemby-apple-20260605t`, had no horizontal overflow, showed the five bottom entries, and produced no browser console errors.
- Verified the `测试 Emby 连接` confirm dialog with a cancel-only browser interaction after the premium cleanup: it opened at 420px width, kept an 8px radius, had no horizontal overflow, and closed after clicking `取消`.
- Browser-verified the same thirteen routes at 390px mobile width with a temporary local Chrome profile: all loaded `alsemby-apple-20260605t`, had no horizontal overflow, and kept the bottom entries `主页|封面系统|工具系统|日志|设置`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Reduced `static/style.css` from 284 to 260 `!important` declarations.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current cache key and CSS debt count.
- Safety note: browser checks only logged into the local UI, navigated routes, and clicked `取消` in the confirm dialog; they did not run Emby reads, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 42 Tool Structure And Emby Task Center Polish

- Repositioned the `工具系统` launcher into three product groups: `核心系统`, `问题清单`, and `辅助检查`.
- Updated both the compatibility `#tools` page and the bottom tool drawer so the structure is consistent across direct routes and popover navigation.
- Reordered `/api/tools/summary` so `Emby 任务中心`, `RSS 真实库`, and `Webhook` are the first-class core tools, followed by media/collection issue lists and auxiliary checks.
- Reworked `Emby 任务中心` copy and layout to match the Emby scheduled-task mental model: native category grouping, an explicit `神医助手` section, execution-before-confirmation language, group descriptions, and clearer running-state treatment.
- Bumped the stylesheet cache key to `alsemby-apple-20260605u`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Restarted the local ALSemby process on port `5256` and verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Verified `/api/tools/summary` returns the new core-first tool order and updated tool copy.
- Browser-verified `#tools` and `#emby_tasks`: both loaded `alsemby-apple-20260605u`, had no horizontal overflow, showed no old `媒体库维护` / `合集检查器` / `元数据体检` / `合集体检` labels, and the bottom tool drawer showed `核心系统`、`问题清单`、`辅助检查`.
- Playwright mobile-smoked `#tools`, `#emby_tasks`, `#media_maintenance`, and `#collections` at 390px width: all routes had no horizontal overflow, retained the five bottom entries, and showed no visible error toast.
- Safety note: browser checks only logged into the local UI and navigated routes; they did not click Emby read/run/stop/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 43 Emby Task Result Filters

- Connected the already-prepared `Emby 任务中心` result-state logic to the page UI.
- Added the `最近失败` metric to the intro and summary strip so failed scheduled-task runs are visible after reading Emby tasks.
- Added a second filter row for `全部结果`、`运行中`、`最近失败`、`空闲`, scoped by the selected task category.
- Added `Emby 日志` and `查看错误日志` entry points that jump to the log center with the Emby category selected.
- Added result-tone badges for task last-run status: success, warning, error, info, and muted.
- Bumped the stylesheet cache key to `alsemby-apple-20260605v`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#emby_tasks` loaded `alsemby-apple-20260605v`, had no horizontal overflow, showed no visible error toast, and displayed the new task intro metric and log entry without clicking `读取任务列表`.
- Source-verified the result filter row and last-result badge bindings in `static/index.html`, `static/app.js`, and `static/style.css`; live result filter rendering was not triggered because that would require reading Emby scheduled tasks.
- CSS debt remains at 260 `!important` declarations.
- Safety note: browser checks only navigated the local UI; they did not click Emby read/run/stop/refresh controls, run RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 44 Media Issue List Priorities

- Reworked the `媒体问题清单` issue model so actionable problems and informational tags are separated.
- Added issue severity metadata in `app/routers/emby_tools.py`: `critical`, `warning`, `info`, and `ok`.
- Treated `疑似文件缺失` and `缺路径` as critical, metadata/image/provider gaps as warning, and `4K` as an informational tag instead of a pending issue.
- Added `待处理`, `严重问题`, and `缺路径` filters to the media issue list.
- Added `issue_meta`, `actionable_issues`, `source_count`, and severity summary counts to media search results.
- Updated the media issue list UI with serious/warning/info summary pills, severity badges, actionable issue copy, and severity-colored tags.
- Updated CSV export to include severity, actionable issue list, and all issue tags.
- Bumped the stylesheet cache key to `alsemby-apple-20260605w` and the script cache key to `alsemby-v0.2.0-ui20260605b`.
- Verified the media issue model with local fake data only: `4K` no longer increments `issue_total`, while missing path/file cases are critical.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Restarted the local ALSemby process on port `5256` with PID `62243` and verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#media_maintenance` loaded `alsemby-apple-20260605w` and `alsemby-v0.2.0-ui20260605b`, had no horizontal overflow, showed no visible error toast, and exposed `待处理`、`严重问题`、`缺路径` filter options.
- Safety note: browser checks only navigated the local UI and did not click `开始检索`, Emby refresh controls, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 45 Local Service Handoff Check

- Rechecked the local ALSemby service after the Step 44 browser smoke and found the previous shell-backgrounded Python process was no longer listening on port `5256`.
- Confirmed the app log only reached normal startup messages and showed no crash traceback, indicating the process was being cleaned up by the shell/tool lifecycle rather than failing inside ALSemby.
- Restarted the local dev service in a detached `screen` session named `alsemby-local` using `uvicorn main:app --host 0.0.0.0 --port 5256`.
- Verified after a delayed recheck that the detached session remains active, PID `65065` is listening on `*:5256`, and `/api/health` returns `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- No project code was changed in this step; this entry only records the stable local service handoff state.

## 2026-06-05 v0.2.0 Step 46 Collection Issue List Priorities

- Reworked `合集问题清单` from a passive collection lookup into a severity-aware issue list.
- Added collection-specific request options in `app/routers/emby_tools.py`: `issue_filter` and `min_members`.
- Added collection issue severity rules: `空合集` is critical; `成员过少`, `缺封面`, `缺简介`, and `缺 TMDb` are warning-level actionable issues.
- Added collection filters for `待处理`, `严重问题`, `空合集`, `成员过少`, `缺 TMDb`, `缺简介`, and `缺封面`.
- Added `issue_meta`, `has_primary`, `low_members`, and severity summary output to the collection summary API.
- Updated `#collections` with the same summary strip, severity badges, actionable issue copy, and severity-colored tags used by `媒体问题清单`.
- Added a `成员过少阈值` field and CSV export for collection issue results.
- Bumped the stylesheet cache key to `alsemby-apple-20260605x` and the script cache key to `alsemby-v0.2.0-ui20260605c`.
- Verified the collection issue model with local fake data only: empty collections become critical, low-member collections become warning, and healthy collections stay out of `issue_total`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Restarted the local ALSemby service in detached `screen` session `alsemby-local` and verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#collections` loaded `alsemby-apple-20260605x` and `alsemby-v0.2.0-ui20260605c`, had no horizontal overflow, showed no visible error toast, and exposed `严重度分层`、`问题筛选`、`成员过少阈值`、`导出 CSV`.
- Mobile width was not rechecked in this step because the local project does not have Playwright installed and no new dependency was introduced just for verification.
- Safety note: browser checks only navigated the local UI and did not click `读取合集`, collection member reads, refresh controls, RSS/Webhook/media tasks, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 47 CSS Cascade De-risk

- Started the CSS architecture cleanup pass without changing runtime feature logic.
- Reduced `static/style.css` `!important` usage from 260 to 244.
- Removed nonessential strong overrides from the legacy global form rule so the v0.2.0 component/form layer can win through normal cascade.
- Removed redundant strong overrides from the final bottom Dock visual layer and the earlier Dock visual patch, so the final unified Dock styling is not silently blocked by an older safety patch.
- Kept manual cover designer structure protection, legacy mobile fallback, and floating bottom boundary protection in place because those rules previously fixed real layout and black-box issues.
- Bumped the stylesheet cache key to `alsemby-apple-20260605y`; the script cache key remains `alsemby-v0.2.0-ui20260605c`.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#server`, `#rss`, `#manual`, and `#collections`: all loaded `alsemby-apple-20260605y`, had no horizontal overflow, showed no visible error toast, and kept the final bottom Dock gradient with transparent bottom shell.
- Browser-verified the same four routes at 390px width: all loaded `alsemby-apple-20260605y`, had no horizontal overflow, kept the bottom labels `主页|封面系统|工具系统|日志|设置`, and kept the Dock within the viewport.
- Safety note: browser checks only navigated local pages and did not click Emby reads, RSS runs, Webhook triggers, cover generation/apply, package, tag, or Docker push actions.

## 2026-06-05 v0.2.0 Step 48 Logs Entry Alignment

- Re-aligned the top-right log shortcut with the standalone `日志中心` product structure.
- Changed the header log button copy from `打开实时日志` to `打开日志中心`.
- Converted the modal into a `日志快捷窗` that shares `logCenterState` filters with the full `#logs` page.
- Added level tabs to the log shortcut modal, so it now has both module categories and severity filters similar to the full log center.
- Fixed the modal category handler exposure: `setConsoleLogCategory` and the new `setConsoleLogLevel` are now returned to Vue.
- Removed `日志中心` from `/api/tools/summary` cards so logs no longer appear as a tool-system card; the bottom navigation remains the primary log entry.
- Updated the `工具系统` intro copy so auxiliary checks no longer mention log judgment.
- Bumped the stylesheet cache key to `alsemby-apple-20260605z` and the script cache key to `alsemby-v0.2.0-ui20260605d`.
- Restarted the local ALSemby service in detached `screen` session `alsemby-local` and verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Verified `/api/tools/summary` now returns `['emby_tasks', 'rss', 'webhook', 'media_maintenance', 'collections', 'diagnostics', 'config_assistant']` without a `logs` card.
- Browser-verified `#tools` loaded the new CSS/JS cache keys, had no horizontal overflow, showed no visible errors, exposed real tool labels, and no longer showed the old log-card copy or old `配置和日志判断` text.
- Browser-verified the top-right log shortcut modal: it shows `日志快捷窗`, module tabs, level tabs, `进入日志中心`, and no visible errors; clicking the `WARNING` level tab switches to `WARNING 0` empty state.
- Safety note: browser checks only read local logs and navigated local pages; they did not clear logs, run Emby tasks, trigger RSS/Webhook, generate/apply covers, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 49 Emby Task Center Product Structure

- Strengthened `Emby 任务中心` as a real core tool rather than a blank technical page before data is loaded.
- Added a local task-center preflight panel explaining that the page does not automatically connect to Emby and that run/stop actions still require confirmation.
- Added a static Emby task grouping blueprint for the empty state: Application, Database, Downloads & Conversions, Infuse Sync, Library, `神医助手 💎 PRO`, and Other.
- Added a local last-read timestamp after manually reading Emby scheduled tasks, so the loaded task state has a clear freshness indicator.
- Added desktop and mobile styles for the new preflight, blueprint, safety note, and read-banner sections.
- Bumped the stylesheet cache key to `alsemby-apple-20260605aa` and the script cache key to `alsemby-v0.2.0-ui20260605e`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#emby_tasks` loaded the new CSS/JS cache keys, had no horizontal overflow, showed no visible error, and displayed the new preflight, no-auto-connect boundary, native grouping explanation, and `神医助手 💎 PRO` grouping.
- Browser-verified `#tools` still presents the drawer-style tool entry grouped as `核心系统`、`问题清单`、`辅助检查`.
- Browser-verified `#emby_tasks` at 390px width: no horizontal overflow, preflight content visible, and the new grouping cards collapse to one column.
- Safety note: browser checks only navigated local pages; they did not click `读取任务列表`, run/stop Emby tasks, trigger RSS/Webhook, generate/apply covers, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 50 Issue List Product Value Pass

- Strengthened `媒体问题清单` and `合集问题清单` so both pages explain their practical value before users run any Emby read.
- Added local `lastReadAt` state for media and collection reads; after manual reads, the pages can show when the current result was fetched.
- Added `媒体问题清单` issue map cards for critical path/file problems, metadata warning issues, and informational 4K tags.
- Added `合集问题清单` issue map cards for empty collections, low-member collections, and collection metadata gaps.
- Added no-auto-read boundary notes to both tool control cards: media reads only happen after `开始检索`; collection reads only happen after `读取合集`; refresh/member actions remain manually triggered.
- Added result advice copy for both pages so a loaded result can guide the next action: prioritize critical path/file issues or empty collections before lower-risk metadata gaps.
- Added shared `tool-preflight`, `tool-safety-card`, `tool-blueprint-grid`, `tool-blueprint-card`, and `tool-read-banner` styles, avoiding a separate one-off style family for each issue list.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ab` and the script cache key to `alsemby-v0.2.0-ui20260605f`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#media_maintenance` and `#collections` loaded the new CSS/JS cache keys, had no horizontal overflow, showed no visible errors, and displayed the new issue-map/problem-map guidance and no-auto-read boundaries.
- Browser-verified both pages at 390px width: no horizontal overflow and the new blueprint cards collapse to a single column.
- Safety note: browser checks only navigated local pages; they did not click `开始检索`, `读取合集`, collection member reads, metadata refresh controls, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 51 Shared Tool Component CSS Consolidation

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Consolidated duplicated preflight/safety/blueprint/read-banner rules shared by `Emby 任务中心`, `媒体问题清单`, and `合集问题清单`.
- Moved the common structure for `.emby-task-preflight` / `.tool-preflight`, `.emby-task-safety-card` / `.tool-safety-card`, `.emby-task-blueprint-card` / `.tool-blueprint-card`, and `.emby-task-read-banner` / `.tool-read-banner` into grouped selectors.
- Preserved the small page-specific differences: task-center blueprint cards stay two-column with shorter cards; issue-list blueprint cards stay three-column on desktop and one-column on mobile.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ac`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Re-audited `static/style.css`: the current `!important` count is 245, so CSS debt is still present; this pass reduced duplication but did not claim to finish the strong-override cleanup.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.

## 2026-06-05 v0.2.0 Step 52 Late Visual Layer Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 245 to 223.
- Removed low-risk strong overrides from the late Apple visual layer for body/main/header backgrounds, primary/secondary/danger/icon button visuals, card/empty-state backgrounds, and the logs shortcut modal.
- Preserved the manual cover designer structural protection, floating bottom Dock boundary protection, legacy mobile spacing fallback, disabled-button hover guard, and decorative pseudo-element hiding rules because those still protect known regressions: old layout stretching, bottom black-box/covering issues, mobile spacing, hover drift, and the previously disliked colorful rectangle decoration.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ad`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and the kept-rule boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#logs`, `#manual`, `#rss`, and `#server`: all loaded `alsemby-apple-20260605ad`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified the right-top `日志快捷窗`: it opens, keeps the 22px radius and dark gradient background, shows module tabs and level tabs, and has no horizontal overflow.
- Browser-verified 390px mobile routes `#dashboard`, `#logs`, and `#manual`: all loaded `alsemby-apple-20260605ad`, had no horizontal overflow, and kept the bottom shell transparent.
- Safety note: browser checks only navigated local pages and opened the local logs shortcut; they did not clear logs, click Emby reads/runs, trigger RSS/Webhook, generate/apply covers, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 53 Legacy Mobile Fallback Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 223 to 205.
- Removed nonessential strong overrides from the old mobile fallback for `.card`, `.card-header`, generic `.modal-container`, mobile `.console-log-modal`, `.server-grid-layout`, `.module-card`, and `.resource-grid`.
- Kept the rules themselves in place as fallback styling, but let the later v0.2.0 component/page layers win through normal cascade.
- Preserved iOS input font-size protection, confirm dialog mobile dimensions, task-log popover dimensions, hand-cover mobile structure rules, floating bottom Dock boundary protection, and the manual cover desktop workbench protection.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ae`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and mobile fallback cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#logs`, `#manual`, and `#server`: all loaded `alsemby-apple-20260605ae`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified 390px mobile routes `#dashboard`, `#logs`, `#manual`, and `#server`: all loaded `alsemby-apple-20260605ae`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified the mobile `日志快捷窗`: it opens with the v0.2.0 modal standard (`width` about `366px`, `height` about `692px`, `18px` radius), shows category tabs, and has no horizontal overflow.
- Safety note: browser checks only navigated local pages and opened the local logs shortcut; they did not clear logs, click Emby reads/runs, trigger RSS/Webhook, generate/apply covers, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 54 Dashboard Mobile Fallback Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 205 to 186.
- Removed nonessential strong overrides from the old mobile dashboard/poster-wall fallback for `.dashboard-layout`, `.poster-wall-container`, `.wall-track`, mobile poster-wall animation declarations, and `.wall-item`.
- Kept the old fallback rules themselves in place, but let the later `Dashboard workbench standard pass` own the final mobile dashboard width, padding, and poster-wall height.
- Audited `Apple workspace height refinement` and intentionally left its strong overrides in place because they still protect the hand-cover designer against older desktop `designer-wrap` / `designer-main` layout rules.
- Bumped the stylesheet cache key to `alsemby-apple-20260605af`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and dashboard/workspace cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#manual`, and `#logs`: all loaded `alsemby-apple-20260605af`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified 390px mobile routes `#dashboard`, `#manual`, and `#logs`: all loaded `alsemby-apple-20260605af`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser evidence: desktop dashboard kept a `360px` poster wall, mobile dashboard now resolves to the final `260px` poster wall, and manual designer still reports grid layout with the protected designer main minimum height.
- Safety note: browser checks only navigated local pages; they did not clear logs, click Emby reads/runs, trigger RSS/Webhook, generate/apply covers, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 55 Toast Mobile Fallback Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 186 to 181.
- Removed nonessential strong overrides from the old mobile Toast fallback for `.toast-container` and `.toast-message`.
- Kept the old fallback rules themselves in place, but let the later v0.2.0 Toast component layer own the final mobile position.
- Preserved confirm dialog mobile dimensions, task-log popover dimensions, hand-cover structure rules, floating bottom Dock boundary protection, and manual cover workspace protection.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ag`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and Toast fallback cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#logs`, and `#server`: all loaded `alsemby-apple-20260605ag`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified 390px mobile routes `#dashboard`, `#logs`, and `#server`: all loaded `alsemby-apple-20260605ag`, had no horizontal overflow, kept the bottom Dock inside the viewport, and resolved the Toast container through the final mobile layer (`left/right: 12px`, `bottom: 92px`).
- Reset the browser viewport after the mobile check and confirmed the desktop width returned to `1267px`.
- Safety note: this pass only edits CSS/docs/cache keys. It does not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 56 Mobile Scroll And Toast Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 181 to 177.
- Removed one obsolete strong override from the old mobile `.scroll-view` fallback and three strong overrides from the final mobile Toast positioning rules.
- Kept the actual fallback and final rules in place, relying on normal cascade order for the low-risk mobile scroll/Toast styles.
- Preserved the floating bottom Dock boundary protection, confirm dialog mobile dimensions, task-log popover dimensions, hand-cover structure rules, and manual cover workspace protection.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ah`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and mobile scroll/Toast cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#rss`, `#logs`, and `#server`: all loaded `alsemby-apple-20260605ah`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified 390px mobile routes `#dashboard`, `#rss`, `#logs`, and `#server`: all loaded `alsemby-apple-20260605ah`, had no horizontal overflow, kept the bottom Dock inside the viewport, and kept the final mobile scroll/Toast values (`scroll-view` top/bottom padding `14px/112px` on scroll pages; Toast `left/right: 12px`, `bottom: 92px`).
- Safety note: this pass only edits CSS/docs/cache keys. It does not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 57 Confirm Dialog Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 177 to 174.
- Removed the obsolete old mobile `.confirm-box` fallback block for width, max-width, and padding.
- Let the later v0.2.0 Confirm component layer own the final width and padding through normal cascade.
- Preserved the floating bottom Dock boundary protection, task-log popover dimensions, hand-cover structure rules, and manual cover workspace protection.
- Bumped the stylesheet cache key to `alsemby-apple-20260605aj`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and Confirm cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#server` desktop confirm dialog by opening `测试 Emby 连接` and clicking `取消`: CSS key `alsemby-apple-20260605aj` loaded, dialog width stayed `420px`, padding stayed `22px`, no horizontal overflow, and the dialog closed with no visible error.
- Browser-verified `#server` at 390px mobile width with the same open/cancel flow: dialog width resolved to `358px` under the unified Confirm layer, padding stayed `22px`, no horizontal overflow, and the dialog closed with no visible error.
- Safety note: this pass only edits CSS/docs/cache keys. Browser confirmation checks may open the dialog and cancel it, but do not confirm Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 58 Task Log Popover Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 174 to 170.
- Downgraded the old mobile `.task-log-popover` width, left, right, and max-height rules from strong overrides to normal mobile fallback rules.
- Kept the task-log popover mobile dimensions in place so the local task queue popover still stays inside the viewport on narrow screens.
- Preserved the floating bottom Dock boundary protection, hand-cover structure rules, and manual cover workspace protection.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ak`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and task-log popover cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified the local task queue popover on `#dashboard` desktop by opening/closing the `系统就绪` status pill: CSS key `alsemby-apple-20260605ak` loaded, popover width stayed `360px`, no horizontal overflow, and close returned to the hidden state with no visible error.
- Browser-verified the same local task queue popover at 390px mobile width: popover width stayed inside the viewport at `350px`, no horizontal overflow, empty state showed `无正在运行的任务`, and close returned to the hidden state with no visible error.
- Safety note: this pass only edits CSS/docs/cache keys. Browser checks may open/close the local task queue popover, but do not confirm Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 59 Apple Product Layer Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 170 to 167.
- Downgraded the Apple product layer disabled-button transform guard, decorative pseudo-element hiding, and mobile `.scroll-view` general padding from strong overrides to normal cascade rules.
- Kept mobile `.scroll-view` `padding-bottom: 112px !important` because it still protects the bottom Dock safe area from content overlap.
- Bumped the stylesheet cache key to `alsemby-apple-20260605al`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and the kept bottom-safe-area boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#rss`, `#logs`, and `#server`: all loaded `alsemby-apple-20260605al`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified 390px mobile routes `#dashboard`, `#rss`, `#logs`, and `#server`: all loaded `alsemby-apple-20260605al`, had no horizontal overflow, kept the bottom Dock inside the viewport, and kept scroll pages at `scroll-view` top/bottom padding `14px/112px`.
- Browser-verified the dashboard decorative pseudo-element remains hidden (`hero-section::after` display resolves to `none`) after downgrading that rule from a strong override.
- Safety note: this pass only edits CSS/docs/cache keys. It does not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 60 Component Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 167 to 159.
- Downgraded the settings shell width, mobile settings/account shell width, RSS form emphasis border, manual/custom cover apply-button styling, and compact tool intro spacing from strong overrides to normal cascade rules.
- Kept the bottom Dock safe-area rules, hand-cover designer structure rules, and mobile scroll bottom padding protections in place.
- Bumped the stylesheet cache key to `alsemby-apple-20260605am`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and this component cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#server`, `#rss`, `#manual`, `#custom`, and `#tools`: all loaded `alsemby-apple-20260605am`, had no horizontal overflow, showed no visible toast/error, and kept the bottom shell transparent.
- Browser-verified 390px mobile routes `#server`, `#rss`, `#manual`, `#custom`, `#tools`, and `#account`: all loaded `alsemby-apple-20260605am`, had no horizontal overflow, kept the bottom Dock inside the viewport, and kept settings/account shells at `362px` within a `390px` viewport.
- Browser-verified manual and custom cover apply buttons still resolve to the gold apply gradient after removing strong overrides.
- Browser-verified opening the RSS create form without saving/running tasks: the `.rss-form-card` is visible, resolves to the blue weak-emphasis border `rgba(10, 132, 255, 0.22)`, and has no horizontal overflow.
- Safety note: this pass only edits CSS/docs/cache keys. It does not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 61 Cover Designer Mobile Cascade Repair

- Continued the CSS architecture cleanup phase and fixed a mobile cover-designer regression found during browser verification.
- Reduced `static/style.css` `!important` usage from 159 to 88.
- Downgraded early desktop cover-designer structure and control-skin overrides for `.designer-wrap`, `.designer-side`, `.designer-main`, `.preview-canvas`, `.floating-bar`, and designer accordion controls.
- Let the later Apple cover-studio layer own desktop styling and let the existing mobile single-column rules take effect again.
- Fixed the 390px mobile `#manual` / `#custom` preview canvas collapse: the canvas no longer resolves to a 2px strip and now renders as a 324px-wide mobile preview area without horizontal overflow.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ao`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and the mobile cover-designer repair.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop `#manual` and `#custom`: both loaded `alsemby-apple-20260605ao`, kept the two-column cover workbench, kept the gold apply button, and had no horizontal overflow or visible error.
- Browser-verified 390px mobile `#manual` and `#custom`: both loaded `alsemby-apple-20260605ao`, switched to single-column layout, rendered the preview canvas at 324px width, kept the floating action bar inside the viewport, and had no horizontal overflow or visible error.
- Browser-verified a broader read-only route smoke for `#dashboard`, `#rss`, `#logs`, `#server`, `#manual`, and `#custom` on desktop and 390px mobile: all loaded `alsemby-apple-20260605ao`, had no horizontal overflow, no visible error/toast, and kept the bottom shell transparent.
- Safety note: this pass only edits CSS/docs/cache keys. Browser checks did not click preview/apply buttons and did not trigger Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 62 Bottom Dock Cascade Cleanup

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 88 to 59.
- Downgraded the bottom Dock shell and dock body positioning, sizing, background, pointer-event, and pseudo-element hiding rules from strong overrides to normal cascade rules.
- Kept the scroll-view bottom safe-area padding, cover-designer mobile canvas protection, and remaining high-risk legacy guards in place.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ap`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and bottom Dock cleanup boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#rss`, `#logs`, `#server`, `#manual`, `#custom`, and `#tools`: all loaded `alsemby-apple-20260605ap`, had no horizontal overflow, showed no visible toast/error, and kept the bottom Dock floating without a large backing block.
- Browser-verified 390px mobile routes `#dashboard`, `#rss`, `#logs`, `#server`, `#manual`, `#custom`, and `#tools`: all loaded `alsemby-apple-20260605ap`, had no horizontal overflow, kept the bottom Dock inside the viewport, and preserved the cover-designer mobile canvas at 324px width on `#manual` / `#custom`.
- Safety note: this pass only edits CSS/docs/cache keys. Browser checks did not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 63 Mobile Cascade Migration

- Continued the CSS architecture cleanup phase without changing runtime feature behavior.
- Reduced `static/style.css` `!important` usage from 59 to 22.
- Downgraded the legacy mobile base transparency rules for `html`, `body`, `#app`, `.header`, `.main`, and `.content-area` from strong overrides to normal cascade rules.
- Downgraded the older `.main` width guard, bottom-shell transparency guard, designer tip-card spacing, and designer isolation rule from strong overrides to normal cascade rules.
- Migrated the early mobile cover-designer structure overrides into a later Apple cover-studio mobile rule so `#manual` / `#custom` keep their mobile single-column layout without relying on those early strong overrides.
- Kept the remaining 22 strong rules intentionally: iOS input font-size protection, scroll-view bottom safe-area padding, and cover-designer height/scroll boundary guards.
- Bumped the stylesheet cache key to `alsemby-apple-20260605ar`; the script cache key remains `alsemby-v0.2.0-ui20260605f` because JS did not change in this pass.
- Updated `docs/v0.2.0-ui-refactor-report.md` with the current CSS debt count and the remaining protected-rule boundary.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed after the CSS migration.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified desktop routes `#dashboard`, `#rss`, `#logs`, `#server`, `#manual`, `#custom`, and `#tools`: all loaded `alsemby-apple-20260605ar`, had no horizontal overflow, showed no visible toast/error, and kept the bottom Dock floating with transparent shell.
- Browser-verified 390px mobile routes `#dashboard`, `#rss`, `#logs`, `#server`, `#manual`, `#custom`, and `#tools`: all loaded `alsemby-apple-20260605ar`, had no horizontal overflow, kept the bottom Dock inside the viewport, and kept `#manual` / `#custom` in a single-column cover-designer layout with a 356px-wide preview canvas.
- Safety note: this pass only edits CSS/docs/cache keys. It does not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 64 Final UI Acceptance Audit

- Ran a requirement-level acceptance audit against the active v0.2.0 UI objective.
- Added a v0.2.0 CSS architecture index at the top of `static/style.css`, explicitly mapping the stylesheet to `Layer 1 - Base Tokens`, `Layer 2 - Shared Components`, and `Layer 3 - Page Rollouts`.
- Updated `docs/v0.2.0-ui-refactor-report.md` from a progress-style report to a final acceptance report with a dedicated验收矩阵.
- Confirmed `docs/ui-design-system-v0.2.0.md` covers product tone, layout shell, typography, tokens, cards, buttons, forms, empty/error states, logs, tools, rollout priority, and verification checklist.
- Confirmed the current stylesheet cache key is `alsemby-apple-20260605ar` and the script cache key is `alsemby-v0.2.0-ui20260605f`.
- Confirmed `static/style.css` now has 22 intentional `!important` protection rules, down from the earlier 260+ history-layer count.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Verified `/api/tools/summary` orders the useful tools as `Emby 任务中心`, `RSS 真实库`, `Webhook`, then problem lists and auxiliary checks; logs are not mixed back into tools.
- Browser-verified the 13 target routes `#dashboard`, `#manual`, `#auto`, `#rss`, `#webhook`, `#logs`, `#tools`, `#server`, `#settings`, `#account`, `#media_maintenance`, `#collections`, and `#emby_tasks` on desktop and 390px mobile: all loaded `alsemby-apple-20260605ar`, had no horizontal overflow, showed no visible error, and kept the bottom labels `主页|封面系统|工具系统|日志|设置`.
- Browser-verified `#custom` separately on desktop and 390px mobile: CSS key loaded, no horizontal overflow, no visible errors, desktop designer remained grid layout, and mobile designer remained single-column with a 356px-wide preview canvas.
- Safety note: this audit only uses local code checks, read-only API checks, and browser route inspection. It does not click Emby reads/runs, RSS/Webhook tasks, cover generation/apply, package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 65 ClaudeCode Review Triage

- Read `/Users/aliaosha/Desktop/macmini/ALSemby_CLAUDE_REVIEW_v0.2.0.md` and adopted the high-signal findings while rejecting/defering the oversized refactor items.
- Adopted: lightweight session token issuance, frontend token persistence, and token verification on the three new Emby write endpoints: `/api/emby_tools/media/refresh`, `/api/emby_tools/tasks/run`, and `/api/emby_tools/tasks/stop`.
- Adopted: explicit `confirm: true` payloads and 5-second backend cooldown guards for those Emby write endpoints.
- Adopted: dashboard stats now separate `auto_tasks` and `rss_tasks`; the existing `tasks` field now reflects automatic cover tasks instead of mixing RSS subscriptions.
- Adopted: `#tools` legacy route now resolves to the dashboard with the bottom tool drawer instead of rendering a second static tools page; the unreachable static tools page markup was removed.
- Adopted: top-right log shortcut now opens the primary `日志中心` page instead of the older modal duplicate.
- Adopted: Webhook Payload parsing copy now clearly marks the panel as a troubleshooting-only, non-required local parser.
- Adopted: metadata refresh buttons now use clearer `提交刷新` / `含图刷新` labels and warning-toned styling.
- Rejected/deferred: broad all-route authentication, CSS/JS module splitting, `.bottom-dock` full consolidation, Dockerfile/defaults change, Emby task caching, and `fetchFonts()` refactor. The Dockerfile/defaults concern was checked and not treated as a blocker because `defaults/` is present in the build context and is not excluded by `.dockerignore`.
- Restarted the local `alsemby-local` screen session so Python route changes are active; new listener PID is `37768`.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Verified unauthenticated calls to the three new Emby write endpoints return `401`, confirming they are blocked before reaching Emby.
- Browser-verified the login page uses ALSemby branding, `#tools` opens the bottom tool drawer without the old static tools page, switching away from `#tools` closes the drawer after the transition, Webhook shows `排障工具，非必填`, and the top-right log shortcut enters `日志中心` without opening the old console modal.
- Safety note: this pass did not click real Emby run/stop/refresh/apply buttons, did not run RSS/Webhook tasks, did not package, tag, or push Docker images.

## 2026-06-05 v0.2.0 Step 66 Local Release Packaging

- Ran the release-prep audit after the user asked to begin packaging for publication.
- Confirmed the ClaudeCode review P0 RSS deletion issue is already fixed: Emby library deletion and link-directory removal only run when `delete_files=true`.
- Added `CLAUDE_REVIEW*.md` and `*_CLAUDE_REVIEW*.md` to `.dockerignore` so local review artifacts are excluded from Docker build context.
- Updated release wording in `README.md`, `docs/CHANGELOG.md`, and `docs/v0.2.0-release-checklist.md` from release-candidate / not-packaged state to local-packaged state.
- Verified `node --check static/app.js` passed.
- Verified `npm run build` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Verified `git diff --check` passed.
- Verified the running local app returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}` from `/api/health`.
- Built local Docker image tags `aliaosha2521/alsemby:v0.2.0` and `aliaosha2521/alsemby:latest`; final local image ID is `sha256:09f211e3c48c86088db990c9283d920031601f3bc7566c13ad25e8acef3df13a`, size about `373MB`.
- Verified the local image contains the bundled default resources: `34` fonts, `22` template files, and `16` layout assets.
- Smoke-tested the local image in a temporary container on `5258->5256`; `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Removed the temporary smoke-test container.
- Created local release commit `efe0d5c` (`Release ALSemby v0.2.0`) and local tag `v0.2.0`.
- Pushed Docker Hub multi-arch tags `aliaosha2521/alsemby:v0.2.0` and `aliaosha2521/alsemby:latest` for `linux/amd64` and `linux/arm64`.
- Verified both pushed tags resolve to manifest digest `sha256:d71d118bff18aeea62cf9f44956c3758bddec88213194ccb26465f7b112a7e7a`.
- Safety note: this pass pushed DockerHub images as requested, but did not change the NAS container, did not connect to Emby, did not scan NAS/CD2/media directories, and did not run real RSS/Webhook/media tasks.

## 2026-06-05 v0.2.0 Step 67 TMDB RSS Subscription Expansion

- Added TMDB as the third RSS real-library task source alongside ordinary RSS/Douban and JavDB.
- Added eight explicit TMDB ranking options: movie popular, movie top rated, movie now playing, TV popular, TV top rated, TV on the air, trending movies weekly, and trending TV weekly.
- Kept trending movies and trending TV as two independent user-selectable options; no hidden double-task creation is performed.
- Added `tmdb_list_type` to RSS task create/update schemas and backend task persistence.
- Added backend task normalization so TMDB tasks clear RSS/Flaresolverr fields and force the correct movie/TV content type from the selected TMDB list.
- Added a dedicated TMDB ranking service that converts TMDB API results directly into `{title, year, tmdb_id, type}` items, bypassing RSS/Douban title-to-TMDB matching.
- Wired the RSS executor so `source_type=tmdb` fetches TMDB ranking items and then reuses the existing hard-link and Emby library refresh flow.
- Updated the RSS form UI so TMDB mode only shows TMDB list selection plus the shared Cron/server/path fields; RSS URL and Flaresolverr stay hidden.
- Updated task cards and configuration assistant checks so TMDB tasks display the selected list name and are not misreported as missing an RSS URL.
- Added `tests/test_tmdb_ranking_service.py` for TMDB option mapping, movie/TV normalization, and endpoint invocation.
- Verified `.venv/bin/python -m unittest tests.test_tmdb_ranking_service` passed.
- Verified `node --check static/app.js` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.0"}`.
- Browser-verified `#rss` with cache key `tmdb-rss-20260605`: TMDB mode shows eight options, locks media type, hides RSS URL/Flaresolverr, and switching to RSS/JavDB restores their expected fields.
- Safety note: this pass did not create or run RSS tasks, did not connect to Emby, did not scan NAS/CD2/media directories, and did not package, tag, or push Docker images.

## 2026-06-05 v0.2.1 Release

- Promoted ALSemby from `0.2.0` to `0.2.1` for the TMDB RSS subscription patch release.
- Updated FastAPI health version, frontend badge, package metadata, README release wording, compose version hint, changelog, and static cache keys.
- Added `docs/v0.2.1-release-checklist.md` for this release pass.
- Restarted the local ALSemby service on port `5256` after clearing the stale old listener PID `37768`; verified the new listener PID `66101` returns `{"status":"ok","app":"ALSemby","version":"0.2.1"}`.
- Verified `.venv/bin/python -m unittest tests.test_tmdb_ranking_service` passed.
- Verified `node --check static/app.js` passed.
- Verified `npm run build` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Verified `git diff --check` passed.
- Browser-verified `#rss` with cache key `v0.2.1-release-20260605`: the page displays `ALSemby v0.2.1`, TMDB mode shows eight list options, hides RSS URL/Flaresolverr fields, and exposes separate `趋势周榜电影` / `趋势周榜电视剧` entries without console errors.
- Built local Docker image tags `aliaosha2521/alsemby:v0.2.1` and `aliaosha2521/alsemby:latest`; local image ID is `sha256:3903639ec27c538af4ee3a3f5d6fd7ce3e438494390cf5cbf22f6cf1a8411a52`, size about `373MB`.
- Verified the local image contains bundled default resources: `34` fonts, `22` templates, `16` layouts, and static assets.
- Smoke-tested the local image in a temporary container on `5258->5256`; `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.1"}`.
- Pushed Docker Hub multi-arch tags `aliaosha2521/alsemby:v0.2.1` and `aliaosha2521/alsemby:latest` for `linux/amd64` and `linux/arm64`.
- Verified both pushed tags resolve to manifest digest `sha256:d39cc2f6e09531a154eed8002438042c170ed9cc1e8200612a42c33dd8f07c42`.
- Safety note: this release pushed DockerHub images as requested, but did not change the NAS container, did not run real RSS/Webhook tasks, did not connect to Emby for task execution, did not generate/apply covers, and did not scan NAS/CD2/media directories.

## 2026-06-06 v0.2.2 RSS Direct-Refresh Hotfix

- Diagnosed the NAS symptom where RSS tasks appeared after clicking into RSS, but disappeared after browser refresh/direct `#rss` load.
- Confirmed backend persistence was unchanged: RSS tasks still read from `config/rss_tasks.json` under the persistent `/app/config` mount.
- Fixed frontend route hydration so direct `#rss` load calls the same RSS task fetch as tab navigation; consolidated direct-load data refresh for Webhook, diagnostics, logs, config assistant, notification config, and Emby helper pages.
- Promoted ALSemby from `0.2.1` to `0.2.2`; updated FastAPI health version, frontend badge, package metadata, static cache keys, README, compose hint, changelog, and release checklist.
- Verified `npm run build` passed.
- Verified `.venv/bin/python -m unittest tests.test_tmdb_ranking_service` passed.
- Verified `.venv/bin/python -m compileall -q -x '(^|/)\\.venv/' .` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Verified `git diff --check` passed.
- Restarted local ALSemby in foreground for verification; `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.2"}`.
- Browser-verified direct `#rss` load with cache key `rss-direct-load-fix-v022-20260606`: a temporary local task named `刷新直达测试` displayed immediately after refresh, with no empty-state regression.
- Removed the temporary local `config/rss_tasks.json` fixture after verification.
- Built and pushed Docker Hub multi-arch tags `aliaosha2521/alsemby:v0.2.2` and `aliaosha2521/alsemby:latest` for `linux/amd64` and `linux/arm64`.
- Verified both pushed tags resolve to manifest digest `sha256:464cbc49acaedf242684b281d85590769478c884475c0d7781cdb0d1b2a96a63`.
- Smoke-tested the pushed `v0.2.2` image in a temporary container on `5258->5256`; `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.2"}`.
- Removed the temporary smoke-test container after verification.
- Safety note: this pass pushed DockerHub images as a hotfix, but did not change the NAS container directly, did not run RSS/Webhook tasks, did not connect to Emby for task execution, and did not scan NAS/CD2/media directories.

## 2026-06-06 Header Log Shortcut Fix

- Restored the top-right header log button to open the lightweight `日志快捷窗` modal instead of navigating to the full bottom-nav `日志中心`.
- Kept the bottom navigation `日志` entry and the modal footer `进入日志中心` button as the full log-center routes.
- Verified `npm run build` passed.
- Browser-verified the header log button with cache key `header-log-popover-20260606`: the URL hash stayed on `#dashboard`, `.modal-mask.log-center-mask` appeared, and `日志快捷窗` was visible.
- Safety note: this pass only touched frontend markup and local documentation; it did not package or push Docker images.

## 2026-06-06 TMDB Ranking Fetch Limits

- Updated TMDB RSS ranking fetch behavior to use fixed backend limits without adding user-facing controls.
- Movie popular, movie top-rated, TV popular, and TV top-rated now fetch 5 TMDB pages each, yielding up to 100 normalized unique items.
- Movie now-playing, TV on-the-air, trending movie week, and trending TV week now fetch 2 TMDB pages each, yielding up to 40 normalized unique items.
- Kept TMDB ID de-duplication; if TMDB repeats items across pages, the final count can be slightly below 100 or 40 and ALSemby does not fetch extra pages to top it up.
- Verified `.venv/bin/python -m unittest tests.test_tmdb_ranking_service` passed.
- Verified `.venv/bin/python -m compileall app core main.py` passed.
- Verified `npm run build` passed.
- Live-count checked the 8 TMDB endpoints through the NAS-configured TMDB key and proxy without printing secrets; no Emby/RSS/Webhook/media task was executed.
- Safety note: this pass only changed local backend ranking normalization/tests and documentation; it did not package or push Docker images.

## 2026-06-06 v0.2.3 Release

- Promoted ALSemby from `0.2.2` to `0.2.3`; updated FastAPI health version, frontend badge, package metadata, static cache keys, README, compose hint, changelog, and release checklist.
- Release scope includes the top-right log quick-window restoration and the fixed TMDB RSS ranking fetch limits from the previous local commits.
- Verified `npm run build` passed.
- Verified `.venv/bin/python -m unittest tests.test_tmdb_ranking_service` passed.
- Verified `.venv/bin/python -m compileall app core main.py` passed.
- Verified `docker compose -f docker-compose.example.yml config` passed.
- Verified `git diff --check` passed.
- Restarted local ALSemby; `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.3"}`.
- Browser-verified the local dashboard with cache key `v0.2.3-release-20260606`; the page displayed `ALSemby v0.2.3`.
- Built and pushed Docker Hub multi-arch tags `aliaosha2521/alsemby:v0.2.3` and `aliaosha2521/alsemby:latest` for `linux/amd64` and `linux/arm64`.
- Verified both pushed tags resolve to manifest digest `sha256:fbb96a660c16ce9d345de3e1782daefb3ce09c25e74f21e102bae9eef44bfbef`.
- Smoke-tested the pushed `v0.2.3` image in a temporary container on `5258->5256`; `/api/health` returned `{"status":"ok","app":"ALSemby","version":"0.2.3"}`.
- Removed the temporary smoke-test container after verification.
- Safety note: this release pushed DockerHub images as requested, but did not change the NAS container, did not run real RSS/Webhook tasks, did not connect to Emby for task execution, and did not scan NAS/CD2/media directories.

## 2026-06-09 v0.2.4 Cover Title Configuration

- Started the v0.2.4 local repair/experience branch after abandoning the collection ecosystem experiment.
- Upgraded the cover translation page into `封面标题`, supporting `Emby 媒体库名 -> 封面主标题 -> 封面副标题`.
- Preserved legacy subtitle-only `translations.json` compatibility: old string values still become subtitles, with the main title falling back to the Emby library name.
- Wired title mapping into automatic cover task execution, which also covers Webhook-triggered cover generation through the shared task flow.
- Updated manual cover library selection so it applies the configured main title and subtitle immediately before preview/apply.
- Added `tests/test_title_mapping.py` for legacy mapping, title/subtitle object mapping, and missing-mapping fallback behavior.
- Safety note: this pass only touched local code, frontend UI text, docs, and tests; it did not publish Docker images, run RSS/Webhook jobs, apply covers, or scan NAS/CD2/media directories.

## 2026-06-09 v0.2.4 Cover Upload Verification

- Investigated the StrmAssistant notification-enhancement conflict where Emby image upload could return success while the visible Primary image remained unchanged.
- Confirmed with a reversible live Emby check that binary media-library cover upload returns `204` but does not change the image while StrmAssistant notification enhancement is enabled.
- Confirmed the base64 media-library cover upload path changes both `ImageTags.Primary` and the served image hash under the same plugin setting.
- Fixed `core/emby_client.py` to prefer base64 uploads, verify through the user item API for `CollectionFolder` Primary tags, and avoid the slow delete/reupload fallback.
- Added `tests/test_emby_cover_upload.py` to cover base64-first success, success-response/no-change failure without deletion, and rejected-upload/no-delete safety.
- Verified `.venv/bin/python -m unittest tests.test_emby_cover_upload` passed.
- Verified `.venv/bin/python -m unittest discover tests` passed.
- Verified `npm run build` passed.
- Verified `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py` passed.
- Verified `git diff --check` passed.
- Verified local health endpoint returned `{"status":"ok","app":"ALSemby","version":"0.2.4"}`.
- Safety note: this pass changed local code, docs, and tests, and performed one controlled Emby cover write/restore on `豆瓣TOP250`; it did not publish Docker images, run RSS/Webhook jobs, or scan NAS/CD2/media directories.
