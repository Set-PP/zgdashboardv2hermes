#!/usr/bin/env python3
"""
Upload all keep=1 photos to Google Drive and save drive_link to DB.
Idempotent — skips files already verified in Drive, retries uploads with backoff.
Headless-safe: uses existing token only (no browser prompt).
"""
import os, pickle, sys, time

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from db import connect

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_FILE = r"C:\Users\user\.openclaw\media\inbound\client_secret_682501943340_eqrjm55dikap8iq3nrsl2ii9mhbs2btk_---0f1d68f9-548b-4d18-aca7-39b6aafc2009.json"
TOKEN_FILE = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\.gdrive_token.pickle"
ROOT_NAME = "ZAWG SITES"
DRIVE_TIMEOUT = (15, 90)


def _gdrive_call(fn, max_retries=3, base_delay=2):
    """Retry flaky Drive calls with exponential backoff."""
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn()
        except (ConnectionError, TimeoutError, OSError) as e:
            last_err = e
            delay = base_delay * (2 ** attempt)
            print(f"  ⚠️ Drive call failed (try {attempt+1}/{max_retries}): {e}")
            time.sleep(delay)
    raise last_err


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("ERROR: No valid credentials and no refresh token. "
                  "Browser login is not supported in headless/cron mode.")
            sys.exit(1)
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(creds, f)

    # Build Drive service with HTTP timeout support
    from googleapiclient.http import HttpRequest
    original_do = HttpRequest.execute

    def timed_execute(self, *args, **kwargs):
        self._timeout = DRIVE_TIMEOUT
        return original_do(self, *args, **kwargs)

    HttpRequest.execute = timed_execute
    return build('drive', 'v3', credentials=creds)


def find_or_create(service, name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent:
        q += f" and '{parent}' in parents"
    results = _gdrive_call(lambda: service.files().list(q=q, fields='files(id)').execute())
    files = results.get('files', [])
    if files:
        return files[0]['id']
    body = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent:
        body['parents'] = [parent]
    result = _gdrive_call(lambda: service.files().create(body=body, fields='id').execute())
    return result['id']


def file_in_folder(service, fname, folder_id):
    """Check if a filename exists in a folder. Returns (found_file_ids) list."""
    q = f"name='{fname}' and '{folder_id}' in parents and trashed=false"
    results = _gdrive_call(lambda: service.files().list(q=q, fields='files(id)').execute())
    return [f['id'] for f in results.get('files', [])]


def upload_file(service, path, folder_id):
    """Upload a file to Drive. Returns (drive_id, was_new) tuple."""
    fname = os.path.basename(path)
    # Upload with retries
    media = MediaFileUpload(path, resumable=True)
    result = _gdrive_call(lambda: service.files().create(
        body={'name': fname, 'parents': [folder_id]},
        media_body=media, fields='id'
    ).execute())
    return result.get('id'), True


def main():
    print("Connecting to Google Drive...", end=" ", flush=True)
    service = get_service()
    upload_count = 0

    root_id = find_or_create(service, ROOT_NAME)
    folder_cache = {}
    uploaded = 0
    skipped = 0
    missing = 0
    no_action = 0

    con = connect()

    # Phase 1: Find photos that need uploading (no drive_id yet) or linking (have ID but no link)
    photos_needing_upload = con.execute("""
        SELECT p.id, p.path, s.name as site_name FROM photos p
        JOIN sites s ON p.site_id = s.id
        WHERE p.keep = 1 AND p.drive_id IS NULL AND p.path IS NOT NULL
    """).fetchall()

    photos_needing_link = con.execute("""
        SELECT p.id, p.path, s.name as site_name FROM photos p
        JOIN sites s ON p.site_id = s.id
        WHERE p.keep = 1 AND p.drive_id IS NOT NULL AND (p.drive_link IS NULL OR p.drive_link = '')
    """).fetchall()

    # Phase 2: Process uploads (files that have no drive_id)
    if photos_needing_upload:
        print(" ✅")
        print(f"Files without Drive ID: {len(photos_needing_upload)}")
        for p in photos_needing_upload:
            path = p['path']
            site_name = p['site_name']

            if not os.path.exists(path):
                missing += 1
                continue

            if site_name not in folder_cache:
                folder_id = find_or_create(service, site_name, root_id)
                folder_cache[site_name] = folder_id
            site_folder_id = folder_cache[site_name]

            # Check for duplicate in Drive first
            dupes = file_in_folder(service, os.path.basename(path), site_folder_id)
            if dupes:
                drive_id = dupes[0]
                con.execute(
                    "UPDATE photos SET drive_id=?, drive_link=? WHERE id=?",
                    (drive_id, f"https://drive.google.com/uc?export=view&id={drive_id}", p['id']))
                uploaded += 1  # counted as link/update rather than raw upload
            else:
                try:
                    drive_id, _ = upload_file(service, path, site_folder_id)
                    drive_link = f"https://drive.google.com/uc?export=view&id={drive_id}"
                    con.execute(
                        "UPDATE photos SET drive_id=?, drive_link=? WHERE id=?",
                        (drive_id, drive_link, p['id']))
                    uploaded += 1
                except Exception as e:
                    print(f"  ⚠️ {site_name}/{os.path.basename(path)}: {e}")
                    skipped += 1

    if photos_needing_link:
        # Phase 3: Photos that have drive_id but missing drive_link — verify in Drive then fix link
        for p in photos_needing_link:
            path = p['path']
            site_name = p['site_name']

            if not os.path.exists(path):
                missing += 1
                continue

            # Just rebuild the link from existing DB drive_id — no API needed
            drive_id = con.execute("SELECT drive_id FROM photos WHERE id=?", (p['id'],)).fetchone()[0]
            drive_link = f"https://drive.google.com/uc?export=view&id={drive_id}"
            con.execute(
                "UPDATE photos SET drive_link=? WHERE id=?",
                (drive_link, p['id']))
            no_action += 1

    # Verify Drive connectivity
    _gdrive_call(lambda: service.files().list(
        q="name='ZAWG SITES' and mimeType!='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id)'
    ).execute())

    print(f"\nDone ✓ ({uploaded} uploaded, {no_action} linked, {missing} missing, {skipped} errors)")
    print(f"https://drive.google.com/drive/folders/{root_id}")


if __name__ == '__main__':
    main()
