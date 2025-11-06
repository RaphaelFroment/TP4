import os, sys

GOOD = os.environ.get("GOOD_HASH")
BAD  = os.environ.get("BAD_HASH")

if not GOOD or not BAD:
    print("ERROR: You must set GOOD_HASH and BAD_HASH in the environment.")
    sys.exit(2)

print(f"Starting bisect: good={GOOD}  bad={BAD}")

rc = os.system(f"git bisect start {BAD} {GOOD}")
if rc != 0:
    print("git bisect start failed")
    sys.exit(1)

try:
    rc = os.system('git bisect run bash -lc "python manage.py test -q"')
    if rc != 0:
        print("git bisect run finished (non-zero exit). Check log above for the first bad commit.")
finally:
    os.system("git bisect reset")
