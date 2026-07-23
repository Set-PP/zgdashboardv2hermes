# ─── Telegram Photo Sync to Google Drive ───
# Uploads graded photos from local disk → GDrive folders organized by [ZG] group.
# Usage: python tele_photo_to_drive.py [--migrate-all]

import sqlite3, os, sys, json, re, io, time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DB_PATH = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\data\zawg.db"
PHOTOS_DIR = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\data\photos"
TOKENS_PATH = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\.zawg-drive-tokens.json"

# ─── Load tokens & authenticate ───
with open(TOKENS_PATH) as f:
    tokens = json.load(f)

CLIENT_ID = '936890683495-d4fb3c8jo3tgtr1l7dkodpgsbprpn693.apps.googleusercontent.com'
TOKEN_URI = "https://oauth2.googleapis.com/token"

creds = Credentials(
    token=tokens['access_token'],
    refresh_token=tokens.get('refresh_token'),
    token_uri=TOKEN_URI,
    client_id=CLIENT_ID,
)

if creds.expired:
    creds.refresh(None)

SERVICE = build('drive', 'v3', credentials=creds)

# ─── Drive folder management ───
ZAWG_ROOT_PARENT = "1CH7NkMKoBejGpgLvVeaD4FKIfJFnZm0V"  # Your existing ZAWG SITES folder

def find_or_create_root():
    """Find or create top-level ZAWG_SITES_ROOT folder under ZAWG SITES."""
    result = SERVICE.files().list(
        q=f"name='ZAWG_SITES_ROOT' and '{ZAWG_ROOT_PARENT}' in parents "
          f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    
    if result.get('files'):
        return result['files'][0]['id']
    
    meta = {"name": "ZAWG_SITES_ROOT", "mimeType": "application/vnd.google-apps.folder"}
    resp = SERVICE.files().create(body=meta, fields="id").execute()
    print(f"✅ Created ZAWG_SITES_ROOT ({resp['id']})")
    return resp["id"]

def safe_name_for_drive(s):
    """Sanitize folder name for GDrive."""
    return re.sub(r'[/\\:*?"<>|_]+', '_', s.strip() or '')[:50]

def ensure_folder(parent_id, folder_name):
    """Create or find a folder inside parent_id. Returns ID."""
    result = SERVICE.files().list(
        q=f"name='{folder_name}' and '{parent_id}' in parents "
          f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)"
    ).execute()
    
    if result.get('files'):
        return result['files'][0]['id']
    
    meta = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    resp = SERVICE.files().create(body=meta, fields="id").execute()
    return resp['id']

def upload_photo_to_drive(filepath, drive_folder_id, filename):
    """Upload a photo to GDrive folder. Returns file ID or None."""
    if not os.path.exists(filepath):
        return None
    
    # Check if already uploaded
    check = SERVICE.files().list(
        q=f"'{drive_folder_id}' in parents and name='{filename}' and trashed=false",
        fields="files(id)"
    ).execute()
    
    if check.get('files'):
        return check['files'][0]['id']  # Already exists
    
    mime = 'image/jpeg' if filepath.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
    media = MediaFileUpload(filepath, mimetype=mime, resumable=True)
    
    metadata = {
        "name": filename,
        "parents": [drive_folder_id]
    }
    
    try:
        resp = SERVICE.files().create(body=metadata, media_body=media).execute()
        return resp.get('id')
    except Exception as e:
        return None

