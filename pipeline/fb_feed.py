#!/usr/bin/env python3
"""Fetch the latest 10 posts from the Zaw G FB page -> data/fb_feed.json (cached for the site)."""
import json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS = r"C:\Users\user\Desktop\hermes data\fb-graph-api\tokens.json"
PAGE_ID = "310908306475419"  # Zaw G Design & Construction
LIMIT = 10


def main():
    token = json.load(open(TOKENS))["pages"][PAGE_ID]["page_token"]
    url = (f"https://graph.facebook.com/v21.0/{PAGE_ID}/posts"
           f"?fields=message,created_time,full_picture,permalink_url,attachments{{media_type}}"
           f"&limit={LIMIT}&access_token={token}")
    data = json.load(urllib.request.urlopen(url, timeout=25))
    posts = []
    for p in data.get("data", []):
        att = (p.get("attachments", {}).get("data") or [{}])[0]
        posts.append({
            "id": p["id"],
            "date": p["created_time"][:10],
            "text": (p.get("message") or "").strip(),
            "image": p.get("full_picture"),
            "link": p.get("permalink_url"),
            "media": att.get("media_type", "status"),
        })
    out = os.path.join(HERE, "data", "fb_feed.json")
    json.dump(posts, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"fb_feed.json updated: {len(posts)} posts, latest {posts[0]['date'] if posts else '-'}")


if __name__ == "__main__":
    main()
