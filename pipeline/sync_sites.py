#!/usr/bin/env python3
"""Auto-sync: Telegram [ZG] groups -> SQLite -> AI grading -> ops parse -> FB feed -> VPS push.
Watchdog pattern: prints ONLY when something changed (or on failure),
so the cron job stays silent when there's nothing new."""
import os, subprocess, sys
from db import connect

# optional pipeline/.env (VPS_TARGET etc.) — no external deps
_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env):
    for _l in open(_env, encoding="utf-8"):
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, *args, timeout=1200):
    r = subprocess.run([PY, os.path.join(HERE, script), *args],
                       cwd=HERE, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "")[-400:], (r.stderr or "")[-400:]


def counts():
    con = connect()
    p = con.execute("SELECT COUNT(*) c FROM photos").fetchone()["c"]
    g = con.execute("SELECT COUNT(*) c FROM photos WHERE score IS NOT NULL").fetchone()["c"]
    r = con.execute("SELECT COUNT(*) c FROM reports").fetchone()["c"]
    return p, g, r


def main():
    p0, g0, r0 = counts()

    rc, out, err = run("tg_collect.py", timeout=1500)
    if rc != 0:
        print(f"[ZG sync] COLLECTOR FAILED: {err}")
        sys.exit(1)

    rc, out, err = run("ingest.py", timeout=900)
    if rc != 0:
        print(f"[ZG sync] INGEST FAILED: {err}")
        sys.exit(1)

    p1, _, r1 = counts()
    new_photos, new_reports = p1 - p0, r1 - r0

    if new_photos > 0:
        rc, out, err = run("grade_worker.py", "300", timeout=5400)
        if rc != 0:
            print(f"[ZG sync] GRADER FAILED: {err}")
            sys.exit(1)

    # non-fatal refreshers: ops parsing + home-page FB feed
    run("ops_parse.py", timeout=300)
    run("fb_feed.py", timeout=120)

    # push fresh data to VPS (silent no-op unless VPS_TARGET is set)
    if os.environ.get("VPS_TARGET"):
        try:
            import push_data
            push_data.main()
        except Exception as e:
            print(f"[ZG sync] push_data failed: {e}")

    p2, g2, _ = counts()
    if new_photos > 0 or new_reports > 0:
        print(f"[ZG sync] +{new_reports} reports, +{new_photos} photos, "
              f"{g2 - g0} newly graded (total {g2}/{p2} graded)")
    # else: silent — nothing new


if __name__ == "__main__":
    main()
