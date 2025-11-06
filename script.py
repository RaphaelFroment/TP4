import os, sys, subprocess, shlex

def run(cmd, check=True, capture=False):
    print(f"+ {cmd}")
    res = subprocess.run(shlex.split(cmd), text=True,
                         stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.STDOUT if capture else None)
    if capture:
        return res.stdout.strip(), res.returncode
    if check and res.returncode != 0:
        sys.exit(res.returncode)
    return "", res.returncode

GOOD = os.environ.get("GOOD_HASH")
BAD  = os.environ.get("BAD_HASH")

if not BAD:
    out, _ = run("git rev-parse HEAD", capture=True)
    BAD = out

if not GOOD:
 
    out, code = run("git rev-parse origin/main", capture=True)
    if code != 0 or not out:
        print("ERROR: Set GOOD_HASH or ensure origin/main exists.")
        sys.exit(2)
    GOOD = out

print(f"Requested GOOD={GOOD}  BAD={BAD}")

_, code = run(f"git merge-base --is-ancestor {GOOD} {BAD}", check=False)
if code != 0:
    mb, _ = run(f"git merge-base {GOOD} {BAD}", capture=True)
    if not mb:
        print("ERROR: No merge-base found; are these from unrelated histories?")
        sys.exit(2)
    print(f"GOOD is not ancestor of BAD. Using merge-base as GOOD: {mb}")
    GOOD = mb

run(f"git bisect start {BAD} {GOOD}")

try:
    cmd = 'bash -lc "python manage.py test -q"'
    
    _, rc = run(f"git bisect run {cmd}", check=False)
    print("git bisect run finished with code:", rc)
finally:
    run("git bisect reset", check=False)
