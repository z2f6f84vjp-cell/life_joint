# -*- coding: utf-8 -*-
import csv
import os

from common import PAError, load_vendor, read_json, sha256_file, write_json, write_text

POS_HEADERS = ["leg", "joint", "position_deg", "mesh_1side_test", "mesh_1side_3000h",
               "pseudo_damage_3000h", "damage_equiv_torque_Nm", "max_torque_Nm",
               "equiv_mesh_at_rated", "budget_utilization", "safety_factor",
               "supported_hours", "verdict"]
SUM_HEADERS = ["leg", "joint", "nonzero_positions", "worst_position_deg",
               "worst_damage_equiv_torque_Nm", "worst_mesh_3000h", "max_budget_utilization",
               "min_safety_factor", "supported_hours", "positions_failing", "verdict"]


def run_gear(out):
    _, gear = load_vendor()
    meta = read_json(os.path.join(out, "gear_params.json"))
    folder, params = meta["gear_folder"], meta["params"]
    parsed, matched, missing, _, need = gear.load_folder(folder)
    if missing:
        raise PAError("齿轮数据文件夹已变化,缺少: %s" % ", ".join(missing))
    for k in need:
        if sha256_file(matched[k]) != meta["files"][k]["sha256"]:
            raise PAError("%s 在 AA-01 之后被修改,请重新执行 prepare" % os.path.basename(matched[k]))

    res = gear.compute_all(parsed, params)
    per_joint = res["per_joint"]
    if not per_joint:
        raise PAError("所有关节均无非零位置,无法校核")

    with open(os.path.join(out, "gear_per_position.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=POS_HEADERS)
        w.writeheader()
        for p in res["per_pos_all"]:
            w.writerow({k: p[k] for k in POS_HEADERS})
    with open(os.path.join(out, "gear_per_position_summary.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(SUM_HEADERS)
        for j in per_joint:
            w.writerow([j[k] for k in SUM_HEADERS])

    lines = ["# 各关节损伤风险位置(累积占比达 80%)", ""]
    for j in per_joint:
        positions, risk = gear.augment_with_pct_and_risk(j)
        rows = sorted([p for p in positions if p["position_deg"] in risk], key=lambda p: -p["_pct"])
        lines += ["## %s %s  (%d 个风险位置 / %d 个非零位置)" % (j["leg"], j["joint"], len(rows), len(positions)), "",
                  "| 位置(°) | 损伤占比 | U | 判定 |", "|---|---|---|---|"]
        lines += ["| %.2f | %.2f%% | %.4f | %s |" % (p["position_deg"], p["_pct"], p["budget_utilization"], p["verdict"])
                  for p in rows]
        lines.append("")
    write_text(os.path.join(out, "gear_damage_position.md"), "\n".join(lines))

    slim = [{k: v for k, v in j.items() if k != "positions"} for j in per_joint]
    result = dict(D_allow=res["D_allow"], K=res["K"], params=params, n_joint=len(slim),
                  n_pass=sum(1 for j in slim if j["verdict"] == "PASS"),
                  n_fail=sum(1 for j in slim if j["verdict"] == "FAIL"),
                  n_position_rows=len(res["per_pos_all"]), per_joint=slim)
    write_json(os.path.join(out, "gear_result.json"), result)
    return result
