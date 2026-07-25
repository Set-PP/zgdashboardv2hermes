#!/usr/bin/env python3
"""
Collect design renders from Zaw G Facebook page.
Downloads highest-resolution images from posts, filters for design content.
"""
import json, os, urllib.request, re

HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS_PATH = r"C:\Users\user\Desktop\hermes data\fb-graph-api\tokens.json"
PAGE_ID = "310908306475419"  # Zaw G Design & Construction
OUT_DIR = os.path.join(HERE, "data", "photos", "_design")
LIMIT = 100  # fetch up to 100 posts

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tokens = json.load(open(TOKENS_PATH))
    token = tokens["pages"][PAGE_ID]["page_token"]
    
    # Fetch posts with photos
    url = (f"https://graph.facebook.com/v21.0/{PAGE_ID}/posts"
           f"?fields=id,message,created_time,full_picture,permalink_url,attachments{{media,subattachments}}"
           f"&limit={LIMIT}&access_token={token}")
    
    data = json.load(urllib.request.urlopen(url, timeout=30))
    posts = data.get("data", [])
    print(f"Fetched {len(posts)} posts from Facebook\n")
    
    # Track what we download
    downloaded = 0
    small_skipped = 0
    
    for i, p in enumerate(posts):
        msg = (p.get("message") or "").lower()
        img_url = p.get("full_picture")
        
        if not img_url:
            continue
        
        # Filter: only posts that look like design renders
        # Skip: invoices, ledgers, structural drawings, text-only
        skip_keywords = ['invoice', 'ledger', 'receipt', 'bill', 'payment',
                        'structural', 'column detail', 'cross-section',
                        'floor plan', 'estimate', 'quotation', 'budget']
        if any(kw in msg for kw in skip_keywords):
            continue
        
        # Download image
        date_str = p["created_time"][:10].replace("-", "")
        post_id = p["id"].split("_")[-1]
        fname = f"design_fb_{date_str}_{post_id}.jpg"
        path = os.path.join(OUT_DIR, fname)
        
        if os.path.exists(path):
            print(f"  ⏭️  {fname} (exists)")
            continue
        
        try:
            urllib.request.urlretrieve(img_url, path)
            size_kb = os.path.getsize(path) / 1024
            
            if size_kb < 100:  # Skip tiny images (thumbnails/icons)
                os.remove(path)
                small_skipped += 1
                continue
            
            print(f"  📥 [{i+1}/{len(posts)}] {fname} ({size_kb:.0f} KB) — {msg[:60]}")
            downloaded += 1
            
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
    
    print(f"\n📊 Downloaded: {downloaded} images")
    print(f"   Skipped (small): {small_skipped}")
    
    # Update portfolio table
    if downloaded > 0:
        from db import connect
        con = connect()
        
        # Clear old design entries
        con.execute("DELETE FROM portfolio WHERE category='design'")
        
        for fname in sorted(os.listdir(OUT_DIR)):
            if not fname.endswith('.jpg') and not fname.endswith('.png'):
                continue
            path = os.path.join(OUT_DIR, fname)
            
            # Extract date from filename
            m = re.match(r'design_fb_(\d{8})_(\d+)', fname)
            if not m:
                continue
            date_str = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:8]}"
            months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
            month = months[int(date_str[5:7])-1]
            
            con.execute("""
                INSERT INTO portfolio (category, title, subtitle, path, source, score, created)
                VALUES ('design', ?, ?, ?, 'facebook', 8, ?)
            """, (f"Design Concept · {month} {date_str[:4]}", f"{date_str[:4]} ZAWG DESIGN", path, f"{date_str}T00:00:00+00:00"))
        
        con.commit()
        total = con.execute("SELECT COUNT(*) c FROM portfolio WHERE category='design'").fetchone()['c']
        print(f"  ✅ Portfolio: {total} design entries from Facebook")

if __name__ == '__main__':
    main()
