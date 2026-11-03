# -*- coding: utf-8 -*-
import hashlib
import os
import re
import subprocess
import sys

ROOT = r"D:\7_tool\1_Comprehensive\joint-fatigue-life-check"
PY = sys.executable
results = []


def rd(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def tables(text, title):
    m = re.search(r"^## %s\s*\n(.*?)(?=^## |\Z)" % re.escape(title), text, re.S | re.M)
    rows = []
    if m:
        for ln in m.group(1).splitlines():
            if ln.strip().startswith("|"):
                c = [x.strip() for x in ln.strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", x) for x in c if x):
                    rows.append(c)
    return rows[1:]


def rec(no, name, ok, evidence):
    results.append((no, name, ok, evidence))


all_files = []
for b, d, fs in os.walk(ROOT):
    d[:] = [x for x in d if x != "__pycache__"]
    for f in fs:
        all_files.append(os.path.join(b, f))
rel = lambda p: os.path.relpath(p, ROOT).replace("\\", "/")

# 1 完整性
plan = rd("Plan.md")
aa_ids = [r[0] for r in tables(plan, "活动节点")]
ca_ids = [r[0] for r in tables(plan, "检查节点")]
miss = []
for f in ["charter.md", "Plan.md", "Manifesto.md", "Identity.md", "source.md"]:
    if not os.path.isfile(os.path.join(ROOT, f)):
        miss.append(f)
for a in aa_ids:
    dirs = [d for d in os.listdir(os.path.join(ROOT, "AAList")) if d.startswith(a + "-")]
    if len(dirs) != 1:
        miss.append("AAList/" + a)
        continue
    for f in ["Identity.md", "Plan.md", "AAInputCheckList.md", "AAOutputCheckList.md", "Tools/tool.md"]:
        if not os.path.isfile(os.path.join(ROOT, "AAList", dirs[0], f)):
            miss.append("AAList/%s/%s" % (dirs[0], f))
for c in ca_ids:
    dirs = [d for d in os.listdir(os.path.join(ROOT, "CAList")) if d.startswith(c + "-")]
    if len(dirs) != 1:
        miss.append("CAList/" + c)
        continue
    for f in ["Identity.md", "Checklist.md"]:
        if not os.path.isfile(os.path.join(ROOT, "CAList", dirs[0], f)):
            miss.append("CAList/%s/%s" % (dirs[0], f))
for f in ["Refs/DataObjects/DataObjects.md", "Refs/Insight/InsightCollection.md", "Refs/Tools/README.md", "Refs/FlowChart/viewer_url.txt"]:
    if not os.path.isfile(os.path.join(ROOT, f)):
        miss.append(f)
if not [f for f in os.listdir(os.path.join(ROOT, "Refs", "Knowledge"))] if os.path.isdir(os.path.join(ROOT, "Refs", "Knowledge")) else True:
    miss.append("Refs/Knowledge/*.md")
flow_dir = os.path.join(ROOT, "Refs", "FlowChart")
flows = [f for f in os.listdir(flow_dir) if f.startswith("flow-") and f.endswith(".html") and os.path.getsize(os.path.join(flow_dir, f)) > 0] if os.path.isdir(flow_dir) else []
vf = os.path.join(flow_dir, "viewer_url.txt")
viewer = open(vf, encoding="utf-8").read().strip() if os.path.isfile(vf) else ""
if not viewer.startswith("https://"):
    miss.append("Refs/FlowChart/viewer_url.txt 未回填在线链接")
empty = [rel(p) for p in all_files if p.endswith((".md", ".txt", ".py", ".json", ".example")) and os.path.getsize(p) == 0]
rec(1, "PA包完整性", not miss and not empty, "AA=%d CA=%d 缺失=%s 空文件=%s 流程图HTML本体=%s 在线链接=%s" % (
    len(aa_ids), len(ca_ids), miss, empty, "已随包" if flows else "未随包(仅在线链接)", viewer or "无"))

# 2 DO
do = rd("Refs/DataObjects/DataObjects.md")
heads = re.findall(r"^## (DO-(\d+)) ", do, re.M)
nums = sorted(int(n) for _, n in heads)
secs = re.split(r"^## DO-", do, flags=re.M)[1:]
bad = []
for s in secs:
    rows = [r for r in tables("## x\n" + s.split("\n", 1)[1], "x")]
    if len(rows) != 10 or any(len(r) < 2 or not r[1] for r in rows):
        bad.append(s.split()[0])
cons = {}
for s in secs:
    did = "DO-" + s.split()[0]
    kv = {r[0]: r[1] for r in tables("## x\n" + s.split("\n", 1)[1], "x")}
    cons[did] = (kv.get("产出方", ""), kv.get("消费方", ""))
orphan = [d for d, (p, c) in cons.items() if not p or not c]
rec(2, "DO合规性", nums == list(range(1, len(nums) + 1)) and not bad and not orphan,
    "DO数=%d 编号连续=%s 要素不全=%s 孤立=%s" % (len(nums), nums == list(range(1, len(nums) + 1)), bad, orphan))

# 3 编排
edges = tables(plan, "边")
nodes = set(aa_ids + ca_ids)
adj = {}
for e in edges:
    adj.setdefault(e[1], set()).add(e[2])
seen, stack = set(), ["AA-01"]
while stack:
    n = stack.pop()
    if n in seen:
        continue
    seen.add(n)
    stack.extend(adj.get(n, ()))
unreach = sorted(nodes - seen)
refs_bad = sorted({x for e in edges for x in e[1:3] if x not in nodes})
loops = [e for e in edges if "↺" in e[4]]
loop_bad = [e[0] for e in loops if not e[6]]
rows_conv = tables(plan, "循环回路收敛规则")
conv_ok = all(r[3].isdigit() and r[4] and r[5] for r in rows_conv) and len(rows_conv) >= 1
loop_edge_ids = {e[0] for e in loops}
conv_edge_ids = set(re.findall(r"E-\d+", " ".join(r[1] for r in rows_conv)))
rec(3, "编排合规性", not unreach and not refs_bad and not loop_bad and conv_ok and loop_edge_ids == conv_edge_ids,
    "节点=%d 边=%d 不可达=%s 悬空引用=%s 回路无上限=%s 收敛表覆盖=%s" % (len(nodes), len(edges), unreach, refs_bad, loop_bad, loop_edge_ids == conv_edge_ids))

# 4 宪章
man = rd("Manifesto.md")
dims = re.findall(r"^## (.+)$", man, re.M)
items = re.findall(r"^### (M-\d+) (.+)$", man, re.M)
blocks = re.split(r"^### ", man, flags=re.M)[1:]
incomplete = [b.split()[0] for b in blocks if not all(k in b for k in ("- 规则:", "- 触发场景:", "- 违反后果:"))]
titles = [t for _, t in items]
rec(4, "宪章合规性", dims == ["价值取向", "质量底线", "协作契约", "安全红线"] and not incomplete and len(set(titles)) == len(titles),
    "维度=%s 原则数=%d 缺规则/场景/后果=%s 标题重复=%s" % (dims, len(items), incomplete, len(titles) != len(set(titles))))

# 5 工具
tool_files = sorted(f for f in os.listdir(os.path.join(ROOT, "Refs", "Tools")) if re.fullmatch(r"T-\d+\.md", f))
tool_ids = {f[:-3] for f in tool_files}
used = set()
miss_tool = []
for a in os.listdir(os.path.join(ROOT, "AAList")):
    t = rd("AAList/%s/Tools/tool.md" % a)
    for tid in re.findall(r"T-\d+", t):
        used.add(tid)
        if tid not in tool_ids:
            miss_tool.append("%s->%s" % (a, tid))
vendor_ok = all(os.path.isfile(os.path.join(ROOT, "runtime", "vendor", f)) for f in ("joint_life_core.py", "gear_fatigue_tool.py"))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
v1 = h(os.path.join(ROOT, "runtime", "vendor", "joint_life_core.py"))
v2 = h(os.path.join(ROOT, "runtime", "vendor", "gear_fatigue_tool.py"))
src = rd("source.md")
hash_ok = v1 in src and v2 in src
rec(5, "工具合规性(薄封装)", not miss_tool and vendor_ok and hash_ok,
    "tool_spec=%d AA引用缺失=%s vendor与source.md哈希一致=%s" % (len(tool_ids), miss_tool, hash_ok))

# 6 知识
kdir = os.path.join(ROOT, "Refs", "Knowledge")
kfiles = sorted(os.listdir(kdir))
no_decl = [f for f in kfiles if "边界声明" not in open(os.path.join(kdir, f), encoding="utf-8").read()]
rec(6, "知识合规性", len(kfiles) >= 1 and not no_decl, "知识文件=%s 缺边界声明=%s" % (kfiles, no_decl))

# 7 凭据
r = subprocess.run([PY, os.path.join(ROOT, "runtime", "scan_credentials.py"), ROOT], capture_output=True, text=True, encoding="utf-8")
cfg = [rel(p) for p in all_files if os.path.basename(p).startswith("config") and not p.endswith(".example")]
rec(7, "凭据零入包", r.returncode == 0 and not cfg, "%s 非模板config=%s" % (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?", cfg))

# 8 CA 检查(CA-02 蓝图 + CA-03 文件)
SELF_OUTPUT = "release/验收报告.md"
ph = [rel(p) for p in all_files if p.endswith(".md") and rel(p) != SELF_OUTPUT and re.search(r"⏳|TODO|\{[^}]*占位[^}]*\}", open(p, encoding="utf-8").read())]
abs_paths = [rel(p) for p in all_files if p.endswith(".md") and re.search(r"[A-Za-z]:\\|/app/workspace", open(p, encoding="utf-8").read())
             and not rel(p).startswith(("Refs/Tools/", "AAList/")) and rel(p) not in ("README.md",)]
ids_in_plan = set(aa_ids + ca_ids)
dirs_ids = {d.split("-")[0] + "-" + d.split("-")[1] for d in os.listdir(os.path.join(ROOT, "AAList")) + os.listdir(os.path.join(ROOT, "CAList"))}
rec(8, "CA检查通过", not ph and ids_in_plan == dirs_ids,
    "含未完成标记的文件(不含本报告自身)=%s 节点编号三处一致=%s" % (ph, ids_in_plan == dirs_ids))

# 9 发布物料
mat = rd("release/L5登记物料.md")
need = ["## 一句话能力描述", "## 参赛/发布背景", "## L5 建议节点", "## 技能清单"]
rec(9, "发布物料齐备", all(n in mat for n in need) and "未确认" in mat, "四要素齐全=%s L5节点如实标注未确认=%s" % (all(n in mat for n in need), "未确认" in mat))

L = ["# 验收报告", "", "| # | 验收项 | 结果 | 证据 |", "|---|---|---|---|"]
for no, name, ok, ev in results:
    L.append("| %d | %s | %s | %s |" % (no, name, "PASS" if ok else "FAIL", ev.replace("|", "/")))
L += ["", "总计: %d / 9 项 PASS" % sum(1 for r in results if r[2]), ""]
report = "\n".join(L)
os.makedirs(os.path.join(ROOT, "release"), exist_ok=True)
with open(os.path.join(ROOT, "release", "验收报告.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(report + "\n")
print(report)
sys.exit(0 if all(r[2] for r in results) else 1)
