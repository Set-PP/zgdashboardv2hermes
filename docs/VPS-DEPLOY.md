# ZawG Portfolio — VPS Deployment Guide

**Problem this solves:** the site on the VPS shows dummy/fallback content because the
pipeline API (FastAPI + SQLite + photos) only existed on the dev PC. Code is identical;
the **data layer** is what was missing.

## Architecture

```
browser ──► web (Next.js :3000) ──/pipe/*──► api (FastAPI :8600, internal) ──► pipeline/data
                                                          ▲
                              data kept fresh by rsync push from the collection PC
```

- `web` serves the site and proxies `/pipe/*` → `api` (no CORS, port 8600 never public)
- `api` is a **read-only data server**; the DB + photos volume is all it needs
- Collection/grading (Telegram, Ollama GPU) stays on the PC; data is pushed after each sync

## 1. First-time setup (on VPS)

```bash
git clone https://github.com/Set-PP/zawg-portfolio.git
cd zawg-portfolio
docker compose up -d --build
```

The site is live at `http://<vps>:3000` — but with an EMPTY database until step 2.

## 2. Seed the data (one time, from the collection PC)

```bash
# on the Windows PC (git-bash), from the repo root:
scp -r pipeline/data user@<vps>:~/zawg-portfolio/pipeline/
```

That's it — real sites, photos, ops, portfolio, feed all appear.

## 3. Keep data fresh automatically

On the collection PC, create `pipeline/.env` (NOT committed):

```
VPS_TARGET=user@<vps>:/home/user/zawg-portfolio/pipeline/data/
```

The existing 3-hour cron (`zawg-site-sync`) now ends with an rsync push —
new Telegram reports/photos land on the VPS within 3h, zero manual steps.
(Requires an SSH key from the PC to the VPS: `ssh-copy-id user@<vps>`.)

## 4. Code updates

Push to `main` on GitHub → existing auto-deploy rebuilds.
**If the auto-deploy doesn't use docker-compose**, set these in its environment:

| Var | Value | Why |
|---|---|---|
| `NEXT_PUBLIC_PIPELINE_API` | `/pipe` | client calls same-origin proxy |
| `PIPELINE_INTERNAL` | `http://api:8600` | where the proxy forwards (compose network) |

Without compose, run the API next to the web app:

```bash
cd pipeline && pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8600   # pm2/systemd recommended
# and set PIPELINE_INTERNAL=http://127.0.0.1:8600 for the web process
```

## Notes

- `pipeline/data/` is gitignored **by design** (DB + hundreds of photos) — it travels via scp/rsync, not git.
- The PC cron needs the Telegram session + Ollama (GPU grading) — keep collection on the PC; the VPS only serves.
- Admin key: `pipeline/data/admin.json` on the VPS (change the default before going public).
