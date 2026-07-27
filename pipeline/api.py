#!/usr/bin/env python3
"""P2.4c — FastAPI: serve sites, reports, graded photos to the Next.js dashboards."""
import json, os, re
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from db import connect

app = FastAPI(title="Zaw G Pipeline API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/media", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "data", "photos")), name="media")

def rel(path: str) -> str:
    """disk path -> /media/... URL (handles both / and \\ separators)"""
    p = path.replace("\\", "/")
    m = re.search(r"/photos/(.+)$", p)
    if m:
        return "/media/" + m.group(1)
    return "/media/" + p

def img_url(path: str, site_id: str = None, msg_id: int = None) -> str:
    """Return GDrive URL if available, else local /media/ URL."""
    if site_id and msg_id:
        con = connect()
        row = con.execute(
            "SELECT drive_link FROM photos WHERE site_id=? AND msg_id=? AND drive_link IS NOT NULL",
            (site_id, msg_id)).fetchone()
        if row and row['drive_link']:
            return row['drive_link']
    return rel(path) if path else None

@app.get("/api/health")
def health():
    con = connect()
    return {
        "ok": True,
        "sites": con.execute("SELECT COUNT(*) c FROM sites").fetchone()["c"],
        "reports": con.execute("SELECT COUNT(*) c FROM reports").fetchone()["c"],
        "photos": con.execute("SELECT COUNT(*) c FROM photos").fetchone()["c"],
        "graded": con.execute("SELECT COUNT(*) c FROM photos WHERE score IS NOT NULL").fetchone()["c"],
    }

@app.get("/api/sites")
def sites():
    con = connect()
    rows = con.execute("""
        SELECT s.*,
          (SELECT COUNT(*) FROM reports r WHERE r.site_id=s.id) AS report_count,
          (SELECT COUNT(*) FROM photos p WHERE p.site_id=s.id) AS photo_count,
          (SELECT COUNT(*) FROM photos p WHERE p.site_id=s.id AND p.keep=1) AS keep_count,
          (SELECT MAX(p.date) FROM photos p WHERE p.site_id=s.id) AS last_photo,
          (SELECT p.path FROM photos p WHERE p.site_id=s.id AND p.keep=1 ORDER BY p.score DESC LIMIT 1) AS cover
        FROM sites s ORDER BY last_photo DESC NULLS LAST
    """).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["cover_url"] = rel(d.pop("cover")) if d.get("cover") else None
        out.append(d)
    # merge real parsed ops (stage/progress/workers/manpower/milestones)
    ops = {o["site_id"]: o for o in con.execute("SELECT * FROM site_ops").fetchall()}
    for d in out:
        o = ops.get(d["id"])
        d["ops"] = ({"stage": o["stage"], "progress": o["progress"], "workers": o["workers"],
                     "manpower": json.loads(o["manpower"] or "[]"),
                     "milestones": json.loads(o["milestones"] or "[]"),
                     "updated": o["updated"]} if o else None)
    return out


@app.get("/api/stats")
def stats():
    """Real company numbers from the pipeline (home-page stats strip)."""
    con = connect()
    g = lambda q: con.execute(q).fetchone()["c"]
    return {
        "sites_total": g("SELECT COUNT(*) c FROM sites"),
        "sites_active": g("SELECT COUNT(*) c FROM sites WHERE active=1"),
        "reports": g("SELECT COUNT(*) c FROM reports"),
        "photos": g("SELECT COUNT(*) c FROM photos"),
        "photos_kept": g("SELECT COUNT(*) c FROM photos WHERE keep=1"),
        "design_renders": g("SELECT COUNT(*) c FROM portfolio WHERE category='design'"),
        "finished_projects": g("SELECT COUNT(*) c FROM portfolio WHERE category='finished'"),
    }

@app.get("/api/sites/{site_id}/days")
def site_days(site_id: str, only_keep: bool = True):
    """Photo journal: photos grouped by day, best-first (the client-portal feed)."""
    con = connect()
    q = "SELECT * FROM photos WHERE site_id=?"
    if only_keep:
        q += " AND keep=1"
    q += " ORDER BY date DESC, score DESC"
    rows = con.execute(q, (site_id,)).fetchall()
    days: dict[str, dict] = {}
    for r in rows:
        day = r["date"][:10]
        d = days.setdefault(day, {"date": day, "photos": []})
        d["photos"].append({
            "url": rel(r["path"]), "score": r["score"], "reason": r["reason"],
        })
    return sorted(days.values(), key=lambda x: x["date"], reverse=True)

