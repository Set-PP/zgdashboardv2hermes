#!/usr/bin/env python3
"""Debug script to understand the database state."""
import sqlite3, os, sys, re, json, shutil

DB = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\data\zawg.db"
JOURNAL = DB + "-journal"

print(f"DB: {DB}")
print(f"Journal exists: {os.path.exists(JOURNAL)}")
print(f"Journal size: {os.path.getsize(JOURNAL) if os.path.exists(JOURNAL) else 0}")

# Try different approaches to open the DB

# 1. Default connect
try:
    conn = sqlite3.connect(DB)
    print("[default] connected successfully")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t["name"] for t in tables]
    print(f"  Tables: {table_names}")
    conn.close()
except Exception as e:
    print(f"[default] FAILED: {e}")

# 2. With journal_mode=OFF (tells SQLite to ignore any existing journal)
try:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=OFF")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t["name"] for t in tables]
    print(f"[journal_mode=OFF] Tables: {table_names}")
    if "photos" in table_names:
        count = conn.execute("SELECT COUNT(*) FROM photos WHERE keep=1").fetchone()[0]
        print(f"  Photos kept: {count}")
        for r in conn.execute("SELECT id, site_id, msg_id FROM photos WHERE keep=1 ORDER BY id DESC LIMIT 3").fetchall():
            print(f"    #{r['id']} site={r['site_id']} msg={r['msg_id']}")
        print("  All sites:")
        for r in conn.execute("SELECT id, name, code FROM sites").fetchall():
            print(f"    {r['name']} ({r['code']})")
    conn.close()
except Exception as e:
    print(f"[journal_mode=OFF] FAILED: {e}")

# 3. Read raw DB structure (bypassing journal recovery)
try:
    with open(DB, 'rb') as f:
        header = f.read(100)
    page_size = int.from_bytes(header[16:18], 'big')
    print(f"\nDB page size: {page_size}")
    
    # Check file format version bytes at offset 18-21
    fmt_version_writable = header[18]
    fmt_version_reader = header[19]
    print(f"File format versions: write={fmt_version_writable}, read={fmt_version_reader}")
except Exception as e:
    print(f"[raw DB] Error: {e}")

# 4. Try using the journal_recovery pragma or sqlite3 tool
print("\n--- Attempting to recover with manual journal deletion ---")
if os.path.exists(JOURNAL):
    print(f"Journal file found at {JOURNAL}")
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    # Copy the DB and its journal somewhere safe where we have full control
    import shutil, os
    safe_db = os.path.join(temp_dir, "zawg_safe.db")
    safe_journal = os.path.join(temp_dir, "zawg_safe.db-journal")
    shutil.copy2(DB, safe_db)
    
    # Copy journal if it exists - we'll manage it ourselves
    try:
        with open(JOURNAL, 'rb') as f_src:
            journal_data = f_src.read()
        with open(safe_journal, 'wb') as f_dst:
            f_dst.write(journal_data)
        print(f"  Copied {len(journal_data)} bytes of journal to safe location")
    except Exception as e:
        print(f"  Could not copy journal: {e}")
    
    # Now try opening the safe DB with journal_mode=delete
    try:
        conn = sqlite3.connect(safe_db)
        result = conn.execute("PRAGMA journal_mode").fetchone()
        mode = result[0] if result else "unknown"
        print(f"  [safe db, initial mode]: {mode}")
        
        # Try to recover committed data from the journal
        if "wal" in str(mode):
            conn.execute("PRAGMA wal_checkpoint(FULL)")
        elif "delete" in str(mode) or "truncate" in str(mode):
            pass  # regular rollback journal - should auto-recover on open
        
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t["name"] for t in tables]
        print(f"  Safe DB tables: {table_names}")
        
        if "photos" in table_names:
            count_total = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
            count_kept = conn.execute("SELECT COUNT(*) FROM photos WHERE keep=1").fetchone()[0]
            print(f"  Photo totals - total: {count_total}, kept: {count_kept}")
            
            # Show unkept photos (the ones that might have been deleted from TG)
            not_kept = conn.execute("SELECT COUNT(*) FROM photos WHERE keep IS NOT NULL AND keep != 1").fetchone()[0]
            print(f"  Not-kept photos: {not_kept}")
            
            for r in conn.execute("SELECT id, site_id, msg_id, keep, reason FROM photos ORDER BY keep ASC LIMIT 5").fetchall():
                kept_label = "kept" if r['keep'] == 1 else f"skip(k={r['keep']})" if r['keep'] is not None else "null"
                print(f"    #{r['id']} {kept_label} site={r['site_id']} msg={r['msg_id']} reason={r.get('reason', 'none')}")
        
        conn.close()
        
        # Copy back to original - the recovered data is now in safe_db, write it back.
        print("\n  Recovery successful! Writing changes back...")
        shutil.copy2(safe_db, DB)
        print(f"  Wrote {safe_db} -> {DB}")
        
        # Verify what we just wrote
        conn2 = sqlite3.connect(DB)
        count_final = conn2.execute("SELECT COUNT(*) FROM photos WHERE keep=1").fetchone()[0]
        print(f"  Final state - kept: {count_final}")
        for r in conn2.execute("SELECT id, site_id, msg_id FROM photos ORDER BY keep ASC LIMIT 3").fetchall():
            print(f"    #{r['id']} keep={r['keep']}")
        conn2.close()
        
    except Exception as e:
        print(f"  [safe db]: FAILED: {e}")

print("\ndone")