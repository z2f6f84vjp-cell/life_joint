# -*- coding: utf-8 -*-
import hashlib
import json
import math
import os
import sys

RUNTIME = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(RUNTIME)
VENDOR = os.path.join(RUNTIME, "vendor")

ARM_KEYS = ["v_max_rpm", "theta_max_deg", "theta_start_deg", "L", "m_arm", "m_load", "g",
            "inertia_mode", "custom_I", "life_exponent", "C_rated", "N_ref", "L10_ref"]
GEAR_KEYS = ["TR", "NR", "LH", "M", "TEETH", "SIDE", "TW"]
DOWNSTREAM = ["arm_result.json", "arm_summary.md", "arm_figures.png", "gear_result.json",
              "gear_per_position.csv", "gear_per_position_summary.csv", "gear_damage_position.md",
              "compare_result.json", "compare_table.csv", "compare_conclusion.md",
              "综合校核报告.md", "report_summary.json", "gate_prepare.json", "gate_arm.json",
              "gate_gear.json", "gate_compare.json", "gate_report.json"]
INERTIA = {"anker": "安克 (0.1828+I_load)", "sanhua": "三花 (0.095+I_load)",
           "theory": "理论 (I_arm+I_load)", "custom": "自定义"}

_BASE = dict(v_max_rpm=100.0, theta_max_deg=120.0, theta_start_deg=-150.0, L=0.3, m_arm=5.176,
             m_load=2.0, g=9.80, inertia_mode=INERTIA["anker"], custom_I=0.0,
             life_exponent=10 / 3, C_rated=6.03, N_ref=100.0, L10_ref=3000.0)
PRESETS = {
    "anker": dict(_BASE),
    "sanhua": dict(_BASE, m_arm=2.7, m_load=2.65, inertia_mode=INERTIA["sanhua"]),
    "high": dict(_BASE, v_max_rpm=150.0),
}


class PAError(Exception):
    pass


def load_vendor():
    os.environ.setdefault("MPLBACKEND", "Agg")
    if VENDOR not in sys.path:
        sys.path.insert(0, VENDOR)
    try:
        import joint_life_core as jl
        import gear_fatigue_tool as gear
    except ImportError as e:
        raise PAError("缺少运行依赖: %s。需要 Python3、numpy>=2.0、matplotlib、tkinter(无需显示器)" % e)
    return jl, gear


def _default(o):
    if hasattr(o, "item"):
        return o.item()
    raise TypeError("无法序列化 %r" % type(o))


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        o = o.item()
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(_clean(obj), f, ensure_ascii=False, indent=2, default=_default, allow_nan=False)


def read_json(path):
    if not os.path.isfile(path):
        raise PAError("缺少上游文件: %s (请先完成上游步骤)" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip("\n") + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)
