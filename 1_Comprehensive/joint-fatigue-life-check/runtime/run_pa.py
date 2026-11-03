# -*- coding: utf-8 -*-
"""关节疲劳寿命综合校核 PA 命令行入口。

用法: python run_pa.py <stage> [选项]
stage: prepare | arm | gear | compare | report | all | selftest
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PRESETS, PAError  # noqa: E402


def stage_run(out, stage, args):
    from ca_gates import gate
    from aa01_prepare import run_prepare
    from aa02_arm import run_arm
    from aa03_gear import run_gear
    from aa04_compare import run_compare
    from aa05_report import run_report
    if stage == "prepare":
        if not args.gear_folder:
            raise PAError("prepare 需要 --gear-folder")
        run_prepare(out, args.preset, args.arm, args.gear, args.gear_folder)
    elif stage == "arm":
        run_arm(out)
    elif stage == "gear":
        run_gear(out)
    elif stage == "compare":
        run_compare(out, args.p)
    elif stage == "report":
        run_report(out)
    res = gate(out, stage)
    print("[%s] %s  (%d/%d 项通过)" % (stage, "PASS" if res["passed"] else "FAIL",
                                       len(res["checks"]) - res["n_fail"], len(res["checks"])))
    for c in res["checks"]:
        if c["status"] == "FAIL":
            print("  FAIL  %s  -> %s" % (c["name"], c["evidence"]))
    if not res["passed"]:
        raise PAError("%s 阶段质量门禁未通过,已停止,详见 %s" % (stage, os.path.join(out, "gate_%s.json" % stage)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="关节疲劳寿命综合校核 PA")
    ap.add_argument("stage", choices=["prepare", "arm", "gear", "compare", "report", "all", "selftest"])
    ap.add_argument("--out", default="out", help="输出目录(默认 ./out)")
    ap.add_argument("--preset", default="anker", choices=list(PRESETS))
    ap.add_argument("--arm", action="append", metavar="KEY=VALUE", help="覆盖摆臂参数,可重复")
    ap.add_argument("--gear", action="append", metavar="KEY=VALUE", help="覆盖齿轮参数,可重复")
    ap.add_argument("--gear-folder", help="含 12 个 {FL,FR,RL,RR}_{hip,thigh,calf}.csv 的目录")
    ap.add_argument("--p", type=float, default=6.61, help="跨模块对比用寿命指数,默认 6.61")
    args = ap.parse_args(argv)
    out = os.path.abspath(args.out)
    try:
        if args.stage == "selftest":
            from selftest import run_selftest
            return run_selftest()
        order = ["prepare", "arm", "gear", "compare", "report"] if args.stage == "all" else [args.stage]
        for s in order:
            stage_run(out, s, args)
        print("输出目录: " + out)
        return 0
    except PAError as e:
        print("错误: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
