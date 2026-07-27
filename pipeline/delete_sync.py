#!/usr/bin/env python3
"""
delete_sync.py — P2.8 Auto delete sync: hides photos whose Telegram messages were deleted.

Finds [ZG] groups by name, checks recent messages for existing photos,
hides any DB-parked photos whose msg_ids no longer exist in Telegram.

Uses sqlite-utils with WAL mode for better concurrent access on Windows.
"""
import asyncio, os, sys, re, shutil, tempfile
from telethon import TelegramClient
import sqlite_utils

# Config
API_ID = 30450730
API_HASH = "dc6b66a4c9cff096f0cb2feb58bf0f4a"
SESSION = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\zawg_telethon_v2.session"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "zawg.db")


async def main():
    target_site = sys.argv[1] if len(sys.argv) > 1 else None

    # Connect to Telegram
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ NOT AUTHORIZED")
        await client.disconnect()
        return

    # Find [ZG] groups (same logic as tg_collect.py)
    groups = []
    async for d in client.iter_dialogs():
        t = getattr(d.entity, "title", "")
        if t and re.match(r"^\[ZG\]", t) and "Client Report" not in t:
            groups.append((d.entity.id, t))

    print(f"Found {len(groups)} [ZG] groups\n")

    # Prepare db with sqlite-utils (handles locking better)
    db = sqlite_utils.Database(DB_PATH)
    
    # Ensure WAL mode for better concurrent access on Windows
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=60000")

    # Get all sites as dict: id -> {name, code}
    sites = {}
    for row in db.query("SELECT * FROM sites"):
        sites[row['id']] = dict(row)

    # Get all photos that could be checked
    all_photos = []
    for row in db.query("SELECT * FROM photos WHERE keep=1 AND msg_id IS NOT NULL"):
        all_photos.append(dict(row))

    print(f"Total photos with keep=1 and msg_id: {len(all_photos)}\n")

    total_hidden = 0
    hidden_details = []

    for gid, title in groups:
        # Extract site name from group title
        name_match = re.search(r'\(([^)]+)\)', title)
        site_name = name_match.group(1) if name_match else title

        # Get recent 200 messages from this Telegram group
        try:
            tg_messages = await client.get_messages(gid, limit=200)
        except Exception as e:
            print(f"  ⚠️  {title[:45]}: {e}")
            continue

        # Build set of existing msg_ids that have photos
        existing_msg_ids = set()
        for m in tg_messages:
            if m and m.photo:
                existing_msg_ids.add(m.id)

        print(f"[{len(existing_msg_ids)} photos on TG]")

        # Find DB photos for sites matching this group
        matched_photos = []
        for p in all_photos:
            site_id = p.get("site_id", "")
            if not site_id or site_id not in sites:
                continue
            site_info = sites[site_id]
            site_name_db = (site_info.get("name", "") or "").lower()
            site_code = (site_info.get("code", "") or "").lower()

            # Match: either site name or site code contains the extracted group name
            if (re.search(re.escape(site_name.lower()), site_name_db) or
                re.search(re.escape(site_name.lower()), site_code)):
                matched_photos.append(p)

        if not matched_photos:
            print(f"---")
            continue

        hidden = 0
        for p in matched_photos:
            msg_id = p.get("msg_id")
            if msg_id not in existing_msg_ids:
                # Photo's TG message was deleted!
                reason = "DELETED FROM TELEGRAM (auto-sync)"
                
                db.execute(
                    """UPDATE photos SET keep=0, reason=?, graded_at=datetime('now') WHERE id=?""",
                    (reason, p['id'])
                )
                
                hidden += 1
                total_hidden += 1
                hidden_details.append({
                    'msg_id': msg_id,
                    'group': title,
                    'site_id': p.get('site_id'),
                    'path': p.get('path', ''),
                })

        if hidden > 0:
            print(f"\n  ✅ {title}: {hidden} photos hidden")

    # Write back to disk - sqlite-utils handles this atomically
    db.conn.commit()

    await client.disconnect()

    # Report results
    print("\n" + "=" * 60)
    print("DELETE SYNC REPORT")
    print("=" * 60)
    print(f"Total photos hidden: {total_hidden}")
    
    if hidden_details:
        print(f"\nHidden details:")
        for d in hidden_details[:10]:  # Show first 10
            msg_id = d['msg_id'] or '?'
            site = d.get('site_id', '?')
            group = d.get('group', '?')
            path = os.path.basename(d.get('path', '')) if d.get('path') else ''
            if len(path) > 40:
                path = path[:37] + '...'
            print(f"  msg_id={msg_id} site={site} group={group} file={path}")

        if total_hidden > 10:
            print(f"\n  ... and {total_hidden - 10} more")

    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
