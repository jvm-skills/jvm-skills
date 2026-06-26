#!/usr/bin/env python3
import subprocess, base64, sys, json
# args: login then repo|path ...
login = sys.argv[1]
specs = sys.argv[2:]
def fetch(repo, path):
    o = subprocess.run(["gh","api",f"repos/{login}/{repo}/contents/{path}","--jq",".content"],
                       capture_output=True, text=True, timeout=40)
    if o.returncode != 0: return None
    try: return base64.b64decode(o.stdout).decode("utf-8","replace")
    except Exception: return None
HEAD = int(__import__("os").environ.get("HEAD","45"))
for spec in specs:
    repo, path = spec.split("|", 1)
    body = fetch(repo, path)
    print("="*70)
    if body is None:
        print(f"### {repo} :: {path}  (FETCH FAILED)"); continue
    n = body.count("\n") + (1 if body and not body.endswith("\n") else 0)
    print(f"### {repo} :: {path}  ({n} lines)")
    print("-"*70)
    print("\n".join(body.splitlines()[:HEAD]))
