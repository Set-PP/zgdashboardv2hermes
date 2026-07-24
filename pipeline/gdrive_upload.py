#!/usr/bin/env python3
"""
One-shot: Upload all keep=1 photos to Google Drive and save drive_link to DB.
Idempotent — skips already-uploaded files, just updates DB links.
"""
import os, pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from db import connect

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_FILE = r"C:\Users\user\.openclaw\media\inbound\client_secret_682501943340_eqrjm55dikap8iq3nrsl2ii9mhbs2btk_---0f1d68f9-548b-4d18-aca7-39b6aafc2009.json"
TOKEN_FILE = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\.gdrive_token.pickle"
ROOT_NAME = "ZAWG SITES"

def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("🔐 Opening browser for Google login...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(creds, f)
    return build('drive', 'v3', credentials=creds)

def find_or_create(service, name, parent=None):
    q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent:
        q += f" and '{parent}' in parents"
    results = service.files().list(q=q, fields='files(id)').execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    body = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent:
        body['parents'] = [parent]
    return service.files().create(body=body, fields='id').execute()['id']

def main():
    service = get_service()
    print("✅ Google Drive connected!\n")

    root_id = find_or_create(service, ROOT_NAME)
    print(f"📁 Root: {ROOT_NAME} ({root_id})")

    con = connect()

    # Get all keep=1 photos directly with their paths
    photos = con.execute("""
        SELECT p.id, p.path, p.site_id, s.name as site_name
        FROM photos p JOIN sites s ON p.site_id = s.id
        WHERE p.keep = 1 AND p.path IS NOT NULL
    """).fetchall()

    print(f"📸 {len(photos)} photos to process\n")

    folder_cache = {}
    uploaded = 0
    skipped = 0
    missing = 0

    for p in photos:
        path = p['path']
        site_name = p['site_name']

        if not path or not os.path.exists(path):
            missing += 1
            continue

        # Get or create site folder
        if site_name not in folder_cache:
            folder_cache[site_name] = find_or_create(service, site_name, root_id)
        site_folder_id = folder_cache[site_name]

        fname = os.path.basename(path)

        try:
            # Check if already in Drive
            existing = service.files().list(
                q=f"name='{fname}' and '{site_folder_id}' in parents and trashed=false",
                fields='files(id)'
            ).execute()
            existing_files = existing.get('files', [])

            if existing_files:
                drive_id = existing_files[0]['id']
            else:
                media = MediaFileUpload(path, resumable=True)
                result = service.files().create(
                    body={'name': fname, 'parents': [site_folder_id]},
                    media_body=media,
                    fields='id'
                ).execute()
                drive_id = result.get('id')
                uploaded += 1

            drive_link = f"https://drive.google.com/uc?export=view&id={drive_id}"

            # Save to DB
            con.execute(
                "UPDATE photos SET drive_id=?, drive_link=? WHERE id=?",
                (drive_id, drive_link, p['id']))
            con.commit()

        except Exception as e:
            print(f"  ⚠️  {site_name}/{fname}: {e}")
            skipped += 1

    print(f"\n✅ Done — {uploaded} uploaded, {missing} missing files, {skipped} errors")
    print(f"📁 https://drive.google.com/drive/folders/{root_id}")

if __name__ == '__main__':
    main()