# ─── Migration logic ───
def migrate_existing_photos(migrate_all=False):
    """Migrate local Telegram photos to GDrive, organized by group."""
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    root_id = find_or_create_root()  # ZAWG_SITES_ROOT under parent folder
    
    print(f"\n📸 Migration started → {root_id}")
    print("=" * 60)
    
    # Get all sites with photos (organized by site, not group)
    group_stats = cur.execute("""
        SELECT 
            COALESCE(s.name, 'Unknown') AS site_name,
            s.code AS site_code,
            COUNT(*) as total_photos,
            SUM(CASE WHEN p.keep=1 THEN 1 ELSE 0 END) as graded_kept
        FROM photos p 
        LEFT JOIN sites s ON p.site_id = s.id
        GROUP BY s.name, s.code 
        ORDER BY total_photos DESC
    """).fetchall()
    
    groups_migrated = 0
    
    for site_name, site_code, total_photos, graded_kept in group_stats:
        print(f"\n📁 Site '{site_name} ({site_code})' → {total_photos} photos ({graded_kept} graded)")
        
        # Create GDrive folder for this site
        safe_folder = safe_name_for_drive(site_code) + "_SITE"
        folder_id = ensure_folder(root_id, safe_folder)
        print(f"   📂 GDrive: {folder_id}")
        
        # Get all photos from the 'photos' table linked to this site
        if migrate_all:
            photo_files = cur.execute("""
                SELECT p.id, p.path, p.keep 
                FROM photos p
                JOIN sites s ON p.site_id = s.id
                WHERE s.code = ?
                ORDER BY p.graded_at DESC
            """, (site_code,)).fetchall()
        else:
            photo_files = cur.execute("""
                SELECT p.id, p.path, p.keep 
                FROM photos p
                JOIN sites s ON p.site_id = s.id
                WHERE s.code = ? AND p.keep = 1
                ORDER BY p.graded_at DESC
            """, (site_code,)).fetchall()
        
        print(f"   📋 Migrating {len(photo_files)} files...")
        uploaded = 0
        
        for photo_id, fpath, kept in photo_files:
            if not os.path.exists(fpath):
                continue
            
            # Build filename with timestamp prefix and keep score
            fname = f"{photo_id}_score{kept}.jpg"
            
            resp = upload_photo_to_drive(fpath, folder_id, fname)
            if resp:
                uploaded += 1
        
        print(f"   ✅ Uploaded {uploaded}/{len(photo_files)} from '{site_name} ({site_code})'")
        groups_migrated += (1 if uploaded > 0 else 0)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Migration complete!")
    print(f"   Groups migrated: {groups_migrated}")
    print(f"   Root folder ID: {root_id}")
    print(f"   Browse at: https://drive.google.com/drive/folders/{root_id}\n")

# ─── Update API config to use GDrive URLs ───
def update_api_for_gdrive():
    """Update the FastAPI pipeline/api.py to serve photos from Drive instead of disk."""
    
    api_py_path = r"C:\Users\user\Desktop\hermes data\zawg-portfolio\pipeline\api.py"
    
    if not os.path.exists(api_py_path):
        print(f"⚠️ API file not found, skipping update")
        return
    
    with open(api_py_path) as f:
        content = f.read()
    
    # Replace local photo path serving with GDrive proxy logic
    old_photo_url = 'r"C:\\Users\\user\\Desktop\\hermes data\\zawg-portfolio\\pipeline\\photos"'
    if old_photo_url in content:
        new_logic = '''# ─── Google Drive Photo Serving ───
# All photos are now uploaded to GDrive. Serve via proxy endpoint.

GDRIVE_PARENT_ID = "1CH7NkMKoBejGpgLvVeaD4FKIfJFnZm0V"  # ZAWG SITES root
PHOTOS_ROOT_PARENT = None  # Will be discovered dynamically at startup

def get_drive_photo_url(drive_file_id):
    """Convert a GDrive file ID to a direct download URL."""
    if drive_file_id:
        return f"https://drive.google.com/thumbnail?id={drive_file_id}&sz=w1024"  # thumbnail format for speed
    return None

def media_url(relative_path):
    """Get the full media URL for photos - use Drive proxy."""
    if relative_path.lower().startswith('http') or '/pipe/' in relative_path:
        return relative_path  # Already a URL
    
    # Extract file_id from original path and convert
    filepath = relative_path
    if 'pipeline/data/photos' in filepath:
       filename = os.path.basename(filepath)
        
        # Look up the corresponding Drive folder from DB mapping
        
        # Simplified for API: construct thumbnail URL directly
        return '/pipe/api/drive-proxy/' + filename
    
    return relative_path'''
        
        content = content.replace(old_photo_url, new_logic.strip())
        print(f"✅ Updated api.py for GDrive serving ✅")

# ─── Main execution function ───
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else '--migrate-all'
    
    if mode == '--update-api':
        update_api_for_gdrive()
    elif mode == '--migrate-all':
        migrate_existing_photos(migrate_all=True)
        update_api_for_gdrive()
    else:
        print("❌ Usage: python tele_photo_to_drive.py --migrate-all [--update-api]")
