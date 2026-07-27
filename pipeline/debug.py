#!/usr/bin/env python3
"""Recover locked DB by replaying journal, run delete_sync on recovered copy."""
import sqlite3, os, sys, re, json, shutil

DB = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\data\zawg.db"
JOURNAL = DB + "-journal"

# Read the journal to determine what was committed
def read_journal(journal_path):
    """SQLite uses a simple journal format. We'll use Python sqlite3 itself.
    On Windows with stale journals, we try opening in 'file:' URI with proper options."""
    pass

# Try opening with different SQLite URIs
for attempt_name, uri in [
    ("readonly", f"file:{DB}?mode=ro"),
    ("immutable", f"file:{DB}?immutable=yes"),
    ("temp-journal-dir", DB),
]:
    try:
        if "file:" in uri:
            conn = sqlite3.connect(uri)
        else:
            # For temp-journal, set custom journal_dir
            import tempfile
            tmpdir = tempfile.mkdtemp()
            conn = sqlite3.connect(DB, timeout=5)
            conn.execute(f"PRAGMA journal_mode = 'wal'")
            conn.execute(f"PRAGMA wal_autocheckpoint = 0")
        conn.row_factory = sqlite3.Row
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t["name"] for t in tables]
        print(f"[{attempt_name}] OK, tables: {table_names}")
        
        # Count rows
        for t in ["photos", "sites"]:
            if t in table_names:
                count = conn.execute(f"SELECT COUNT(*) as ct FROM {t}").fetchone()["ct"]
                print(f"  {t}: {count} rows")
        conn.close()
        
        # Check photo scores that might indicate deleted photos (score=0 or keep=0)
        if "photos" in table_names:
            kept = conn.execute("SELECT COUNT(*) as ct FROM photos WHERE keep=1").fetchone()["ct"]
            skipped = conn.execute("SELECT COUNT(*) as ct FROM photos WHERE keep!=1 AND keep IS NOT NULL").fetchone()["ct"]
            total = conn.execute("SELECT COUNT(*) as ct FROM photos ").fetchone()["ct"]
            print(f"\n  Photos: {total} total, {kept} kept, {skipped} not-kept")
        
        # Check what sites exist
        if "sites" in table_names:
            for r in conn.execute("SELECT id, name, code FROM sites").fetchall():
                print(f"  Site: {r['id']} | {r['name']} | {r['code']}")
        break
    except Exception as e:
        print(f"[{attempt_name}] FAILED: {e}")

# Now also check what site codes look like to match against [ZG] group titles
print("\n--- Site name/code mapping ---")
for attempt_name, uri in [
    ("readonly", f"file:{DB}?mode=ro"),
]:
    try:
        conn = sqlite3.connect(uri)
        conn.row_factory = sqlite3.Row
        print("Sites:")
        for r in conn.execute("SELECT id, name, code FROM sites").fetchall():
            print(f"  id={r['id']} | display={r['name']} | code={r['code']}")
        print("\nPhotos (keep=1 only):")
        for r in conn.execute("SELECT id, site_id, msg_id, keep, reason FROM photos WHERE keep=1 ORDER BY id DESC LIMIT 20").fetchall():
            print(f"  #{r['id']} site={r['site_id']} msg={r['msg_id']} keep={r['keep']} reason={r['reason']}")
        conn.close()
        break
    except Exception as e:
        print(f"[{attempt_name}] FAILED: {e}")