@app.get("/api/sites/{site_id}/reports")
def site_reports(site_id: str, limit: int = 30):
    con = connect()
    rows = con.execute(
        "SELECT * FROM reports WHERE site_id=? AND text != '' ORDER BY date DESC LIMIT ?",
        (site_id, limit)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/feed")
def feed():
    """Latest FB page posts (cached by fb_feed.py / the sync cron)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fb_feed.json")
    if not os.path.exists(path):
        return []
    return json.load(open(path, encoding="utf-8"))


def _msg_key(path: str):
    p = path.replace("\\", "/")
    # Real renders: P05_26_(POL-03)_Scene1.png → key=P05-POL-03
    m = re.search(r"([DP]\d+)_\d+_\(([^)]+)\)", p)
    if m:
        return (f"{m.group(1)}-{m.group(2).replace('_','-')}", 0)
    # Simple: P05_26 → key=P05
    m = re.search(r"[DP](\d+)_(\d+)", p)
    if m:
        return (f"{'D' if 'D' in m.group(0)[0] else 'P'}{m.group(1)}", int(m.group(2)))
    # Facebook/Telegram fallback
    m = re.search(r"design_fb_(\d{8})_(\d+)", p)
    if m:
        return (m.group(1), int(m.group(2)))
    m = re.search(r"design_(\d{8})_(\d+)", p)
    return (m.group(1), int(m.group(2))) if m else ("", 0)


def _diverse_design(rows, n: int = 12):
    """One card per project: cluster by D-number, keep the best of each."""
    items = sorted(rows, key=lambda r: _msg_key(r["path"]))
    clusters: dict[str, list[dict]] = {}
    for r in items:
        key = _msg_key(r["path"])[0]  # date string or D-number
        clusters.setdefault(key, []).append(r)
    picks = [max(c, key=lambda r: r["score"] or 0) for c in clusters.values()]
    picks.sort(key=lambda r: -(r["score"] or 0))
    return picks[:n]


_MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _design_title(path: str) -> str:
    p = path.replace("\\", "/")
    fname = p.split("/")[-1]
    # Real render: P05_26_(POL-03)_Scene1.png
    m = re.search(r"P(\d+)_\d+_\(([^)]+)\)", p)
    if m:
        pnum = m.group(1)
        name = m.group(2).replace("_", " ").strip()
        return f"Project P{pnum} — {name}"
    # D-code: D01_26_(School)_HALL.jpg
    m = re.search(r"D(\d+)_\d+_\(([^)]+)\)", p)
    if m:
        dnum = m.group(1)
        name = m.group(2).replace("_", " ").strip()
        return f"Design D{dnum} — {name}"
    # Fallback: any Dxx or Pxx reference
    m = re.search(r"[DP](\d+)", fname)
    if m:
        prefix = "Project" if 'P' in fname else "Design"
        return f"{prefix} {m.group(0)} — 2026"
    # Facebook / Telegram
    d, _ = _msg_key(p)
    if len(d) == 8:
        return f"Design Concept · {_MONTHS[int(d[4:6]) - 1]} {d[:4]}"
    return "Design Concept"


@app.get("/api/portfolio")
def portfolio():
    """Real portfolio: design renders + finished projects (AI-curated) + ongoing sites."""
    con = connect()

    def rows_of(cat: str, n: int = 6):
        rows = con.execute(
            "SELECT * FROM portfolio WHERE category=? AND score >= 7 ORDER BY score DESC, created DESC LIMIT ?",
            (cat, n)).fetchall()
        return [{"title": r["title"], "subtitle": r["subtitle"], "score": r["score"],
                 "img": rel(r["path"])} for r in rows]

    # design: pull the full curated pool, then one card per distinct project dump
    pool = con.execute(
        "SELECT * FROM portfolio WHERE category='design' AND score >= 7 ORDER BY score DESC").fetchall()
    design = [{"title": _design_title(r["path"]), "subtitle": r["subtitle"],
               "score": r["score"], "img": rel(r["path"])} for r in _diverse_design(pool)]

    # ongoing: ALL active sites with best graded photo
    all_sites = con.execute("SELECT * FROM sites WHERE active=1 ORDER BY id").fetchall()
    seen, ongoing = set(), []
    for s in all_sites:
        sid = str(s['id'])
        if sid in seen:
            continue
        # get best graded photo for this site (may be None)
        best = con.execute(
            "SELECT path, score, msg_id, drive_link FROM photos WHERE site_id=? AND keep=1 ORDER BY score DESC LIMIT 1",
            (sid,)
        ).fetchone()
        ops_stage = con.execute(
            "SELECT stage, progress_override FROM site_ops WHERE site_id=?",
            (sid,)
        ).fetchone()
        
        if best:
            # Prefer local /media/ for website display (faster, no auth issues)
            # GDrive is backup/sync only
            local_url = rel(best['path']) if best['path'] else None
            ongoing.append({
                "title": s['name'], "subtitle": s['code'] or s['title'],
                "score": best['score'],
                "img": local_url or best['drive_link'],
                "slug": sid,
            })
        else:
            # Site without graded photos yet — use stage from ops_data, auto-mapped progress
            stage_str = (ops_stage['stage'] or '') if ops_stage else ''
            prog_map = {"Substructure": 20, "Structure": 45, "Masonry": 65,
                        "Plaster": 78, "Painting": 92, "Finishing": 97}
            ongoing.append({
                "title": s['name'], "subtitle": s['code'] or s['title'],
                "score": None,
                "img": None,
                "slug": sid,
                "_stage": stage_str,
                "_auto_progress": prog_map.get(stage_str, 30),
            })
        seen.add(sid)
    
    hidden = {r["img"] for r in con.execute("SELECT img FROM curate WHERE hidden=1") if r.get("img")}
    return {"design": [d for d in design if d.get("img") not in hidden],
        "finished": [f for f in rows_of("finished") if f.get("img") not in hidden],
        "ongoing": [o for o in ongoing]}



# ---------------- Client portals + Admin (Phase 3) ----------------
import json as _json
from datetime import datetime as _dt
from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel

DATA_DIR = os.path.dirname(DB) if "DB" in dir() else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ADMIN_FILE = os.path.join(DATA_DIR, "admin.json")


def _admin_key():
    if not os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "w") as f:
            _json.dump({"key": "zawg-admin-2026"}, f)
    return _json.load(open(ADMIN_FILE))["key"]


def _require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != _admin_key():
        raise HTTPException(403, "invalid admin key")


class PortalAuth(BaseModel):
    code: str


class PortalCfg(BaseModel):
    client_name: str = ""
    access_code: str = ""
    cover_rel: str = ""
    note: str = ""


class CurateIn(BaseModel):
    img: str
    hidden: bool = False


@app.post("/api/portal/auth")
def portal_auth(body: PortalAuth):
    """Client enters their access code -> full portal payload."""
    con = connect()
    row = con.execute(
        """SELECT pc.site_id, pc.client_name, pc.cover_rel, pc.note,
                  s.name, s.code, s.title, s.active
           FROM portal_config pc JOIN sites s ON s.id = pc.site_id
           WHERE pc.access_code = ?""", (body.code.strip(),)).fetchone()
    if not row:
        raise HTTPException(404, "Invalid access code")
    sid = row["site_id"]
    photos = con.execute(
        "SELECT path, score, date FROM photos WHERE site_id=? AND keep=1 "
        "ORDER BY date DESC, score DESC LIMIT 30", (sid,)).fetchall()
    pc_ = con.execute("SELECT COUNT(*) c FROM photos WHERE site_id=?", (sid,)).fetchone()["c"]
    rep = con.execute("SELECT COUNT(*) c, MIN(date) f, MAX(date) l FROM reports WHERE site_id=?",
                      (sid,)).fetchone()
    cover = row["cover_rel"] or (rel(photos[0]["path"]) if photos else None)
    o = con.execute("SELECT * FROM site_ops WHERE site_id=?", (sid,)).fetchone()
    ops = ({"stage": o["stage"], "progress": o["progress"], "workers": o["workers"],
            "manpower": json.loads(o["manpower"] or "[]"),
            "milestones": json.loads(o["milestones"] or "[]"),
            "updated": o["updated"]} if o else None)
    return {
        "slug": sid, "name": row["name"], "code": row["code"] or row["title"],
        "ops": ops,
        "client_name": row["client_name"], "note": row["note"] or "",
        "active": bool(row["active"]), "cover": cover,
        "photos": [{"img": rel(p["path"]), "score": p["score"], "date": p["date"]} for p in photos],
        "photo_count": pc_, "report_count": rep["c"],
        "first_report": rep["f"], "last_report": rep["l"],
    }


@app.get("/api/admin/overview")
def admin_overview(_=Depends(_require_admin)):
    con = connect()
    sites = con.execute("SELECT * FROM sites ORDER BY active DESC, name").fetchall()
    out = []
    for s in sites:
        cfg = con.execute("SELECT * FROM portal_config WHERE site_id=?", (s["id"],)).fetchone()
        np_ = con.execute("SELECT COUNT(*) c FROM photos WHERE site_id=?", (s["id"],)).fetchone()["c"]
        nr = con.execute("SELECT COUNT(*) c FROM reports WHERE site_id=?", (s["id"],)).fetchone()["c"]
        best = con.execute("SELECT path FROM photos WHERE site_id=? AND keep=1 "
                           "ORDER BY score DESC LIMIT 1", (s["id"],)).fetchone()
        ops = con.execute("SELECT stage, progress, progress_override, workers FROM site_ops WHERE site_id=?",
                          (s["id"],)).fetchone()
        o = con.execute("SELECT stage, progress, progress_override, workers FROM site_ops WHERE site_id=?",
                        (s["id"],)).fetchone()
        ops = con.execute("SELECT stage, progress, progress_override FROM site_ops WHERE site_id=?",
                          (s["id"],)).fetchone()
        out.append({"site_id": s["id"], "name": s["name"], "code": s["code"],
                    "title": s["title"], "active": bool(s["active"]),
                    "photos": np_, "reports": nr,
                    "stage": ops["stage"] if ops else None,
                    "progress": ops["progress"] if ops else None,
                    "progress_override": ops["progress_override"] if ops else None,
                    "client_name": cfg["client_name"] if cfg else "",
                    "access_code": cfg["access_code"] if cfg else "",
                    "cover_rel": cfg["cover_rel"] if cfg else "",
                    "note": cfg["note"] if cfg else "",
                    "best_photo": rel(best["path"]) if best else None,
                    "stage": o["stage"] if o else None,
                    "progress": o["progress"] if o else None,
                    "progress_override": o["progress_override"] if o else None,
                    "workers": o["workers"] if o else None})
    return out


@app.get("/api/admin/covers/{site_id}")
def admin_covers(site_id: str, _=Depends(_require_admin)):
    """Candidate cover images: top site photos + design renders."""
    con = connect()
    site = con.execute(
        "SELECT path, score FROM photos WHERE site_id=? AND keep=1 "
        "ORDER BY score DESC, date DESC LIMIT 12", (site_id,)).fetchall()
    design = con.execute(
        "SELECT path, score FROM portfolio WHERE category='design' AND score>=7 "
        "ORDER BY score DESC LIMIT 12").fetchall()
    return {"site": [rel(p["path"]) for p in site],
            "design": [rel(p["path"]) for p in design]}


@app.post("/api/admin/portal/{site_id}")
def admin_save_portal(site_id: str, body: PortalCfg, _=Depends(_require_admin)):
    con = connect()
    if not con.execute("SELECT 1 FROM sites WHERE id=?", (site_id,)).fetchone():
        raise HTTPException(404, "unknown site")
    if body.access_code:
        dupe = con.execute("SELECT site_id FROM portal_config WHERE access_code=? AND site_id!=?",
                           (body.access_code, site_id)).fetchone()
        if dupe:
            raise HTTPException(409, "access code already used by another site")
    con.execute(
        """INSERT INTO portal_config (site_id, client_name, access_code, cover_rel, note, updated)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(site_id) DO UPDATE SET client_name=excluded.client_name,
             access_code=excluded.access_code, cover_rel=excluded.cover_rel,
             note=excluded.note, updated=excluded.updated""",
        (site_id, body.client_name, body.access_code, body.cover_rel, body.note,
         _dt.now().isoformat(timespec="seconds")))
    con.commit()
    return {"ok": True}


@app.get("/api/admin/curation")
def admin_curation(_=Depends(_require_admin)):
    con = connect()
    hidden = {r["img"] for r in con.execute("SELECT img FROM curate WHERE hidden=1")}
    rows = con.execute("SELECT category, title, path, score FROM portfolio ORDER BY category, score DESC").fetchall()
    return [{"category": r["category"], "title": r["title"], "score": r["score"],
             "img": rel(r["path"]), "hidden": rel(r["path"]) in hidden} for r in rows]


@app.post("/api/admin/curation")
def admin_curate(body: CurateIn, _=Depends(_require_admin)):
    con = connect()
    con.execute("INSERT INTO curate (img, hidden) VALUES (?,?) "
                "ON CONFLICT(img) DO UPDATE SET hidden=excluded.hidden",
                (body.img, 1 if body.hidden else 0))
    con.commit()
    return {"ok": True}


class OpsIn(BaseModel):
    progress: int | None = None  # 0-100, or null to return to auto (stage-derived)


@app.post("/api/admin/ops/{site_id}")
def admin_ops(site_id: str, body: OpsIn, _=Depends(_require_admin)):
    """Admin sets a real progress override for a site (null -> back to auto)."""
    con = connect()
    p = body.progress
    if p is not None and not (0 <= p <= 100):
        raise HTTPException(400, "progress must be 0-100")
    exists = con.execute("SELECT 1 FROM site_ops WHERE site_id=?", (site_id,)).fetchone()
    if not exists:
        raise HTTPException(404, "site has no parsed ops yet (run sync first)")
    if p is None:
        stage = con.execute("SELECT stage FROM site_ops WHERE site_id=?", (site_id,)).fetchone()["stage"]
        auto = {"Substructure": 25, "Structure": 45, "Masonry": 60, "Plaster": 75, "Painting": 88, "Finishing": 95}.get(stage, 50)
        con.execute("UPDATE site_ops SET progress_override=NULL, progress=? WHERE site_id=?", (auto, site_id))
    else:
        con.execute("UPDATE site_ops SET progress_override=?, progress=? WHERE site_id=?", (p, p, site_id))
    con.commit()
    return {"ok": True}
