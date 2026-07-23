#!/usr/bin/env python3
"""P2.4b — Grade all ungraded photos in the DB via local Ollama (batched, resumable)."""
import sys, time, json
from db import connect
from grade_photo import grade

BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 30

def main():
    con = connect()
    rows = con.execute(
        "SELECT id, path FROM photos WHERE score IS NULL ORDER BY date DESC LIMIT ?",
        (BATCH,)).fetchall()
    total_left = con.execute("SELECT COUNT(*) c FROM photos WHERE score IS NULL").fetchone()["c"]
    print(f"Ungraded: {total_left} | grading batch of {len(rows)}")
    for i, r in enumerate(rows, 1):
        try:
            g = grade(r["path"])
            con.execute(
                "UPDATE photos SET score=?, keep=?, sharp=?, site_related=?, reason=?, graded_at=datetime('now') WHERE id=?",
                (g.get("score"), int(bool(g.get("keep"))), int(bool(g.get("sharp"))),
                 int(bool(g.get("site_related"))), str(g.get("reason", ""))[:200], r["id"]))
            con.commit()
            print(f"  [{i}/{len(rows)}] #{r['id']} score={g.get('score')} keep={g.get('keep')} | {str(g.get('reason',''))[:60]}")
        except Exception as e:
            print(f"  [{i}/{len(rows)}] #{r['id']} ERROR: {e}")
            time.sleep(2)
    print("Batch done.")

if __name__ == "__main__":
    main()
