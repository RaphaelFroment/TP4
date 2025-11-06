# myscript.py
import os, sys, subprocess, shlex

TEST_CMD = 'bash -lc "python manage.py test -q"'   

def run(cmd, check=True, capture=False):
    print("+", cmd)
    res = subprocess.run(shlex.split(cmd), text=True,
                         stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.STDOUT if capture else None)
    if capture:
        return res.stdout.strip(), res.returncode
    if check and res.returncode != 0:
        sys.exit(res.returncode)
    return "", res.returncode

def test_commit(sha):
    run(f"git checkout -f {sha}")
    print(f"== Testing {sha} ==")
    out, code = run(TEST_CMD, check=False, capture=False)
    return code

GOOD = os.environ.get("GOOD_HASH")
BAD  = os.environ.get("BAD_HASH")

if not BAD:
    BAD, _ = run("git rev-parse HEAD", capture=True)
if not GOOD:
    GOOD, _ = run("git rev-parse origin/main", capture=True)

print(f"Requested GOOD={GOOD}  BAD={BAD}")

run("git fetch --all --tags --prune")

_, code = run(f"git merge-base --is-ancestor {GOOD} {BAD}", check=False)
if code != 0:
    MB, _ = run(f"git merge-base {GOOD} {BAD}", capture=True)
    print(f"GOOD is not ancestor of BAD. Using merge-base as candidate GOOD: {MB}")
    GOOD = MB

if GOOD == BAD:
    print("GOOD and BAD are the same commit. Searching for the nearest passing ancestor...")
    START, _ = run("git rev-parse HEAD", capture=True)
    revs, _ = run(f"git rev-list --first-parent {BAD}", capture=True)
    found = None
    for sha in revs.splitlines()[1:]:  
        code = test_commit(sha)
        if code == 0:
            found = sha
            print(f"Found passing ancestor: {found}")
            break
        elif code == 125:
            print(f"Skipping untestable commit: {sha}")
            continue
        else:
            print(f"Commit {sha} is bad (code {code})")
    if not found:
        print("No passing ancestor found. The bug exists as far back as history scanned.")
        sys.exit(1)
    GOOD = found
    run(f"git checkout -f {BAD}")

run(f"git bisect start {BAD} {GOOD}")
try:
    
    cmd = TEST_CMD
    _, rc = run(f"git bisect run {cmd}", check=False)
    print("git bisect run finished with code:", rc)
finally:
    run("git bisect reset", check=False)
