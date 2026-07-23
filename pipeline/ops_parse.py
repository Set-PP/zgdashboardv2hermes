#!/usr/bin/env python3
"""Parse real ops (stage / manpower / progress) from engineer report text -> site_ops table.

Real data only: stage + manpower are parsed from actual Telegram reports.
Progress = stage-derived estimate UNLESS an admin override is set (progress_override wins).
Run by sync_sites.py after grading; also runnable standalone.
"""
import json, re, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import connect

BUR_DIGITS = str.maketrans("၀၁၂၃၄၅၆၇၈၉", "0123456789")

# stage keywords (Burmese + English) — checked newest-report-first, first hit = current stage
STAGES = [
    ("Finishing",    ["ကြွေပြား", "tile", "ceiling", "မျက်နှာကျက်", "glass", "door", "window", "တံခါး", "ပရော်ဖဲင်"]),
    ("Painting",     ["ဆေးသုတ်", "putty", "paint", "sealer", "ကော်ပတ်"]),
    ("Plaster",      ["ပလတ်စတာ", "ချော", "plaster", "screed"]),
    ("Masonry",      ["masonry", "အုတ်", "brick", "block"]),
    ("Structure",    ["တိုင်", "ဝမ်းစာ", "beam", "column", "slab", "သံပန်း", "carpenter", "ခေါင်းစီး", "ဖေါင်း", "formwork", "steel"]),
    ("Substructure", ["footing", "foundation", "ကျင်း", "တူး", "lean", "excavat", "မြေ", "septic", "ground beam", "အောက်မြေ"]),
]
STAGE_PROGRESS = {"Substructure": 25, "Structure": 45, "Masonry": 60, "Plaster": 75, "Painting": 88, "Finishing": 95}
MILESTONE_ORDER = ["Substructure", "Structure", "Masonry", "Plaster", "Painting", "Finishing"]

# trade labels that carry daily headcounts: "Masonry -17-7-8", "Carpenter 4", "သံပန်း 7", "ပန်းရံ 5 2 1"
TRADE_RE = re.compile(
    r"(?:masonry|carpenter|smith|board|steel|သံပန်း|ပန်းရံ|လက်သမား|အုတ်|board|ပါဝါ|တڕကား|helper|worker)s?\s*[-–:]?\s*((?:\d+\s*){1,4})",
    re.I)
DATE_RE = re.compile(r"\b(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})\b")


def norm(txt: str) -> str:
    return (txt or "").translate(BUR_DIGITS)


def msg_date(text: str, fallback: str):
    m = DATE_RE.search(text or "")
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = 2000 + y if y < 100 else y
        try:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        except ValueError:
            pass
    return (fallback or "")[:10]


def manpower_series(reports):
    """reports: [(text, date)] newest first -> list of {date, workers} oldest..newest (max 7)."""
    by_date = {}
    for text, date in reports:
        t = norm(text)
        if not t.strip():
            continue
        d = msg_date(t, date)
        nums = [int(n) for grp in TRADE_RE.findall(t) for n in grp.split()]
        if nums:
            by_date[d] = by_date.get(d, 0) + sum(nums)
    days = sorted(by_date.items())[-7:]
    return [{"date": d, "workers": w} for d, w in days]


def detect_stage(reports):
    for text, _ in reports:  # newest first
        t = norm(text).lower()
        if len(t) < 10 or t.startswith("⚠"):
            continue
        for stage, keys in STAGES:  # STAGES ordered latest-first priority
            if any(k in t for k in keys):
                return stage
    return "Substructure"


def run():
    con = connect()
    sites = con.execute("SELECT id FROM sites").fetchall()
    updated = 0
    for s in sites:
        sid = s["id"]
        reports = [(r["text"] or "", r["date"] or "") for r in con.execute(
            "SELECT text, date FROM reports WHERE site_id=? ORDER BY date DESC LIMIT 120", (sid,)).fetchall()]
        series = manpower_series(reports)
        stage = detect_stage(reports)
        workers = series[-1]["workers"] if series else 0

        row = con.execute("SELECT progress_override FROM site_ops WHERE site_id=?", (sid,)).fetchone()
        override = row["progress_override"] if row else None
        progress = override if override is not None else STAGE_PROGRESS[stage]
        done_upto = MILESTONE_ORDER.index(stage)
        milestones = [{"label": m, "done": i < done_upto} for i, m in enumerate(MILESTONE_ORDER)]

        con.execute(
            """INSERT INTO site_ops (site_id, stage, progress, workers, manpower, milestones, updated)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(site_id) DO UPDATE SET stage=excluded.stage,
                 progress=excluded.progress, workers=excluded.workers,
                 manpower=excluded.manpower, milestones=excluded.milestones, updated=excluded.updated""",
            (sid, stage, progress, workers, json.dumps(series), json.dumps(milestones),
             datetime.now().isoformat(timespec="seconds")))
        updated += 1
    con.commit()
    print(f"ops_parse: {updated} sites updated")


if __name__ == "__main__":
    run()
