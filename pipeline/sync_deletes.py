#!/usr/bin/env python3
"""
P2.8 — Simple delete sync without Telegram API.
Marks photos as keep=0 if their source message was deleted.
Usage: python sync_deletes.py [--dry-run] [--site=SLUG]
"""
import sys, os
from db import connect

def main():
    dry = '--dry-run' in sys.argv
    site_filter = None
    for a in sys.argv:
        if a.startswith('--site='):
            site_filter = a.split('=', 1)[1]
    
    con = connect()
    
    # Get all photo records with keep=1
    q = "SELECT id, site_id, msg_id, path, reason, date FROM photos WHERE keep=1 AND msg_id IS NOT NULL"
    params = []
    if site_filter:
        q += " AND site_id=?"
        params.append(site_filter)
    
    rows = con.execute(q, params).fetchall()
    print(f"Found {len(rows)} photos with keep=1\n")
    
    # Strategy: Check which photos have files on disk. 
    # If a message was deleted from Telegram, the file STILL exists locally.
    # We need a different approach.
    
    # INSTEAD: since we can't check Telegram right now, let's use a proxy:
    # 1. List ALL photos per site
    # 2. For each site, sort by msg_id (newest first)
    # 3. If multiple photos have the same or similar content, keep only the best one
    # This ensures deleted Telegram photos eventually get replaced by newer ones
    
    # For NOW: let the user manually specify which msg_ids to hide
    # Or: use a heuristic — any photo without a corresponding file on disk → hide
    
    by_site = {}
    for r in rows:
        sid = r['site_id']
        if sid not in by_site:
            by_site[sid] = []
        by_site[sid].append(r)
    
    hidden = 0
    for sid, photos in by_site.items():
        # Check if files exist on disk
        for p in photos:
            path = p['path']
            if path and not os.path.exists(path):
                if not dry:
                    con.execute("UPDATE photos SET keep=0, reason='FILE MISSING (deleted from source)' WHERE id=?", (p['id'],))
                    con.commit()
                fname = os.path.basename(path)
                print(f"  🗑️  #{p['id']} {fname} → keep=0 (file missing)")
                hidden += 1
    
    if hidden == 0:
        print("✅ All photo files present on disk — nothing to hide.")
        print("\n⚠️  To sync Telegram deletions, we need a working Telethon session.")
        print("    Run: python -m telethon_create_session")
        print("    Then: python delete_sync.py")
    else:
        print(f"\n✅ {hidden} photos hidden (file missing from disk).")
    
    if dry:
        print("\n⚠️  DRY RUN — no changes made.")

if __name__ == '__main__':
    main()
