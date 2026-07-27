#!/usr/bin/env python3
"""SQLite storage layer for the Zaw G pipeline."""
import os, sqlite3

DB = os.path.join(os.path.dirname(__file__), "data", "zawg.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
  id TEXT PRIMARY KEY,
  group_id INTEGER UNIQUE,
  title TEXT,
  name TEXT,
  code TEXT,
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
  category TEXT,
  title TEXT, subtitle TEXT,
  path TEXT UNIQUE,
  source TEXT,
  score INTEGER,
  created TEXT
);
CREATE TABLE IF NOT EXISTS portal_config (
  site_id TEXT PRIMARY KEY,
  client_name TEXT,
  access_code TEXT UNIQUE,
  cover_rel TEXT,
  note TEXT,
  updated TEXT
);
CREATE TABLE IF NOT EXISTS curate (
  img TEXT PRIMARY KEY,
  hidden INTEGER DEFAULT 0,
  featured INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS site_ops (
  site_id TEXT PRIMARY KEY,
  stage TEXT,
  progress INTEGER,
  progress_override INTEGER,
  workers INTEGER,
  manpower TEXT,
  milestones TEXT,
  updated TEXT
);
"""

def connect():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
