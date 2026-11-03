#!/usr/bin/env python3
"""批量修改 CSV 第一行(表头)的列名, 其余内容原样保留。

用法:
  python rename_header.py                       # 无参数: 弹出图形界面
  python rename_header.py -i 输入目录 -o 输出目录  # 命令行模式 (保持子目录结构)
  python rename_header.py -i 输入目录 -o 输出目录 --dry-run      # 仅预览
  python rename_header.py -i 输入目录 -o 输出目录 --skip-others  # 不复制非 CSV 文件
"""
import argparse
import codecs
import os
import queue
import shutil
import sys
import threading
from pathlib import Path

RENAME = {
    "位置给定": "pos_cmd",
    "位置反馈": "pos_fbk",
    "速度给定": "vel_cmd",
    "速度反馈": "vel_fbk",
    "IQ给定": "IQ_cmd",
    "IQ反馈": "IQ_fbk",
    "编码器反馈": "encoder_fbk",
    "运行次数": "cycle",
}
ENCODINGS = ("utf-8", "gbk")


def convert_header(raw: bytes):
    """返回 (新的首行字节, 是否有改动); 无法解码返回 None。保留 BOM、编码和换行符。"""
    bom = b""
    if raw.startswith(codecs.BOM_UTF8):
        bom, raw = codecs.BOM_UTF8, raw[len(codecs.BOM_UTF8):]
    body = raw.rstrip(b"\r\n")
    eol = raw[len(body):]
    for enc in ENCODINGS:
        try:
            text = body.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return None
    cols = text.split(",")
    new_cols = [RENAME.get(c.strip(), c) for c in cols]
    return bom + ",".join(new_cols).encode(enc) + eol, new_cols != cols


def process_csv(src: Path, dst: Path, dry_run: bool):
    with open(src, "rb") as fin:
        res = convert_header(fin.readline())
        if res is None:
            return "undecodable"
        new_first, changed = res
        if dry_run:
            return "changed" if changed else "unchanged"
        tmp = dst.with_name(dst.name + ".tmp")
        with open(tmp, "wb") as fout:
            fout.write(new_first)
            shutil.copyfileobj(fin, fout, 1024 * 1024)
    os.replace(tmp, dst)
    return "changed" if changed else "unchanged"


def run(src: Path, dst: Path, dry_run=False, skip_others=False, log=print):
    if not src.is_dir():
        raise FileNotFoundError(f"输入文件夹不存在: {src}")
    src_r, dst_r = src.resolve(), dst.resolve()
    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)

    stats = {"changed": 0, "unchanged": 0, "copied": 0, "failed": 0}
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if dst_r != src_r and dst_r in f.resolve().parents:
            continue  # 输出目录位于输入目录内时, 跳过输出目录自身
        rel = f.relative_to(src)
        target = dst / rel
        try:
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix.lower() == ".csv":
                result = process_csv(f, target, dry_run)
                if result == "undecodable":
                    stats["failed"] += 1
                    log(f"[失败] 表头无法解码: {rel}")
                    continue
                stats[result] += 1
                log(f"[{'预览' if dry_run else '完成'}-{'已改表头' if result == 'changed' else '表头无需修改'}] {rel}")
            elif not skip_others:
                if not dry_run and dst_r != src_r:
                    shutil.copy2(f, target)
                stats["copied"] += 1
                log(f"[{'预览' if dry_run else '复制'}-非CSV原样] {rel}")
        except Exception as e:
            stats["failed"] += 1
            log(f"[失败] {rel}: {e}")
    log(f"汇总: 改表头 {stats['changed']}, 无需修改 {stats['unchanged']}, "
        f"非CSV复制 {stats['copied']}, 失败 {stats['failed']}")
    return stats


def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    root = tk.Tk()
    root.title("CSV 表头批量重命名")
    in_var, out_var = tk.StringVar(), tk.StringVar()
    dry_var, skip_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
    msgs = queue.Queue()

    def pick(var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    for r, (label, var) in enumerate([("输入文件夹", in_var), ("输出文件夹", out_var)]):
        tk.Label(root, text=label).grid(row=r, column=0, padx=6, pady=6, sticky="e")
        tk.Entry(root, textvariable=var, width=60).grid(row=r, column=1, padx=6)
        tk.Button(root, text="浏览...", command=lambda v=var: pick(v)).grid(row=r, column=2, padx=6)
    tk.Checkbutton(root, text="仅预览(不实际写文件)", variable=dry_var).grid(row=2, column=1, sticky="w")
    tk.Checkbutton(root, text="不复制非 CSV 文件", variable=skip_var).grid(row=3, column=1, sticky="w")
    box = scrolledtext.ScrolledText(root, width=90, height=20, state="disabled")
    box.grid(row=5, column=0, columnspan=3, padx=6, pady=6)
    btn = tk.Button(root, text="开始", width=16)
    btn.grid(row=4, column=1, pady=6)

    def poll():
        try:
            while True:
                m = msgs.get_nowait()
                if m is None:
                    btn.configure(state="normal")
                    continue
                box.configure(state="normal")
                box.insert("end", m + "\n")
                box.see("end")
                box.configure(state="disabled")
        except queue.Empty:
            pass
        root.after(100, poll)

    def worker(src, dst, dry, skip):
        try:
            run(src, dst, dry, skip, msgs.put)
        except Exception as e:
            msgs.put(f"错误: {e}")
        msgs.put(None)

    def start():
        if not in_var.get() or not out_var.get():
            messagebox.showwarning("提示", "请先选择输入和输出文件夹")
            return
        src, dst = Path(in_var.get()), Path(out_var.get())
        if src.resolve() == dst.resolve() and not dry_var.get():
            if not messagebox.askyesno("确认", "输出与输入相同, 将直接覆盖原文件, 是否继续?"):
                return
        btn.configure(state="disabled")
        threading.Thread(target=worker, args=(src, dst, dry_var.get(), skip_var.get()), daemon=True).start()

    btn.configure(command=start)
    poll()
    root.mainloop()


def main():
    p = argparse.ArgumentParser(description="批量修改 CSV 表头列名")
    p.add_argument("-i", "--input", help="输入文件夹")
    p.add_argument("-o", "--output", help="输出文件夹")
    p.add_argument("--dry-run", action="store_true", help="仅预览")
    p.add_argument("--skip-others", action="store_true", help="不复制非 CSV 文件")
    a = p.parse_args()

    if not a.input and not a.output:
        run_gui()
        return
    if not a.input or not a.output:
        p.error("命令行模式需要同时指定 -i 和 -o")
    try:
        stats = run(Path(a.input), Path(a.output), a.dry_run, a.skip_others)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(1 if stats["failed"] else 0)


if __name__ == "__main__":
    main()
