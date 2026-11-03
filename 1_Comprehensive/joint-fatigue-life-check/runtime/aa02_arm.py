# -*- coding: utf-8 -*-
import math
import os

from common import ARM_KEYS, PAError, load_vendor, read_json, write_json, write_text


def run_arm(out):
    jl, _ = load_vendor()
    import numpy as np
    from matplotlib.figure import Figure

    arm = read_json(os.path.join(out, "arm_params.json"))
    try:
        r = jl.calculate_life(**{k: arm[k] for k in ARM_KEYS})
    except KeyError as e:
        raise PAError("arm_params.json 缺少字段 %s" % e)
    if not (math.isfinite(r["Life"]) and math.isfinite(r["Teq"])):
        raise PAError("摆臂结果发散(Life=%s, Teq=%s),请检查参数取值范围" % (r["Life"], r["Teq"]))

    tt = r["torque_total"]
    result = dict(
        Life_h=float(r["Life"]), Teq_Nm=float(r["Teq"]), T_total_s=float(r["T_total"]), Ts_s=float(r["Ts"]),
        peak_torque_Nm=float(np.max(np.abs(tt))), torque_min_Nm=float(np.min(tt)), torque_max_Nm=float(np.max(tt)),
        fatigue_integral=float(r["fatigue_integral"]), L_val=float(r["L_val"]),
        cycles=float(r["Life"] * 3600.0 / r["T_total"]), I_total=float(r["I_total"]),
        omega_max=float(r["omega_max"]), alpha_max=float(r["alpha_max"]), jerk_max=float(r["jerk_max"]),
        life_exponent=float(r["life_exponent"]), N_ref=float(r["N_ref"]),
    )
    write_json(os.path.join(out, "arm_result.json"), result)
    write_text(os.path.join(out, "arm_summary.md"), "```text" + jl.build_summary(r) + "\n```")
    fig = Figure(figsize=(11, 8), dpi=100)
    jl.create_figures(fig, r)
    fig.savefig(os.path.join(out, "arm_figures.png"))
    return result
