#!/usr/bin/env python3
"""SQLite storage layer for the Zaw G pipeline."""
import os, sqlite3

DB = os.path.join(os.path.dirname(__file__), "data", "zawg.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
  id TEXT PRIMARY KEY,          -- slug e.g. 'p10-26-54b'
  group_id INTEGER UNIQUE,
  title TEXT,                   -- raw telegram title
  name TEXT,                    -- display name e.g. '54B'
  code TEXT,                    -- e.g. 'P10 26'
  active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_id TEXT, msg_id INTEGER, date TEXT, sender TEXT, text TEXT,
  UNIQUE(site_id, msg_id)
);
CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_id TEXT, msg_id INTEGER, path TEXT UNIQUE, date TEXT,
  score INTEGER, keep INTEGER, sharp INTEGER, site_related INTEGER,
  reason TEXT, graded_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_photos_site ON photos(site_id, date);
CREATE INDEX IF NOT EXISTS idx_reports_site ON reports(site_id, date);
CREATE TABLE IF NOT EXISTS portfolio (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT,                -- 'design' | 'finished'
  title TEXT, subtitle TEXT,
  path TEXT UNIQUE,             -- local file path (served via /media)
  source TEXT,                  -- 'facebook' | 'telegram-design'
  score INTEGER,
  created TEXT
);
CREATE TABLE IF NOT EXISTS portal_config (
  site_id TEXT PRIMARY KEY,
  client_name TEXT,
  access_code TEXT UNIQUE,
  cover_rel TEXT,               -- /media/... cover image for the client portal
  note TEXT,                    -- message shown to the client
  updated TEXT
);
CREATE TABLE IF NOT EXISTS curate (
  img TEXT PRIMARY KEY,         -- /media/... path of a portfolio item
  hidden INTEGER DEFAULT 0,
  featured INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS site_ops (
  site_id TEXT PRIMARY KEY,
  stage TEXT,                   -- parsed from latest reports
  progress INTEGER,             -- stage estimate or admin override
  progress_override INTEGER,    -- set via admin panel; NULL = auto
  workers INTEGER,
  manpower TEXT,                -- JSON [{date, workers}...] last 7 report days
  milestones TEXT,              -- JSON [{label, done}...]
  updated TEXT
);
"""

def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
