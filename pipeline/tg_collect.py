#!/usr/bin/env python3
"""P2.2 — Collect daily reports + photos from [ZG] site-engineer groups."""
import asyncio, json, os, re
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient

API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\zawg_telethon_v2.session"
OUT = os.path.join(os.path.dirname(__file__), "data")
DAYS = 90  # backfill 3 months of photos

async def main():
    os.makedirs(OUT, exist_ok=True)
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("NOT AUTHORIZED"); return

    since = datetime.now(timezone.utc) - timedelta(days=DAYS)
    groups = []
    async for d in client.iter_dialogs():
        t = getattr(d.entity, "title", "")
        if t and re.match(r"^\[ZG\]", t) and "Client Report" not in t:
            groups.append((d.entity.id, t))

    print(f"Found {len(groups)} engineer groups. Scanning last {DAYS} days...\n")
    summary = []
    for gid, title in groups:
        safe = re.sub(r"[^\w\-\(\) ]", "", title).strip()
        gdir = os.path.join(OUT, "photos", safe)
        os.makedirs(gdir, exist_ok=True)
        msgs, photos = [], 0
        async for m in client.iter_messages(gid, offset_date=since, reverse=True, limit=150):
            if not (m.text or m.photo):
                continue
            entry = {
                "id": m.id,
                "date": m.date.isoformat(),
                "sender": getattr(m.sender, "first_name", None) or getattr(m.sender, "title", "?"),
                "text": (m.text or "")[:500],
                "has_photo": bool(m.photo),
            }
            if m.photo:
                photos += 1
                path = os.path.join(gdir, f"{m.date:%Y%m%d}_{m.id}.jpg")
                if not os.path.exists(path):
                    await m.download_media(path)
                entry["photo_path"] = path
            msgs.append(entry)
        summary.append({"group_id": gid, "title": title, "messages": len(msgs), "photos": photos})
        print(f"  {title[:40]:40s} msgs={len(msgs):3d} photos={photos:3d}")
        for mm in msgs[-2:]:  # show latest 2 as samples
            txt = mm["text"].replace("\n", " ")[:110]
            print(f"      └ {mm['date'][:16]} | {mm['sender'][:12]:12s} | {'📷' if mm['has_photo'] else '  '} {txt}")

    with open(os.path.join(OUT, "reports_raw.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSaved summary → data/reports_raw.json")
    await client.disconnect()

asyncio.run(main())
