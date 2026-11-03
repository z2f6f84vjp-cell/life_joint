# -*- coding: utf-8 -*-
"""扫描目录中的凭据实值。命中时只输出文件与行号,不输出内容。用法: python scan_credentials.py <目录>"""
import os
import re
import sys

PATTERNS = [
    re.compile(r"(?i)\b(token|password|passwd|secret|api[_-]?key|authorization)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-.=+/]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-.=]{16,}"),
]
SKIP_EXT = {".png", ".jpg", ".zip", ".pyc", ".pdf"}


def scan(root):
    hits = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if os.path.splitext(f)[1].lower() in SKIP_EXT:
                continue
            path = os.path.join(base, f)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    for no, line in enumerate(fh, 1):
                        if any(p.search(line) for p in PATTERNS):
                            hits.append((os.path.relpath(path, root).replace("\\", "/"), no))
            except OSError:
                continue
    return hits


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    found = scan(target)
    for p, n in found:
        print("命中: %s:%d" % (p, n))
    print("凭据扫描: %s" % ("未发现" if not found else "发现 %d 处" % len(found)))
    sys.exit(2 if found else 0)
