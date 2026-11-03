# -*- coding: utf-8 -*-
import math
import os

from common import read_json, write_json

REQUIRED = {
    "prepare": ["arm_params.json", "gear_params.json", "gear_files_report.md"],
    "arm": ["arm_result.json", "arm_summary.md", "arm_figures.png"],
    "gear": ["gear_result.json", "gear_per_position.csv", "gear_per_position_summary.csv", "gear_damage_position.md"],
    "compare": ["compare_result.json", "compare_table.csv", "compare_conclusion.md"],
    "report": ["综合校核报告.md", "report_summary.json"],
}


def _rel(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def gate(out, stage):
    checks = []

    def add(name, ok, evidence):
        checks.append(dict(name=name, status="PASS" if ok else "FAIL", evidence=evidence))

    for f in REQUIRED[stage]:
        p = os.path.join(out, f)
        ok = os.path.isfile(p) and os.path.getsize(p) > 0
        add("文件存在且非空: " + f, ok, p if ok else "缺失或为空")

    if stage == "arm" and os.path.isfile(os.path.join(out, "arm_result.json")):
        r = read_json(os.path.join(out, "arm_result.json"))
        p = read_json(os.path.join(out, "arm_params.json"))
        add("Life、Teq 为正的有限数", all(isinstance(r[k], (int, float)) and math.isfinite(r[k]) and r[k] > 0 for k in ("Life_h", "Teq_Nm")),
            "Life=%s Teq=%s" % (r["Life_h"], r["Teq_Nm"]))
        add("T_total = 6 x Ts", _rel(r["T_total_s"], 6 * r["Ts_s"]), "T_total=%s Ts=%s" % (r["T_total_s"], r["Ts_s"]))
        add("omega_max 与输入转速一致", _rel(r["omega_max"], p["v_max_rpm"] * 2 * math.pi / 60), "omega_max=%s" % r["omega_max"])
        add("峰值扭矩与扭矩范围一致", _rel(r["peak_torque_Nm"], max(abs(r["torque_min_Nm"]), abs(r["torque_max_Nm"]))), "peak=%s" % r["peak_torque_Nm"])
    if stage == "gear" and os.path.isfile(os.path.join(out, "gear_result.json")):
        g = read_json(os.path.join(out, "gear_result.json"))
        pr = g["params"]
        add("D_allow = TR^M x NR", _rel(g["D_allow"], (pr["TR"] ** pr["M"]) * pr["NR"]), "D_allow=%s" % g["D_allow"])
        add("PASS+FAIL = 关节数", g["n_pass"] + g["n_fail"] == g["n_joint"], "%d+%d=%d" % (g["n_pass"], g["n_fail"], g["n_joint"]))
        bad = [j for j in g["per_joint"] if (j["verdict"] == "PASS") != (j["max_budget_utilization"] <= 1)]
        add("每关节判定与最严苛位置 U 一致(U<=1 为 PASS)", not bad, "不一致关节: %s" % [(j["leg"], j["joint"]) for j in bad])
        add("关节数 = 12(缺失关节须说明)", g["n_joint"] == 12, "n_joint=%d" % g["n_joint"])
    if stage == "compare" and os.path.isfile(os.path.join(out, "compare_result.json")):
        c = read_json(os.path.join(out, "compare_result.json"))
        g = read_json(os.path.join(out, "gear_result.json"))
        add("D1 为正的有限数", math.isfinite(c["D1"]) and c["D1"] > 0, "D1=%s" % c["D1"])
        add("对比行数 = 齿轮关节数", c["n_joint"] == g["n_joint"], "%d vs %d" % (c["n_joint"], g["n_joint"]))
        add("按 D2÷D1 降序", all(c["rows"][i]["ratio"] >= c["rows"][i + 1]["ratio"] for i in range(len(c["rows"]) - 1)), "max=%s" % c["max_ratio"])
    if stage == "report":
        txt = open(os.path.join(out, "综合校核报告.md"), encoding="utf-8").read() if os.path.isfile(os.path.join(out, "综合校核报告.md")) else ""
        g = read_json(os.path.join(out, "gear_result.json"))
        for j in g["per_joint"]:
            if j["verdict"] == "FAIL":
                add("FAIL 关节已列入报告: %s_%s" % (j["leg"], j["joint"]), ("%s_%s" % (j["leg"], j["joint"])) in txt, "报告文本匹配")
        add("报告含总体判定", "## 总体判定" in txt, "章节检查")

    n_fail = sum(1 for c in checks if c["status"] == "FAIL")
    res = dict(stage=stage, passed=(n_fail == 0), n_fail=n_fail, checks=checks)
    write_json(os.path.join(out, "gate_%s.json" % stage), res)
    return res
