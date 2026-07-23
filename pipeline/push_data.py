#!/usr/bin/env python3
"""Push fresh pipeline data (zawg.db + photos) to the VPS after each sync.

Env-gated: does nothing unless VPS_TARGET is set, e.g. in pipeline/.env or the environment:
    VPS_TARGET=ubuntu@1.2.3.4:/home/ubuntu/zawg-portfolio/pipeline/data/
Uses rsync over SSH (delete removed files). Runs at the END of sync_sites.py.
"""
import os, subprocess, sys

def main():
    target = os.environ.get("VPS_TARGET", "").strip()
    if not target:
        return 0                                    # not configured — silent no-op
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data") + "/"
    if not os.path.isdir(src):
        return 0
    r = subprocess.run(["rsync", "-az", "--delete", src, target],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(f"[push_data] rsync failed: {r.stderr.strip()[:300]}", file=sys.stderr)
        return 1
    print(f"[push_data] data pushed -> {target}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
