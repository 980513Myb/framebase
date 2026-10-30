# ALSemby v0.2.0 UI Design System

> Current reference page: `#server` settings center after Step 23.

## Product Tone

- ALSemby should feel like a quiet Apple-style admin workstation, not a marketing page and not a noisy monitoring wall.
- Main surfaces use graphite black, restrained frosted panels, Apple-blue accents, and compact hierarchy.
- Avoid decorative floating shapes, colorful placeholder blocks, oversized empty backgrounds, and nested card-in-card layouts.
- The product structure stays practical: Home, Cover System, Tools, Logs, Settings.

## Layout Shell

- `#app` is a fixed-height admin workspace: `100vh`, no document-level sprawl.
- `.main` owns the app frame, `.content-area` stays bounded, and page content scrolls through `.scroll-view`.
- Floating bottom dock must never reserve a large opaque block or cover final content. Every scroll page needs a bottom safe area of at least `112px`; dense mobile pages can use `160-180px`.
- Desktop content should prefer centered shells between `960px` and `1120px`, depending on information density.
- Mobile content should use `calc(100vw - 28px)` shells, single-column cards, and compact intro panels.

## Typography

- Font stack stays system-first: Apple / BlinkMac / Segoe / PingFang / Microsoft YaHei.
- Page hero titles: 28-42px desktop, 24-28px mobile.
- Card titles: 15-18px.
- Field labels and meta text: 11-12px, semibold, muted.
- No negative letter spacing. Kicker labels can use small positive tracking.

## Tokens

- Primary background: near-black graphite.
- Main surface: translucent graphite panel with subtle top highlight.
- Accent: Apple blue `#0a84ff`, used for focus, active nav, primary links, and selected states.
- Success: green only for confirmed healthy/on states.
- Warning: amber only for caution or incomplete setup.
- Danger: red only for destructive actions and errors.
- Border radius standard is 8px for cards/buttons/inputs; pills only for badges, toggles, and the bottom dock.

## Cards

- Cards are individual functional units only. Do not put page sections inside decorative outer cards.
- Use one soft border, one subtle top sheen, and a restrained shadow.
- Card headers should be clear and compact. Avoid two-line English/Chinese title collisions.
- Repeated cards should align in a grid; config forms should prefer one focused card over many scattered fragments.

## Buttons

- Primary action: light Apple-blue/ice button for safe positive actions.
- Secondary action: translucent graphite button.
- Destructive action: small red/low-emphasis until confirmation.
- Icon buttons should use existing Font Awesome icons and include visible text when the action is not obvious.
- Buttons must keep stable height and not resize the layout on hover.

## Forms

- Settings desktop standard: 980px shell, one main config card, two-column form body where fields are short.
- Long or sensitive fields can span full width.
- Mobile forms always collapse to one column.
- Inputs use dark inset surfaces, subtle border, and blue focus ring.
- Helper text should explain impact, not repeat the field label.

## Empty And Error States

- Empty states must be compact and useful: icon, short title, one sentence, optional next action.
- Do not use large colorful placeholder illustrations.
- Errors should show cause and next step. Toasts are for immediate feedback; persistent issues need inline hints.

## Logs

- Logs are a primary bottom-nav section, not a tool.
- Right-top quick log button should open a log panel grouped by type: system, RSS, webhook, cover, Emby task, and errors.
- Log rows should be dense, filterable, and copy-friendly.

## Tools

- Tool entry should use the bottom drawer pattern, matching the cover-system drawer.
- A tool must have actual operational value, not only diagnostics or documentation.
- Existing tool categories:
  - RSS real library
  - Webhook
  - Emby task center
  - Media issue list
  - Collection issue list
  - Auxiliary diagnostics

## Page Rollout Priority

1. Home: make it a clear workbench overview, not a decorative landing page.
2. RSS: keep subscription operations dense and readable; preserve per-subscription path overrides.
3. Webhook: keep setup simple; move local payload parsing into an advanced/debug section if retained.
4. Logs: make it a real first-class page and quick panel.
5. Tools: return to bottom drawer entry; avoid a static dashboard full of auxiliary cards.
6. Cover studio: keep the current inspector/canvas direction, then tune spacing only.

## Verification Checklist

- Browser check desktop and 390px mobile.
- Confirm no horizontal overflow.
- Confirm bottom dock does not cover final content.
- Confirm no console error toast.
- Run `node --check static/app.js`.
- Run `.venv/bin/python -m compileall -q main.py app core config_manager.py constants.py`.
- Run `git diff --check`.
- Confirm `/api/health` still returns `ALSemby`.
