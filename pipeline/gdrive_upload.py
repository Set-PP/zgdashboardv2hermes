#!/usr/bin/env python3
"""
Upload all keep=1 photos to Google Drive and save drive_link to DB.
Idempotent - skips files already verified in Drive, retries uploads with backoff.
Headless-safe: uses existing token only (no browser prompt).
Timeout-aware: caps each Drive API call to avoid hangs on large folders.
"""
import os, pickle, sys, time, threading

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from db import connect

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_FILE = r"C:\Users\user\.openclaw\media\inbound\client_secret_682501943340_eqrjm55dikap8iq3nrsl2ii9mhbs2btk_---0f1d68f9-548b-4d18-aca7-39b6aafc2009.json"
TOKEN_FILE = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\.gdrive_token.pickle"
ROOT_NAME = "ZAWG SITES"

# Per-API-call timeout. Default googole is 120s -- way too long for cron.
API_TIMEOUT = 30  # seconds per call
RETRY_MAX = 3
RETRY_BASE = 2


class APITimeoutError(Exception):
    pass


def _timeout_wrapper(fn, timeout_secs):
    """Run fn in a thread; abort if it takes longer than timeout_secs."""
    result = {"value": None, "error": None}

    def _run():
        try:
            result["value"] = fn()
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout_secs)

    if thread.is_alive():
        raise APITimeoutError(f"API call timed out after {timeout_secs}s")
    if result["error"]:
        raise result["error"]
    return result["value"]


def _gdrive_call(fn, max_retries=None, base_delay=None):
    """Retry flaky Drive calls with exponential backoff and timeout guarding."""
    _max_retries = max_retries or RETRY_MAX
    _base_delay = base_delay or RETRY_BASE

    last_err = None
    for attempt in range(_max_retries):
        try:
            return _timeout_wrapper(fn, API_TIMEOUT)
        except APITimeoutError as e:
            last_err = e
            delay = _base_delay * (2 ** attempt)
            print(f"\n  [TIMEOUT] attempt {attempt + 1}/{_max_retries}, retry in {delay}s...", flush=True)
            time.sleep(delay)
        except Exception as e:
            last_err = e
            if attempt < _max_retries - 1:
                delay = _base_delay * (2 ** attempt)
                print(f"\n  [ERR] {type(e).__name__}: {e} (attempt {attempt + 1}/{_max_retries}), retry in {delay}s...", flush=True)
                time.sleep(delay)
    raise last_err or APITimeoutError("Max retries exceeded")


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing credentials...", flush=True)
            creds = _timeout_wrapper(lambda: creds.refresh(Request()), 60)
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)
        else:
            sys.exit("ERROR: No valid credentials. Browser login not supported in cron mode.")

    return build("drive", "v3", credentials=creds)


