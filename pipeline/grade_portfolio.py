#!/usr/bin/env python3
"""Portfolio grader — AI-grade ungraded portfolio rows (portfolio mode); drop rejects."""
import os, sys
from db import connect
from grade_photo import grade

BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 40

con = connect()
rows = con.execute("SELECT id, path, category FROM portfolio WHERE score IS NULL LIMIT ?", (BATCH,)).fetchall()
left = con.execute("SELECT COUNT(*) c FROM portfolio WHERE score IS NULL").fetchone()["c"]
print(f"ungraded portfolio items: {left} | batch {len(rows)}")
kept = dropped = 0
for i, r in enumerate(rows, 1):
    try:
        g = grade(r["path"], mode="portfolio")
        score = g.get("score") or 0
        ok = bool(g.get("keep")) and bool(g.get("site_related"))
        if ok and score >= 7:
            con.execute("UPDATE portfolio SET score=? WHERE id=?", (score, r["id"]))
            kept += 1
        else:
            con.execute("DELETE FROM portfolio WHERE id=?", (r["id"],))
            try: os.remove(r["path"])
            except OSError: pass
            dropped += 1
        con.commit()
        print(f"  [{i}/{len(rows)}] {r['category']:8s} score={score} {'KEEP' if ok and score>=7 else 'DROP'} | {str(g.get('reason',''))[:55]}")
    except Exception as e:
        print(f"  [{i}/{len(rows)}] ERROR {e}")
print(f"\nkept={kept} dropped={dropped}")
