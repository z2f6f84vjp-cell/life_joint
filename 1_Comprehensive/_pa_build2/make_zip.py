# -*- coding: utf-8 -*-
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = r"D:\7_tool\1_Comprehensive\joint-fatigue-life-check"
ZIP = r"D:\7_tool\1_Comprehensive\joint-fatigue-life-check.zip"
NAME = os.path.basename(ROOT)

n = 0
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "out"))
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            z.write(p, (NAME + "/" + os.path.relpath(p, ROOT)).replace("\\", "/"))
            n += 1
print("zip files:", n, "size:", os.path.getsize(ZIP))
with open(ZIP, "rb") as fh:
    print("zip sha256:", hashlib.sha256(fh.read()).hexdigest())

tmp = tempfile.mkdtemp(prefix="pa_zipcheck_")
try:
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        z.extractall(tmp)
    print("testzip:", "OK" if bad is None else "BAD " + bad)
    pkg = os.path.join(tmp, NAME)
    env = dict(os.environ, PYTHONUTF8="1")
    r = subprocess.run([sys.executable, os.path.join(pkg, "runtime", "run_pa.py"), "selftest"],
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=900)
    tail = [l for l in r.stdout.splitlines() if l.startswith("selftest:")]
    print("解压副本 selftest 退出码:", r.returncode, tail)
    c = subprocess.run([sys.executable, os.path.join(pkg, "runtime", "scan_credentials.py"), pkg],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    print(c.stdout.strip().splitlines()[-1] if c.stdout.strip() else "扫描无输出")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