def find_or_create(service, name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent:
        q += f" and '{parent}' in parents"
    results = _gdrive_call(lambda: service.files().list(q=q, fields="files(id)").execute())
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        body["parents"] = [parent]
    result = _gdrive_call(lambda: service.files().create(body=body, fields="id").execute())
    return result.get("id")


def file_in_folder(service, fname, folder_id):
    """Check if a filename exists in a folder. Returns list of file IDs."""
    q = f"name='{fname}' and '{folder_id}' in parents and trashed=false"
    results = _gdrive_call(lambda: service.files().list(q=q, fields="files(id)").execute())
    return [f["id"] for f in results.get("files", [])]


def upload_file(service, path, folder_id):
    """Upload a file to Drive. Returns (drive_id, was_new) tuple."""
    fname = os.path.basename(path)

    # Check if it already exists in the destination folder
    existing = file_in_folder(service, fname, folder_id)
    if existing:
        return existing[0], False  # Duplicate found! Skip upload.

    media = MediaFileUpload(path, resumable=True)
    result = _gdrive_call(lambda: service.files().create(
        body={"name": fname, "parents": [folder_id]},
        media_body=media, fields="id"
    ).execute())
    return result.get("id"), True


def main():
    start_time = time.time()
    print(f"Starting gdrive_upload.py ({API_TIMEOUT}s per API call timeout)", flush=True)

    service = get_service()
    root_id = find_or_create(service, ROOT_NAME)

    con = connect()
    print("Database connected.", flush=True)

    # Phase 1: Photos that need a new upload (no drive_id yet)
    photos_needing_upload = con.execute("""
        SELECT p.id, p.path, s.name as site_name FROM photos p
        JOIN sites s ON p.site_id = s.id
        WHERE p.keep = 1 AND p.drive_id IS NULL AND p.path IS NOT NULL
    """).fetchall()

    # Phase 2: Photos that have drive_id but no link (just rebuild)
    photos_needing_link = con.execute("""
        SELECT p.id, p.path, s.name as site_name FROM photos p
        JOIN sites s ON p.site_id = s.id
        WHERE p.keep = 1 AND p.drive_id IS NOT NULL AND (p.drive_link IS NULL OR p.drive_link = '')
    """).fetchall()

    print(f"Photos needing new upload: {len(photos_needing_upload)}")
    print(f"Photos needing link rebuild: {len(photos_needing_link)}\n", flush=True)

    if not photos_needing_upload and not photos_needing_link:
        elapsed = time.time() - start_time
        print(f"No work to do. Completed in {elapsed:.1f}s.")
        con.close()
        return

    sites_seen = set()
    folder_cache = {}
    uploaded_count = 0
    skipped_count = 0
    missing_files = 0
    dup_count = 0
    linked_count = 0

    # --- Phase 1: Upload photos without drive_id ---
    if photos_needing_upload:
        for i, p in enumerate(photos_needing_upload):
            path = p["path"]
            site_name = p["site_name"]

            # Track which sites we've hit so far
            if site_name not in sites_seen:
                print(f"\n--- Site: {site_name} ---", flush=True)
                sites_seen.add(site_name)

            if not os.path.exists(path):
                missing_files += 1
                continue

            # Get/create the site's Drive folder
            if site_name not in folder_cache:
                try:
                    folder_id = find_or_create(service, site_name, root_id)
                    folder_cache[site_name] = folder_id
                    print(f"  Folder '{site_name}': {folder_id}", flush=True)
                except Exception as e:
                    print(f"\n  Error creating folder for '{site_name}': {e}", flush=True)
                    skipped_count += 1
                    continue

            site_folder_id = folder_cache[site_name]

            try:
                drive_id, was_new = upload_file(service, path, site_folder_id)

                if not was_new:
                    dup_count += 1  # Already exists in Drive!

                drive_link = f"https://drive.google.com/uc?export=view&id={drive_id}"
                con.execute(
                    "UPDATE photos SET drive_id=?, drive_link=? WHERE id=?",
                    (drive_id, drive_link, p["id"])
                )
                if was_new:
                    uploaded_count += 1

            except Exception as e:
                # Catch all per-file exceptions -- one bad file won't kill the run
                print(f"  [ERR] {site_name}/{os.path.basename(path)}: {e}", flush=True)
                skipped_count += 1

            # Progress every 50 files
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed * 60 if elapsed > 0 else 0
                print(f"\n  Progress: {i+1}/{len(photos_needing_upload)} done "
                      f"({uploaded_count} uploaded, "
                      f"{skipped_count} skipped, "
                      f"{dup_count} dupes, "
                      f"{elapsed:.0f}s elapsed)\n", flush=True)

    # --- Phase 2: Link phase -- photos with drive_id but no link ---
    if photos_needing_link:
        for p in photos_needing_link:
            path = p["path"]
            site_name = p["site_name"]

            if not os.path.exists(path):
                missing_files += 1
                continue

            try:
                drive_id = con.execute("SELECT drive_id FROM photos WHERE id=?", (p["id"],)).fetchone()[0]
                drive_link = f"https://drive.google.com/uc?export=view&id={drive_id}"
                con.execute(
                    "UPDATE photos SET drive_link=? WHERE id=?",
                    (drive_link, p["id"])
                )
                linked_count += 1
            except Exception as e:
                print(f"  [LINK ERR] {site_name}/{os.path.basename(path)}: {e}", flush=True)
                skipped_count += 1

    con.commit()
    elapsed = time.time() - start_time

    # --- Summary ---
    total_done = uploaded_count + dup_count + linked_count
    print(f"\n{'='*45}")
    print("GDRIVE UPLOAD SUMMARY")
    print(f"{'='*45}")
    print(f"  New files uploaded:     {uploaded_count}")
    if dup_count:
        print(f"  Duplicates skipped:     {dup_count} (already in Drive)")
    if linked_count:
        print(f"  Links rebuilt:          {linked_count}")
    if missing_files:
        print(f"  Files not on disk:      {missing_files}")
    print(f"  Skipped (errors):       {skipped_count}")
    print(f"{'-'*45}")
    print(f"Total files touched:      {total_done + dup_count}")
    if photos_needing_link:
        total_touched = uploaded_count + dup_count + linked_count
        print(f"Total photos updated in DB: {total_touched}")
    print(f"Time elapsed:             {elapsed:.1f}s")
    print(f"{'='*45}")

    con.close()


if __name__ == "__main__":
    main()
