#!/usr/bin/env python3
"""P2.3 — Grade site photos with local Ollama vision model ($0 API cost).
Usage: python grade_photo.py <image_path> [model]
Returns JSON: {score, keep, reason}
"""
import base64, json, sys, urllib.request

OLLAMA = "http://localhost:11434/api/generate"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "gemma4:12b"

PROMPT = """You are a photo curator for a construction company's client portal.
Grade this site photo. Reply ONLY with valid JSON, no other text:
{"score": <1-10>, "keep": <true/false>, "sharp": <true/false>, "site_related": <true/false>, "reason": "<max 12 words>"}

Scoring guide:
- 8-10: sharp, well-lit, shows construction progress clearly, client-worthy
- 5-7: acceptable but ordinary
- 1-4: blurry, dark, irrelevant, meme/screenshot/document/selfie

AUTO-FILTER RULES — keep = false (regardless of score) if image contains:
• DEMOLITION/RENATION: bricks/walls being broken down, rubble, wrecking debris, demolition crews in action
• CONSTRUCTION JUNK: piles of loose bricks with no structure, scattered construction waste, dirty work surfaces
• BAD CONTENT: memes, text documents, screenshots, selfies, non-site photos, logos/marketing materials

keep = true ONLY if score >= 7 AND site_related AND NOT (demolition OR renovation debris OR construction junk)."""

PROMPT_PORTFOLIO = """You are a curator for a premium architecture portfolio website.
Grade this image. Reply ONLY with valid JSON, no other text:
{"score": <1-10>, "keep": <true/false>, "sharp": <true/false>, "site_related": <true/false>, "reason": "<max 12 words>"}

Scoring guide:
- 8-10: stunning composition, sharp, premium look — architecture, building exterior/interior, or high-quality render
- 5-7: decent but ordinary
- 1-4: blurry, dark, meme, screenshot, document, selfie, text-heavy poster, infographic, collage
site_related = true if it shows a building/structure/interior/render (not text poster/meme/logo).

AUTO-FILTER RULES — keep = false (regardless of score) if image contains:
• DEMOLITION/RENOVATION DEBRIS: bricks/walls being broken down, rubble, wrecking, demolition crews, wall demolition, structural repair with visible wreckage, torn-down walls, piles of broken bricks
• CONSTRUCTION JUNK: scattered construction waste, unorganized messy work sites, dirty surfaces with no visible structure
• BAD CONTENT: memes, text documents, screenshots, selfies, non-site photos, logos/marketing materials

keep = true ONLY if score >= 7 AND site_related AND NOT (demolition OR renovation debris OR construction junk OR bad content)."""

def grade(path: str, mode: str = "site") -> dict:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": MODEL,
        "prompt": PROMPT_PORTFOLIO if mode == "portfolio" else PROMPT,
        "images": [b64],
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    text = resp.get("response", "").strip()
    # extract JSON from response
    start, end = text.find("{"), text.rfind("}")
    if start == -1:
        return {"error": "no JSON", "raw": text[:300]}
    return json.loads(text[start:end + 1])

if __name__ == "__main__":
    result = grade(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
