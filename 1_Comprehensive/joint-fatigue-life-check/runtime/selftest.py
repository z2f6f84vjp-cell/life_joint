# -*- coding: utf-8 -*-
"""自检: 用合成数据跑通整条流程,并用独立的纯 Python 公式复算齿轮结果做数值回归。"""
import math
import os
import shutil
import tempfile

from common import PAError, load_vendor, read_json

LEGS = ["FL", "FR", "RL", "RR"]
JOINTS = ["hip", "thigh", "calf"]
TORQUES = [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0, 30.0]
POSITIONS = [float(x) for x in range(-20, 21, 5)]
HEAVY = ("RR", "calf")


def synth_z(leg, joint, pi, ti):
    if TORQUES[ti] == 0.0:
        return 0.0
    base = 0.02 * (1 + (LEGS.index(leg) + JOINTS.index(joint) + pi + ti) % 4)
    if pi == 0 and ti == 6:
        return 0.0
    return base * (60.0 if (leg, joint) == HEAVY else 1.0)


def write_dataset(folder):
    for leg in LEGS:
        for joint in JOINTS:
            lines = ["#TITLES", "position," + ",".join(repr(t) for t in TORQUES), "#DATA"]
            for pi, pos in enumerate(POSITIONS):
                lines.append(repr(pos) + "," + ",".join(repr(synth_z(leg, joint, pi, ti)) for ti in range(len(TORQUES))))
            with open(os.path.join(folder, "%s_%s.csv" % (leg, joint)), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lines) + "\n")


def independent_gear(params):
    TR, NR, LH, M, TEETH, SIDE, TW = (params[k] for k in ("TR", "NR", "LH", "M", "TEETH", "SIDE", "TW"))
    K = LH * 3600.0 / TW
    out = {}
    for leg in LEGS:
        for joint in JOINTS:
            best = None
            for pi, pos in enumerate(POSITIONS):
                cyc = dmg = 0.0
                for ti, t in enumerate(TORQUES):
                    z = synth_z(leg, joint, pi, ti)
                    if z <= 0:
                        continue
                    n = z * TEETH / SIDE
                    cyc += n
                    dmg += abs(t) ** M * n
                if cyc <= 0:
                    continue
                u = dmg * K / TR ** M / NR
                if best is None or u > best[0]:
                    best = (u, pos, (dmg / cyc) ** (1 / M), cyc * K)
            out[(leg, joint)] = best
    return out


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def run_selftest():
    from run_pa import main
    results = []

    def check(name, ok, detail=""):
        results.append(ok)
        print("%s  %s %s" % ("PASS" if ok else "FAIL", name, detail))

    tmp = tempfile.mkdtemp(prefix="pa_selftest_")
    try:
        data, out = os.path.join(tmp, "data"), os.path.join(tmp, "out")
        os.makedirs(data)
        write_dataset(data)

        rc = main(["all", "--out", out, "--gear-folder", data])
        check("端到端 all 退出码为 0", rc == 0, "rc=%s" % rc)
        if rc != 0:
            return 1

        arm = read_json(os.path.join(out, "arm_result.json"))
        check("摆臂回归: Life 约 269.3 h", abs(arm["Life_h"] - 269.3) < 0.05, "Life=%.3f" % arm["Life_h"])
        check("摆臂回归: Teq 约 12.428 N·m", abs(arm["Teq_Nm"] - 12.428) < 0.0005, "Teq=%.4f" % arm["Teq_Nm"])
        check("摆臂回归: T_total 约 0.4 s", abs(arm["T_total_s"] - 0.4) < 1e-9, "T=%s" % arm["T_total_s"])

        gear = read_json(os.path.join(out, "gear_result.json"))
        ref = independent_gear(gear["params"])
        bad = []
        for j in gear["per_joint"]:
            u, pos, teq, mesh = ref[(j["leg"], j["joint"])]
            if not (close(j["max_budget_utilization"], u) and close(j["worst_position_deg"], pos)
                    and close(j["worst_damage_equiv_torque_Nm"], teq) and close(j["worst_mesh_3000h"], mesh)):
                bad.append((j["leg"], j["joint"]))
        check("齿轮回归: 12 个关节与独立公式一致", not bad and len(gear["per_joint"]) == 12, "不一致: %s" % bad)
        check("设计内含 FAIL 与 PASS 各至少 1 个", gear["n_fail"] >= 1 and gear["n_pass"] >= 1,
              "PASS=%d FAIL=%d" % (gear["n_pass"], gear["n_fail"]))

        cmp_ = read_json(os.path.join(out, "compare_result.json"))
        d1 = arm["peak_torque_Nm"] ** 6.61 * arm["cycles"] * 0.5
        check("对比回归: D1 与独立公式一致", close(cmp_["D1"], d1), "D1=%.6e" % cmp_["D1"])
        report = open(os.path.join(out, "综合校核报告.md"), encoding="utf-8").read()
        check("报告列出 FAIL 关节 RR_calf", "RR_calf" in report and "存在 FAIL" in report)

        os.remove(os.path.join(data, "FL_hip.csv"))
        rc = main(["prepare", "--out", os.path.join(tmp, "out2"), "--gear-folder", data])
        check("缺少 CSV 时拒绝执行(退出码 2)", rc == 2, "rc=%s" % rc)
        rc = main(["prepare", "--out", os.path.join(tmp, "out3"), "--gear-folder", data, "--arm", "L=-1"])
        check("非法参数时拒绝执行(退出码 2)", rc == 2, "rc=%s" % rc)
        write_dataset(data)
        rc = main(["compare", "--out", out, "--p", "0"])
        check("对比指数 p=0 时拒绝执行(退出码 2)", rc == 2, "rc=%s" % rc)
        rc = main(["prepare", "--out", out, "--gear-folder", data, "--arm", "v_max_rpm=150"])
        check("改参数后重新 prepare 成功", rc == 0, "rc=%s" % rc)
        stale = [f for f in ("arm_result.json", "gear_result.json", "compare_result.json", "综合校核报告.md", "gate_arm.json")
                 if os.path.exists(os.path.join(out, f))]
        check("重新 prepare 清除旧的下游结果", not stale, "残留: %s" % stale)
        rc = main(["compare", "--out", out])
        check("上游结果被清除后 compare 拒绝执行(退出码 2)", rc == 2, "rc=%s" % rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("selftest: %d/%d 通过" % (sum(results), len(results)))
    return 0 if all(results) else 1
