#!/usr/bin/env python3
"""Cron wrapper — runs the Zaw G site-data auto-sync (Telegram -> DB -> AI grade)."""
import subprocess, sys

TARGET = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\sync_sites.py"

r = subprocess.run([sys.executable, TARGET], capture_output=True, text=True)
sys.stdout.write(r.stdout)
if r.returncode != 0:
    sys.stderr.write(r.stderr[-400:])
    sys.exit(r.returncode)
