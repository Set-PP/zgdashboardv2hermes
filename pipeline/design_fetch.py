#!/usr/bin/env python3
"""Portfolio-B — pull design/render photos from '2025 ZAWG DESIGN' Telegram group."""
import asyncio, os
from telethon import TelegramClient
from db import connect

API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = r"C:\Users\user\Downloads\zawg_telethon_session.session"
GROUP = 4631928334  # 2025 ZAWG DESIGN
OUT = os.path.join(os.path.dirname(__file__), "data", "photos", "_design")
LIMIT = 500

async def main():
    os.makedirs(OUT, exist_ok=True)
    con = connect()
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    n = 0
    async for m in client.iter_messages(GROUP, limit=LIMIT):
        if not m.photo:
            continue
        fname = f"design_{m.date:%Y%m%d}_{m.id}.jpg"
        path = os.path.join(OUT, fname)
        if not os.path.exists(path):
            await m.download_media(path)
        if os.path.getsize(path) < 15000:
            os.remove(path); continue
        con.execute(
            "INSERT OR IGNORE INTO portfolio(category,title,subtitle,path,source,created) "
            "VALUES('design','Design Concept','2025 ZAWG DESIGN',?,'telegram-design',?)",
            (path, m.date.isoformat()))
        n += 1
    con.commit()
    total = con.execute("SELECT COUNT(*) c FROM portfolio WHERE category='design'").fetchone()["c"]
    print(f"downloaded/registered: {n} | total design rows: {total}")
    await client.disconnect()

asyncio.run(main())
