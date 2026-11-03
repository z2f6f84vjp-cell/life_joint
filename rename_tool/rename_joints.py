#!/usr/bin/env python3
"""批量重命名 1_01~1_12 为 FL_hip ... RR_calf。

用法:
  python rename_joints.py                      # 无参数: 弹出图形界面选择输入/输出文件夹
  python rename_joints.py -i 输入目录 -o 输出目录 # 命令行模式 (默认复制, 不改动原文件)
  python rename_joints.py -i 输入目录 -o 输出目录 --move     # 移动而不是复制
  python rename_joints.py -i 输入目录 -o 输出目录 --dry-run  # 仅预览
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

NAMES = [
    "FL_hip", "FL_thigh", "FL_calf",
    "FR_hip", "FR_thigh", "FR_calf",
    "RL_hip", "RL_thigh", "RL_calf",
    "RR_hip", "RR_thigh", "RR_calf",
]
MAPPING = {f"1_{i:02d}": name for i, name in enumerate(NAMES, start=1)}
STEM_RE = re.compile(r"^1_(0[1-9]|1[0-2])$")


def rename_files(src: Path, dst: Path, move=False, dry_run=False, log=print):
    if not src.is_dir():
        raise FileNotFoundError(f"输入文件夹不存在: {src}")
    dst.mkdir(parents=True, exist_ok=True)

    done, skipped = 0, 0
    found = set()
    for f in sorted(src.iterdir()):
        if not f.is_file() or not STEM_RE.match(f.stem):
            continue
        found.add(f.stem)
        target = dst / (MAPPING[f.stem] + f.suffix)
        if target.exists() and target.resolve() != f.resolve():
            log(f"[跳过] 目标已存在: {target.name}")
            skipped += 1
            continue
        action = "移动" if move else "复制"
        log(f"[{'预览' if dry_run else action}] {f.name} -> {target.name}")
        if not dry_run:
            (shutil.move if move else shutil.copy2)(str(f), str(target))
        done += 1

    for stem in sorted(set(MAPPING) - found):
        log(f"[缺失] 未找到 {stem}.*")
    log(f"完成: 处理 {done} 个, 跳过 {skipped} 个, 缺失 {len(MAPPING) - len(found)} 个")
    return done, skipped


def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    root = tk.Tk()
    root.title("关节文件批量重命名")
    in_var, out_var = tk.StringVar(), tk.StringVar()
    move_var, dry_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)

    def pick(var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    for r, (label, var) in enumerate([("输入文件夹", in_var), ("输出文件夹", out_var)]):
        tk.Label(root, text=label).grid(row=r, column=0, padx=6, pady=6, sticky="e")
        tk.Entry(root, textvariable=var, width=60).grid(row=r, column=1, padx=6)
        tk.Button(root, text="浏览...", command=lambda v=var: pick(v)).grid(row=r, column=2, padx=6)

    tk.Checkbutton(root, text="移动文件(默认复制, 保留原文件)", variable=move_var).grid(row=2, column=1, sticky="w")
    tk.Checkbutton(root, text="仅预览(不实际执行)", variable=dry_var).grid(row=3, column=1, sticky="w")
    box = scrolledtext.ScrolledText(root, width=80, height=18, state="disabled")
    box.grid(row=5, column=0, columnspan=3, padx=6, pady=6)

    def log(msg):
        box.configure(state="normal")
        box.insert("end", msg + "\n")
        box.see("end")
        box.configure(state="disabled")

    def start():
        if not in_var.get() or not out_var.get():
            messagebox.showwarning("提示", "请先选择输入和输出文件夹")
            return
        try:
            rename_files(Path(in_var.get()), Path(out_var.get()), move_var.get(), dry_var.get(), log)
        except Exception as e:
            messagebox.showerror("错误", str(e))

    tk.Button(root, text="开始重命名", command=start, width=16).grid(row=4, column=1, pady=6)
    root.mainloop()


def main():
    p = argparse.ArgumentParser(description="批量重命名 1_01~1_12 为 FL_hip ... RR_calf")
    p.add_argument("-i", "--input", help="输入文件夹")
    p.add_argument("-o", "--output", help="输出文件夹")
    p.add_argument("--move", action="store_true", help="移动文件而不是复制")
    p.add_argument("--dry-run", action="store_true", help="仅预览, 不实际执行")
    a = p.parse_args()

    if not a.input and not a.output:
        run_gui()
        return
    if not a.input or not a.output:
        p.error("命令行模式需要同时指定 -i 和 -o")
    try:
        rename_files(Path(a.input), Path(a.output), a.move, a.dry_run)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
