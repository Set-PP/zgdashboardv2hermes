#!/usr/bin/env python3
"""
P2.8 — Auto delete sync: hides photos whose Telegram messages were deleted.
Finds [ZG] groups by name, checks recent messages, hides deleted photos.
"""
import asyncio, os, sys, re
from telethon import TelegramClient
from db import connect

API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\zawg_telethon_v2.session"

async def main():
    target_site = sys.argv[1] if len(sys.argv) > 1 else None
    
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ NOT AUTHORIZED")
        return
    
    # Find [ZG] groups (same logic as tg_collect.py)
    groups = []
    async for d in client.iter_dialogs():
        t = getattr(d.entity, "title", "")
        if t and re.match(r"^\[ZG\]", t) and "Client Report" not in t:
            groups.append((d.entity.id, t))
    
    print(f"Found {len(groups)} [ZG] groups\n")
    
    con = connect()
    total_hidden = 0
    
    for gid, title in groups:
        # Get all photos from DB for matching sites (match by name keyword)
        # Extract site name from group title: [ZG] P01 25 (59 Market) → "59 Market"
        name_match = re.search(r'\(([^)]+)\)', title)
        site_name = name_match.group(1) if name_match else title
        
        # Get recent 200 messages from this group
        try:
            messages = await client.get_messages(gid, limit=200)
        except Exception as e:
            print(f"  ⚠️  {title[:45]}: {e}")
            continue
        
        # Build set of existing msg_ids that have photos
        existing = set()
        for m in messages:
            if m and m.photo:
                existing.add(m.id)
        
        # Find DB photos for sites matching this group
        # Match by site name containing the extracted name
        db_photos = con.execute("""
            SELECT p.id, p.msg_id, p.path, s.name, s.id as site_id
            FROM photos p JOIN sites s ON p.site_id = s.id
            WHERE p.keep=1 AND p.msg_id IS NOT NULL AND s.name LIKE ?
        """, (f'%{site_name}%',)).fetchall()
        
        if not db_photos:
            continue
        
        hidden = 0
        for p in db_photos:
            if p['msg_id'] not in existing:
                con.execute(
                    "UPDATE photos SET keep=0, reason='DELETED FROM TELEGRAM (auto-sync)', graded_at=datetime('now') WHERE id=?",
                    (p['id'],))
                con.commit()
                fname = os.path.basename(p['path']) if p['path'] else '?'
                print(f"  🗑️  #{p['id']} site={p['site_id']} msg={p['msg_id']} {fname}")
                hidden += 1
        
        if hidden > 0:
            print(f"  ✅ {title[:50]}: {hidden} photos hidden")
            total_hidden += hidden
    
    print(f"\n✅ Done. {total_hidden} photos hidden (deleted from Telegram).")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
