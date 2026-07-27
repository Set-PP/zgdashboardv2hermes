#!/usr/bin/env python3
"""
P3.0 — Upload database backup to Google Drive.
Uploads zawg.db + essential config to GDrive.
Run: python gdrive_backup.py
"""
import os, pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from db import connect

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_FILE = r"C:\Users\user\.openclaw\media\inbound\client_secret_682501943340_eqrjm55dikap8iq3nrsl2ii9mhbs2btk_---0f1d68f9-548b-4d18-aca7-39b6aafc2009.json"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".gdrive_token.pickle")
BACKUP_FOLDER = "ZAWG BACKUPS"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "zawg.db")

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
    print("✅ Google Drive connected\n")
    
    # Create/Find backup folder
    backup_id = find_or_create(service, BACKUP_FOLDER)
    print(f"📁 Backup folder: {backup_id}")
    
    # Upload database
    if os.path.exists(DB_PATH):
        db_size = os.path.getsize(DB_PATH)
        
        # Remove old backup first
        existing = service.files().list(
            q=f"name='zawg.db' and '{backup_id}' in parents and trashed=false",
            fields='files(id)'
        ).execute()
        for f in existing.get('files', []):
            service.files().delete(fileId=f['id']).execute()
        
        media = MediaFileUpload(DB_PATH, mimetype='application/octet-stream', resumable=True)
        result = service.files().create(
            body={'name': 'zawg.db', 'parents': [backup_id]},
            media_body=media,
            fields='id'
        ).execute()
        print(f"✅ Database uploaded ({db_size/1024:.0f} KB) → {result['id']}")
    
    # Upload gdrive token (so VPS can auth without re-login)
    if os.path.exists(TOKEN_FILE):
        media = MediaFileUpload(TOKEN_FILE, mimetype='application/octet-stream')
        # Remove old
        existing = service.files().list(
            q=f"name='gdrive_token.pickle' and '{backup_id}' in parents",
            fields='files(id)'
        ).execute()
        for f in existing.get('files', []):
            service.files().delete(fileId=f['id']).execute()
        
        result = service.files().create(
            body={'name': 'gdrive_token.pickle', 'parents': [backup_id]},
            media_body=media,
            fields='id'
        ).execute()
        print(f"✅ Token uploaded → {result['id']}")
    
    print(f"\n📁 https://drive.google.com/drive/folders/{backup_id}")

if __name__ == '__main__':
    main()
