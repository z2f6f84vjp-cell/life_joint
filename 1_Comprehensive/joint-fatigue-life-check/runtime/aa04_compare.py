# -*- coding: utf-8 -*-
import csv
import math
import os

from common import PAError, finite, read_json, write_json, write_text

DEFAULT_P = 6.61


def run_compare(out, p=DEFAULT_P):
    if not (finite(p) and p > 0):
        raise PAError("对比用寿命指数 p 必须是 >0 的有限数字,当前: %r" % (p,))
    arm = read_json(os.path.join(out, "arm_result.json"))
    gear = read_json(os.path.join(out, "gear_result.json"))

    d1 = (arm["peak_torque_Nm"] ** p) * arm["cycles"] * 0.5
    if not (finite(d1) and d1 > 0):
        raise PAError("D1 不是正的有限数(D1=%r),无法对比" % (d1,))

    rows = []
    for j in gear["per_joint"]:
        teq2, mesh2 = j["worst_damage_equiv_torque_Nm"], j["worst_mesh_3000h"]
        d2 = (teq2 ** p) * mesh2
        ratio = d2 / d1
        rows.append(dict(leg=j["leg"], joint=j["joint"], teq2=teq2, mesh2=mesh2, d2=d2, ratio=ratio,
                         dominant="gear" if ratio > 1 else "arm"))
    rows.sort(key=lambda r: -r["ratio"])
    n_gear = sum(1 for r in rows if r["dominant"] == "gear")

    with open(os.path.join(out, "compare_table.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["leg", "joint", "teq2_Nm", "mesh2_3000h", "D2", "D2_over_D1", "dominant"])
        for r in rows:
            w.writerow([r["leg"], r["joint"], r["teq2"], r["mesh2"], r["d2"], r["ratio"], r["dominant"]])

    top = rows[0]
    result = dict(p=p, peak_torque1_Nm=arm["peak_torque_Nm"], cycles1=arm["cycles"], D1=d1, n_joint=len(rows),
                  n_gear_dominant=n_gear, n_arm_dominant=len(rows) - n_gear,
                  max_ratio=top["ratio"], max_ratio_joint="%s_%s" % (top["leg"], top["joint"]), rows=rows)
    write_json(os.path.join(out, "compare_result.json"), result)
    write_text(os.path.join(out, "compare_conclusion.md"),
               "# 跨模块伪损伤对比\n\n- 对比用寿命指数 p = %g\n- D1 = (峰值扭矩1 %.3f)^p x 循环次数1 %.0f x 0.5 = %.6e\n"
               "- 齿轮损伤超过摆臂基准(D2÷D1>1)的关节: %d / %d\n- 最大比值: %s_%s = %.3f\n\n"
               "说明: D1 是整体基准,不区分关节;D2÷D1>1 只表示齿轮损伤超过摆臂模型基准,不等同于校核失败,"
               "失败以齿轮校核的 PASS/FAIL 为准。\n"
               % (p, arm["peak_torque_Nm"], arm["cycles"], d1, n_gear, len(rows), top["leg"], top["joint"], top["ratio"]))
    return result
