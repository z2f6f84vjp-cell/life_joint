# -*- coding: utf-8 -*-
import os

from common import read_json, write_json, write_text

TOL_U = 0.9


def fnum(v, nd=3):
    if v is None:
        return "inf"
    a = abs(v)
    return ("%.3e" % v) if (a >= 1e6 or (0 < a < 1e-3)) else ("%.*f" % (nd, v))


def run_report(out):
    arm = read_json(os.path.join(out, "arm_result.json"))
    gear = read_json(os.path.join(out, "gear_result.json"))
    cmp_ = read_json(os.path.join(out, "compare_result.json"))

    joints = gear["per_joint"]
    fails = [j for j in joints if j["verdict"] == "FAIL"]
    near = [j for j in joints if j["verdict"] == "PASS" and j["max_budget_utilization"] >= TOL_U]
    weakest = min(joints, key=lambda j: j["min_safety_factor"] if j["min_safety_factor"] is not None else float("inf"))
    gear_dom = [r for r in cmp_["rows"] if r["dominant"] == "gear"]
    overall = "存在 FAIL 关节(%d/%d)" % (len(fails), len(joints)) if fails else "全部 %d 个关节 PASS" % len(joints)

    L = ["# 关节疲劳寿命综合校核报告", "", "## 总体判定", "", "**%s**" % overall, "",
         "- 摆臂测试寿命 %.1f h,等效扭矩 Teq %.3f N·m,峰值扭矩 %.2f N·m(来源 arm_result.json)"
         % (arm["Life_h"], arm["Teq_Nm"], arm["peak_torque_Nm"]),
         "- 齿轮校核 PASS %d / FAIL %d,D_allow = %s(来源 gear_result.json)" % (gear["n_pass"], gear["n_fail"], fnum(gear["D_allow"])),
         "- 最薄弱关节 %s_%s,SF = %s,U = %.4f" % (weakest["leg"], weakest["joint"], fnum(weakest["min_safety_factor"]), weakest["max_budget_utilization"]),
         "- 跨模块对比(p=%g): 齿轮损伤超过摆臂基准的关节 %d / %d,最大比值 %s = %.3f(来源 compare_result.json)"
         % (cmp_["p"], cmp_["n_gear_dominant"], cmp_["n_joint"], cmp_["max_ratio_joint"], cmp_["max_ratio"]),
         "", "## 风险项", ""]
    L += ["- FAIL: %s_%s, U=%.4f, SF=%s, 最严苛位置 %.2f°" % (j["leg"], j["joint"], j["max_budget_utilization"], fnum(j["min_safety_factor"]), j["worst_position_deg"]) for j in fails] or ["- 无 FAIL 关节"]
    L += ["- 接近预算(U>=%.1f 且仍 PASS): %s_%s, U=%.4f" % (TOL_U, j["leg"], j["joint"], j["max_budget_utilization"]) for j in near]
    L += ["- 齿轮主导(D2÷D1>1): %s_%s, 比值 %.3f" % (r["leg"], r["joint"], r["ratio"]) for r in gear_dom]
    L += ["", "## 各关节明细(按 SF 升序)", "", "| 关节 | 最严苛位置(°) | 等效扭矩(N·m) | U | SF | 支持寿命(h) | 失效位置数 | 判定 |", "|---|---|---|---|---|---|---|---|"]
    for j in sorted(joints, key=lambda j: j["min_safety_factor"] if j["min_safety_factor"] is not None else float("inf")):
        L.append("| %s_%s | %.2f | %.2f | %.4f | %s | %s | %d | %s |" % (
            j["leg"], j["joint"], j["worst_position_deg"], j["worst_damage_equiv_torque_Nm"],
            j["max_budget_utilization"], fnum(j["min_safety_factor"]), fnum(j["supported_hours"]), j["positions_failing"], j["verdict"]))
    L += ["", "## 建议", ""]
    if fails:
        L.append("- 先处理 FAIL 关节: 其最严苛位置的 U 已超过 1,可核对该位置的扭矩分布或额定参数(TR/NR/M)后复算。")
    elif near:
        L.append("- 无 FAIL,但有关节 U 接近预算,建议补充测试或保留裕量。")
    else:
        L.append("- 全部关节有裕量,可按当前参数进入下一阶段。")
    L += ["- 对比结论仅说明损伤来源,不替代 PASS/FAIL 判定。", "", "## 交付文件", ""]
    files = ["arm_params.json", "arm_result.json", "arm_summary.md", "arm_figures.png", "gear_params.json", "gear_files_report.md",
             "gear_result.json", "gear_per_position.csv", "gear_per_position_summary.csv", "gear_damage_position.md",
             "compare_result.json", "compare_table.csv", "compare_conclusion.md"]
    L += ["- %s" % f for f in files if os.path.isfile(os.path.join(out, f))]
    write_text(os.path.join(out, "综合校核报告.md"), "\n".join(L))
    summary = dict(overall=overall, n_fail=len(fails), n_near=len(near), weakest="%s_%s" % (weakest["leg"], weakest["joint"]))
    write_json(os.path.join(out, "report_summary.json"), summary)
    return summary
