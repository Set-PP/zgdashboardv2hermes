#!/usr/bin/env python3
"""
P3.1 — Restore database + photos from Google Drive to local machine.
Run on VPS after git clone: python gdrive_restore.py
Pulls: zawg.db (database) + all ZAWG SITES photos + design renders.
"""
import os, pickle, io
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_FILE = r"C:\Users\user\.openclaw\media\inbound\client_secret_682501943340_eqrjm55dikap8iq3nrsl2ii9mhbs2btk_---0f1d68f9-548b-4d18-aca7-39b6aafc2009.json"
# On VPS, put client_secret in pipeline/ and update this path
TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".gdrive_token.pickle")
BACKUP_FOLDER = "ZAWG BACKUPS"
PHOTOS_FOLDER = "ZAWG SITES"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "zawg.db")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
DESIGN_DIR = os.path.join(PHOTOS_DIR, "_design")

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

def download_file(service, file_id, dest_path):
    """Download a single file from GDrive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return os.path.getsize(dest_path)

def download_folder(service, folder_id, dest_dir, skip_existing=True):
    """Download all files from a GDrive folder recursively."""
    os.makedirs(dest_dir, exist_ok=True)
    downloaded = 0
    
    # List all files in folder
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=500
    ).execute()
    
    for f in results.get('files', []):
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            # Recurse into subfolder
            sub_dir = os.path.join(dest_dir, f['name'])
            downloaded += download_folder(service, f['id'], sub_dir, skip_existing)
        else:
            dest = os.path.join(dest_dir, f['name'])
            if skip_existing and os.path.exists(dest):
                continue
            try:
                size = download_file(service, f['id'], dest)
                downloaded += 1
                if downloaded % 50 == 0:
                    print(f"  📥 {downloaded} files...")
            except Exception as e:
                print(f"  ⚠️  {f['name']}: {e}")
    
    return downloaded

def main():
    service = get_service()
    print("✅ Google Drive connected\n")

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DESIGN_DIR, exist_ok=True)

    # 1. Download database backup
    print("📦 Downloading database...")
    backup_results = service.files().list(
        q=f"name='zawg.db' and trashed=false",
        fields="files(id, size)",
        orderBy="createdTime desc"
    ).execute()
    
    db_files = backup_results.get('files', [])
    if db_files:
        db_id = db_files[0]['id']
        size = download_file(service, db_id, DB_PATH)
        print(f"  ✅ Database: {size/1024:.0f} KB")
    else:
        print("  ⚠️  No database backup found in GDrive")
        print("  Run gdrive_backup.py on your local machine first!")

    # 2. Download photos
    print("\n📸 Downloading site photos...")
    folder_results = service.files().list(
        q=f"name='{PHOTOS_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)"
    ).execute()
    
    photo_folders = folder_results.get('files', [])
    if photo_folders:
        photos_id = photo_folders[0]['id']
        total = download_folder(service, photos_id, PHOTOS_DIR)
        print(f"  ✅ {total} photos downloaded")
    else:
        print("  ⚠️  'ZAWG SITES' folder not found in GDrive")
        print("  Run gdrive_upload.py on your local machine first!")

    # 3. Also download GDrive token for future use
    print("\n🔑 Downloading auth token...")
    token_results = service.files().list(
        q=f"name='gdrive_token.pickle' and trashed=false",
        fields="files(id)"
    ).execute()
    for f in token_results.get('files', []):
        download_file(service, f['id'], TOKEN_FILE)
        print(f"  ✅ Token saved")

    print(f"\n✅ Restore complete!")
    print(f"   DB: {DB_PATH}")
    print(f"   Photos: {PHOTOS_DIR}")
    print(f"\n📋 Next: python -m uvicorn api:app --port 8600 &")
    print(f"          cd .. && npm start")

if __name__ == '__main__':
    main()
