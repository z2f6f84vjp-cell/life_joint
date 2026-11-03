# -*- coding: utf-8 -*-
import os

from common import (ARM_KEYS, DOWNSTREAM, GEAR_KEYS, INERTIA, PRESETS, PAError, finite, load_vendor,
                    sha256_file, write_json, write_text)

ARM_POSITIVE = ["v_max_rpm", "theta_max_deg", "L", "life_exponent", "C_rated", "N_ref", "L10_ref"]


def parse_kv(pairs, keys, kind):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise PAError("--%s 参数格式应为 key=value: %s" % (kind, p))
        k, v = p.split("=", 1)
        k = k.strip()
        if k not in keys:
            raise PAError("未知%s参数 %s,可用: %s" % (kind, k, ", ".join(keys)))
        out[k] = v.strip()
    return out


def to_float(key, text):
    try:
        if "/" in text:
            a, b = text.split("/", 1)
            return float(a) / float(b)
        return float(text)
    except (ValueError, ZeroDivisionError):
        raise PAError("参数 %s 不是有效数字: %r" % (key, text))


def build_arm(preset, overrides):
    if preset not in PRESETS:
        raise PAError("未知预设 %r,可用: %s" % (preset, ", ".join(PRESETS)))
    arm = dict(PRESETS[preset])
    for k, v in overrides.items():
        arm[k] = INERTIA.get(v, v) if k == "inertia_mode" else to_float(k, v)
    errs = []
    for k in ARM_KEYS:
        if k != "inertia_mode" and not finite(arm[k]):
            errs.append("%s 必须是有限数字" % k)
    errs += ["%s 必须 > 0" % k for k in ARM_POSITIVE if finite(arm[k]) and not arm[k] > 0]
    if arm["inertia_mode"] not in INERTIA.values():
        errs.append("inertia_mode 必须是 %s 之一" % "/".join(INERTIA))
    if errs:
        raise PAError("摆臂参数校验失败: " + ";".join(errs))
    return arm


def build_gear(gear_mod, overrides):
    gp = dict(gear_mod.DEFAULTS)
    for k, v in overrides.items():
        gp[k] = to_float(k, v)
    errs = ["%s 必须是 >0 的有限数字" % k for k in GEAR_KEYS if not (finite(gp[k]) and gp[k] > 0)]
    if errs:
        raise PAError("齿轮参数校验失败: " + ";".join(errs))
    return {k: float(gp[k]) for k in GEAR_KEYS}


def check_folder(gear_mod, folder):
    if not os.path.isdir(folder):
        raise PAError("齿轮数据文件夹不存在: %s" % folder)
    try:
        parsed, matched, missing, unmatched, need = gear_mod.load_folder(folder)
    except Exception as e:
        raise PAError("解析齿轮CSV失败: %s" % e)
    if missing:
        raise PAError("缺少 %d 个必需文件: %s" % (len(missing), ", ".join("%s_%s.csv" % (m[:2], m[2:]) for m in missing)))
    files = {}
    for k in need:
        torque, pos, z = parsed[k]
        short = [pos[i] for i, row in enumerate(z) if len(row) < len(torque)]
        if short:
            raise PAError("%s: 位置 %s 的数据列数少于扭矩级数 %d" % (os.path.basename(matched[k]), short[0], len(torque)))
        files[k] = dict(file=os.path.basename(matched[k]), sha256=sha256_file(matched[k]),
                        n_torque=len(torque), n_pos=len(pos))
    return files, unmatched


def run_prepare(out, preset, arm_kv, gear_kv, folder):
    _, gear = load_vendor()
    arm = build_arm(preset, parse_kv(arm_kv, ARM_KEYS, "摆臂"))
    gp = build_gear(gear, parse_kv(gear_kv, GEAR_KEYS, "齿轮"))
    folder = os.path.abspath(folder)
    files, unmatched = check_folder(gear, folder)
    for name in DOWNSTREAM:
        stale = os.path.join(out, name)
        if os.path.isfile(stale):
            os.remove(stale)
    write_json(os.path.join(out, "arm_params.json"), arm)
    write_json(os.path.join(out, "gear_params.json"), dict(params=gp, gear_folder=folder, files=files))
    rows = "\n".join("| %s | %s | %d | %d | %s |" % (k, v["file"], v["n_torque"], v["n_pos"], v["sha256"][:12])
                     for k, v in files.items())
    warn = "\n".join("- " + u for u in unmatched) or "- 无"
    write_text(os.path.join(out, "gear_files_report.md"),
               "# 齿轮数据文件匹配报告\n\n文件夹: `%s`\n\n| 关节 | 文件 | 扭矩级数 | 位置数 | sha256(前12位) |\n|---|---|---|---|---|\n%s\n\n"
               "## 未匹配/被忽略的文件\n%s\n" % (folder, rows, warn))
    return arm, gp, files
