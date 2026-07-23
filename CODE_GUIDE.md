# Zaw G Dashboard — Complete Code Guide
> VPS-Ready Backup · July 23, 2026

---

## 🚀 VPS Quick Deploy

```bash
# 1. Upload to VPS
scp -r zawgdashboard/ user@vps:/home/user/zawgdashboard/

# 2. SSH in and install
ssh user@vps
cd /home/user/zawgdashboard
npm install
cd pipeline && pip install fastapi uvicorn && cd ..

# 3. Start backend (API)
cd pipeline
nohup python -m uvicorn api:app --port 8600 --host 127.0.0.1 > api.log 2>&1 &

# 4. Start frontend (production)
cd ..
nohup npm start > frontend.log 2>&1 &

# Or use Docker:
docker-compose up -d
```

---

## 📁 Key Files for VPS

| File | Purpose |
|---|---|
| `pipeline/data/zawg.db` | SQLite database (22 sites, 826 reports, 423 photos metadata) |
| `pipeline/data/photos/` | Photo assets (24 site folders, 461 JPGs) |
| `pipeline/api.py` | All 15+ API endpoints |
| `Dockerfile` | Docker container config |
| `docker-compose.yml` | Multi-service Docker setup |
| `docs/VPS-DEPLOY.md` | Full VPS deployment guide |

---

## 📊 Current Data State

| Metric | Count |
|---|---|
| Active sites | 22 |
| Design renders | 32 |
| Completed builds | 6 |
| Total portfolio cards | **33** (5+6+22) |
| Engineer reports | 826 |
| Site photos (total) | 423 |
| Graded photos | 403 |

---

## 🔌 API Endpoints (port 8600)

| Endpoint | Description |
|---|---|
| `/api/health` | System health |
| `/api/portfolio` | Portfolio grid (design, finished, ongoing) |
| `/api/stats` | Stats counters |
| `/api/sites` | All sites with ops |
| `/api/sites/{id}/days` | Photo journal |
| `/api/sites/{id}/reports` | Engineer reports |
| `/api/feed` | Facebook posts |
| `/api/portal/auth` | Client login |
| `/api/admin/*` | Admin panel |

---

## 🏗️ Build Commands

```bash
npm run dev      # Development with HMR
npm run build    # Production build
npm start        # Serve production build (port 3000)
```

---

## 🔧 Setup Commands Summary

```bash
# Full setup from scratch
git clone <repo>
cd zawgdashboard
npm install
cd pipeline && pip install fastapi uvicorn && cd ..
npm run build
cd pipeline && python -m uvicorn api:app --port 8600 --host 127.0.0.1 &
cd .. && npm start
```
