#!/usr/bin/env python3
"""One-shot: regrade photos that mention demolition/renovation/wall-wrecking in their reason.
Uses the updated grade_photo.py with auto-filter rules."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import connect
from grade_photo import grade

def main():
    con = connect()
    # Find keep=1 photos with suspicious reasons
    keywords = ['demolition', 'demolish', 'wall demolition', 'structural repair',
                'renovation debris', 'rubble', 'wrecking', 'torn-down', 'broken bricks']
    
    for kw in keywords:
        rows = con.execute(
            "SELECT id, path, site_id, reason FROM photos WHERE keep=1 AND reason LIKE ?",
            (f'%{kw}%',)).fetchall()
        
        for r in rows:
            path = r['path']
            if not os.path.exists(path):
                print(f"  SKIP #{r['id']} — file missing: {path}")
                continue
            
            try:
                g = grade(path)
                score = g.get('score', 0)
                keep = int(bool(g.get('keep')))
                reason = str(g.get('reason', ''))[:200]
                
                con.execute(
                    "UPDATE photos SET score=?, keep=?, reason=?, graded_at=datetime('now') WHERE id=?",
                    (score, keep, reason, r['id']))
                con.commit()
                
                status = "HIDE" if keep == 0 else "KEEP"
                print(f"  #{r['id']} site={r['site_id']} → {status} score={score} reason='{reason}'")
            except Exception as e:
                print(f"  #{r['id']} ERROR: {e}")
    
    print("\nDone. Check results:")
    total = con.execute("SELECT COUNT(*) c FROM photos WHERE keep=1").fetchone()['c']
    print(f"  keep=1 (visible): {total}")

if __name__ == '__main__':
    main()
