#!/usr/bin/env python3
"""P2.4a — Ingest Telegram messages into SQLite (text-only pull, links existing photos)."""
import asyncio, os, re
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from db import connect

API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = r"C:\Users\user\Downloads\zawg_telethon_session.session"
PHOTOS = os.path.join(os.path.dirname(__file__), "data", "photos")
DAYS = 7

def slugify(title: str):
    m = re.match(r"^\[ZG\](\w+)\s+(\d+)\s*\((.+?)\)", title)
    if m:
        code = f"{m.group(1)} {m.group(2)}"
        name = m.group(3).strip()
        slug = re.sub(r"[^a-z0-9]+", "-", f"{m.group(1)}-{m.group(2)}-{name}".lower()).strip("-")
        return slug, code, name
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug, "", title

async def main():
    con = connect()
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    since = datetime.now(timezone.utc) - timedelta(days=DAYS)

    groups = []
    async for d in client.iter_dialogs():
        t = getattr(d.entity, "title", "")
        if t and re.match(r"^\[ZG\]", t) and "Client Report" not in t:
            groups.append((d.entity.id, t))

    n_r = n_p = 0
    for gid, title in groups:
        slug, code, name = slugify(title)
        con.execute(
            "INSERT INTO sites(id,group_id,title,name,code,active) VALUES(?,?,?,?,?,1) "
            "ON CONFLICT(id) DO UPDATE SET group_id=excluded.group_id,title=excluded.title",
            (slug, gid, title, name, code))
        async for m in client.iter_messages(gid, offset_date=since, reverse=True, limit=200):
            if not (m.text or m.photo):
                continue
            sender = getattr(m.sender, "first_name", None) or getattr(m.sender, "title", "?")
            try:
                con.execute(
                    "INSERT OR IGNORE INTO reports(site_id,msg_id,date,sender,text) VALUES(?,?,?,?,?)",
                    (slug, m.id, m.date.isoformat(), sender, (m.text or "")[:1000]))
                if con.total_changes: n_r += 1
            except Exception:
                pass
            if m.photo:
                fname = f"{m.date:%Y%m%d}_{m.id}.jpg"
                safe = re.sub(r"[^\w\-\(\) ]", "", title).strip()
                path = os.path.join(PHOTOS, safe, fname)
                if os.path.exists(path):
                    try:
                        con.execute(
                            "INSERT OR IGNORE INTO photos(site_id,msg_id,path,date) VALUES(?,?,?,?)",
                            (slug, m.id, path, m.date.isoformat()))
                        n_p += 1
                    except Exception:
                        pass
        con.commit()
        print(f"  {title[:45]:45s} -> {slug}")

    sites = con.execute("SELECT COUNT(*) c FROM sites").fetchone()["c"]
    reps = con.execute("SELECT COUNT(*) c FROM reports").fetchone()["c"]
    pho = con.execute("SELECT COUNT(*) c FROM photos").fetchone()["c"]
    print(f"\nDB: {sites} sites | {reps} reports | {pho} photos")
    await client.disconnect()

asyncio.run(main())
