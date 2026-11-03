#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WS2.5 关节齿轮接触疲劳寿命校核 —— 方法二本地工具
单边啮合次数 = 圈数 x 齿数 / 2; 损伤 D = |扭矩|^m x 啮合次数
判定按每个位置独立与额定预算对比, 取各关节最严苛位置(不跨位置累加)
纯 Python 标准库(tkinter), 无需安装任何第三方包, 双击 启动工具.bat 即可运行.
"""
import os
import re
import csv
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

LEGS = ["FL", "FR", "RL", "RR"]
JOINTS = ["hip", "thigh", "calf"]
JOINT_LABEL = {"hip": "Hip", "thigh": "Thigh", "calf": "Calf"}

DEFAULTS = {
    "TR": 12.8, "NR": 71820000.0, "LH": 3000.0,
    "M": 6.61, "TEETH": 128.0, "SIDE": 2.0, "TW": 5635.486,
}


def strip_bom(s):
    if s and s[0] == "﻿":
        return s[1:]
    return s


def parse_csv(text):
    lines = text.splitlines()
    titles_idx = -1
    data_idx = -1
    for i, l in enumerate(lines):
        t = l.strip()
        if t == "#TITLES":
            titles_idx = i
        if t == "#DATA":
            data_idx = i
    if titles_idx < 0 or data_idx < 0:
        raise ValueError("文件缺少 #TITLES 或 #DATA 标记")
    parts = lines[titles_idx + 1].split(",")
    torque = [float(v) for v in parts[1:]]

    rows = []
    for l in lines[data_idx + 1:]:
        l = l.strip()
        if not l:
            continue
        p = l.split(",")
        if len(p) < 2:
            continue
        pos = float(p[0])
        vals = [float(v) for v in p[1:]]
        rows.append((pos, vals))
    rows.sort(key=lambda r: r[0])
    pos = [r[0] for r in rows]
    z = [r[1] for r in rows]
    return torque, pos, z


def match_key(filename):
    base = re.sub(r"\.csv$", "", filename, flags=re.IGNORECASE)
    norm = re.sub(r"[\s_]", "", base).lower()
    for leg in LEGS:
        for joint in JOINTS:
            if norm == (leg + joint).lower():
                return leg + joint
    return None


def load_folder(folder):
    """returns (parsed_data dict, matched_files dict, missing list, unmatched list, need list)"""
    csv_files = glob.glob(os.path.join(folder, "*.csv"))
    matched = {}
    unmatched = []
    for f in csv_files:
        name = os.path.basename(f)
        key = match_key(name)
        if key:
            if key in matched:
                unmatched.append(name + "（重复匹配，已忽略）")
            else:
                matched[key] = f
        else:
            unmatched.append(name + "（无法匹配到 leg×joint）")

    need = [leg + joint for leg in LEGS for joint in JOINTS]
    missing = [k for k in need if k not in matched]

    parsed = {}
    if not missing:
        for k, path in matched.items():
            with open(path, encoding="utf-8-sig", errors="ignore") as fh:
                text = strip_bom(fh.read())
            torque, pos, z = parse_csv(text)
            parsed[k] = (torque, pos, z)

    return parsed, matched, missing, unmatched, need


def compute_all(parsed, params):
    TR, NR, LH, M = params["TR"], params["NR"], params["LH"], params["M"]
    TEETH, SIDE, TW = params["TEETH"], params["SIDE"], params["TW"]
    K = (LH * 3600.0) / TW
    D_allow = (TR ** M) * NR

    per_joint = []
    per_pos_all = []

    for leg in LEGS:
        for joint in JOINTS:
            key = leg + joint
            torque, pos, z = parsed[key]
            AT = [abs(t) for t in torque]
            n_pos, n_tq = len(pos), len(torque)

            positions = []

            for i in range(n_pos):
                cyc_test = 0.0
                dmg_test = 0.0
                tmax = 0.0

                row = z[i]
                for j in range(n_tq):
                    zij = row[j]
                    if zij <= 0:
                        continue
                    n = zij * TEETH / SIDE
                    cyc_test += n
                    dmg_test += (AT[j] ** M) * n
                    if AT[j] > tmax:
                        tmax = AT[j]
                if cyc_test <= 0:
                    continue

                Teq = (dmg_test / cyc_test) ** (1.0 / M)
                mesh3000 = cyc_test * K
                D3000 = dmg_test * K
                equiv_mesh_at_rated = D3000 / (TR ** M)
                U = equiv_mesh_at_rated / NR
                SF = 1.0 / U if U > 0 else float("inf")
                hours = SF * LH
                verdict = "PASS" if U <= 1 else "FAIL"

                positions.append({
                    "leg": leg, "joint": joint, "position_deg": pos[i],
                    "mesh_1side_test": cyc_test, "mesh_1side_3000h": mesh3000,
                    "pseudo_damage_3000h": D3000, "damage_equiv_torque_Nm": Teq,
                    "max_torque_Nm": tmax, "equiv_mesh_at_rated": equiv_mesh_at_rated,
                    "budget_utilization": U, "safety_factor": SF,
                    "supported_hours": hours, "verdict": verdict,
                })

            if not positions:
                continue

            worst = max(positions, key=lambda p: p["budget_utilization"])
            n_fail = sum(1 for p in positions if p["verdict"] == "FAIL")

            per_joint.append({
                "leg": leg, "joint": joint,
                "nonzero_positions": len(positions),
                "worst_position_deg": worst["position_deg"],
                "worst_damage_equiv_torque_Nm": worst["damage_equiv_torque_Nm"],
                "worst_max_torque_Nm": worst["max_torque_Nm"],
                "worst_mesh_3000h": worst["mesh_1side_3000h"],
                "worst_damage_3000h": worst["pseudo_damage_3000h"],
                "max_budget_utilization": worst["budget_utilization"],
                "min_safety_factor": worst["safety_factor"],
                "supported_hours": worst["safety_factor"] * LH,
                "positions_failing": n_fail,
                "verdict": "PASS" if worst["budget_utilization"] <= 1 else "FAIL",
                "positions": positions,
            })
            per_pos_all.extend(positions)

    return {"per_joint": per_joint, "per_pos_all": per_pos_all, "D_allow": D_allow, "K": K}


def fmt_sci(v, d=3):
    return "{:.{}e}".format(v, d)


def fmt_fix(v, d=2):
    return "{:.{}f}".format(v, d)


def fmt_num(v):
    if abs(v) >= 1e6 or (abs(v) > 0 and abs(v) < 1e-3):
        return fmt_sci(v, 3)
    return fmt_fix(v, 3)


# ---------- 损伤-位置分布图：共用绘图逻辑 ----------

def augment_with_pct_and_risk(joint):
    """返回 (按位置升序排列的 positions 列表(带 _pct), risk_set 累积80%损伤的位置集合)"""
    positions = sorted(joint["positions"], key=lambda p: p["position_deg"])
    total_damage = sum(p["pseudo_damage_3000h"] for p in positions)
    for p in positions:
        p["_pct"] = p["pseudo_damage_3000h"] / total_damage * 100 if total_damage > 0 else 0
    by_damage_desc = sorted(positions, key=lambda p: -p["_pct"])
    cum = 0.0
    risk_set = set()
    for p in by_damage_desc:
        cum += p["_pct"]
        risk_set.add(p["position_deg"])
        if cum >= 80:
            break
    return positions, risk_set


def format_tip(p):
    return (
        "位置 {:.2f}°\n占比 {:.2f}%\n啮合(3000h) {}\n损伤D {}\n"
        "等效扭矩 {:.2f} N·m\n峰值扭矩 {:.2f} N·m\nU={:.4f} SF={}\n{}"
    ).format(
        p["position_deg"], p["_pct"], fmt_sci(p["mesh_1side_3000h"], 3),
        fmt_sci(p["pseudo_damage_3000h"], 3), p["damage_equiv_torque_Nm"],
        p["max_torque_Nm"], p["budget_utilization"], fmt_num(p["safety_factor"]), p["verdict"],
    )


def bind_tooltip(widget, canvas, item, text):
    tip = {"win": None}

    def show(event):
        hide(event)
        x, y = event.x_root + 14, event.y_root + 10
        win = tk.Toplevel(widget)
        win.wm_overrideredirect(True)
        try:
            win.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        win.wm_geometry("+{}+{}".format(x, y))
        lbl = tk.Label(win, text=text, justify="left", bg="#0b0b0b", fg="white",
                       font=("Consolas", 8), padx=8, pady=6)
        lbl.pack()
        tip["win"] = win

    def hide(event):
        if tip["win"] is not None:
            try:
                tip["win"].destroy()
            except tk.TclError:
                pass
            tip["win"] = None

    canvas.tag_bind(item, "<Enter>", show)
    canvas.tag_bind(item, "<Leave>", hide)


def render_bar_chart(widget, canvas, x0, y0, w, h, positions, risk_set,
                      show_ylabel=True, tick_every=None, font_size=8, tooltip=True,
                      click_cb=None):
    """在 canvas 的 (x0,y0,w,h) 区域内画一张位置-损伤占比柱状图，返回绘制的矩形项列表"""
    margin_l = 40 if show_ylabel else 14
    margin_r = 8
    margin_t = 6
    margin_b = 30
    plot_w = w - margin_l - margin_r
    plot_h = h - margin_t - margin_b
    max_pct = max((p["_pct"] for p in positions), default=0.01) or 0.01
    n = len(positions)
    bar_w = plot_w / n if n else plot_w

    nticks = 5 if h >= 220 else 3
    for t in range(nticks + 1):
        yv = max_pct * t / nticks
        y = y0 + margin_t + plot_h - (yv / max_pct) * plot_h
        canvas.create_line(x0 + margin_l, y, x0 + w - margin_r, y, fill="#e1e0d9")
        if show_ylabel:
            canvas.create_text(x0 + margin_l - 4, y, text="{:.0f}%".format(yv),
                                anchor="e", font=("Arial", max(7, font_size - 1)), fill="#898781")

    step = tick_every or max(1, n // 8)
    items = []
    for i, p in enumerate(positions):
        x = x0 + margin_l + i * bar_w
        hh = (p["_pct"] / max_pct) * plot_h
        y = y0 + margin_t + plot_h - hh
        color = "#d03b3b" if p["position_deg"] in risk_set else "#2a78d6"
        rect = canvas.create_rectangle(
            x + bar_w * 0.08, y, x + bar_w * 0.92, y0 + margin_t + plot_h,
            fill=color, outline="",
        )
        items.append((rect, p))
        if tooltip:
            bind_tooltip(widget, canvas, rect, format_tip(p))
        if click_cb:
            canvas.tag_bind(rect, "<Button-1>", lambda e, cb=click_cb: cb())
        if i % step == 0:
            canvas.create_text(
                x + bar_w / 2, y0 + h - margin_b + 10, text="{:.0f}".format(p["position_deg"]),
                font=("Arial", max(7, font_size - 1)), fill="#898781", angle=60, anchor="e",
            )

    canvas.create_line(x0 + margin_l, y0 + margin_t + plot_h, x0 + w - margin_r,
                        y0 + margin_t + plot_h, fill="#c3c2b7")
    if show_ylabel:
        canvas.create_text(x0 + 12, y0 + margin_t + plot_h / 2, text="占关节损伤 %",
                            angle=90, font=("Arial", font_size), fill="#52514e")
    return items


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WS2.5 关节齿轮接触疲劳寿命校核 - 方法二本地工具")
        self.geometry("1180x780")
        self.minsize(980, 640)

        self.parsed = {}
        self.results = None
        self.folder = None
        self.param_vars = {}

        self._build_ui()

    # ---------- UI 构建 ----------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        title = tk.Label(
            self,
            text="WS2.5 关节齿轮接触疲劳寿命校核 —（单边啮合 · 逐位置判据）",
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        title.pack(anchor="w", **pad)

        subtitle = tk.Label(
            self,
            text=("单边啮合次数 = 圈数 x 齿数 / 2; 损伤 D = |扭矩|^m x 啮合次数; "
                  "判定按每个位置独立与额定预算对比, 取各关节最严苛位置(不跨位置累加)。"
                  "全部计算在本机完成, 不联网、不上传。"),
            font=("Microsoft YaHei UI", 9), fg="#52514e", wraplength=1120, justify="left",
        )
        subtitle.pack(anchor="w", padx=10, pady=(0, 10))

        # --- 文件夹选择 ---
        f1 = ttk.LabelFrame(self, text="① 选择数据文件夹")
        f1.pack(fill="x", padx=10, pady=6)
        row = tk.Frame(f1)
        row.pack(fill="x", padx=8, pady=6)
        ttk.Button(row, text="选择文件夹...", command=self.pick_folder).pack(side="left")
        self.status_var = tk.StringVar(value="尚未选择数据文件夹。请选择包含 12 个 "
                                               "{FL/FR/RL/RR}_{hip/thigh/calf}.csv 文件的目录。")
        self.status_label = tk.Label(row, textvariable=self.status_var, fg="#52514e", anchor="w")
        self.status_label.pack(side="left", padx=10)

        self.filelist_text = tk.Text(f1, height=5, font=("Consolas", 9), wrap="none")
        self.filelist_text.pack(fill="x", padx=8, pady=(0, 8))
        self.filelist_text.configure(state="disabled")

        # --- 参数面板 ---
        f2 = ttk.LabelFrame(self, text="② 校核参数（修改后自动重新计算）")
        f2.pack(fill="x", padx=10, pady=6)
        prow = tk.Frame(f2)
        prow.pack(fill="x", padx=8, pady=8)

        labels = [
            ("TR", "额定扭矩 T_R (N·m)"), ("NR", "额定啮合次数 N_R"),
            ("LH", "额定寿命 L_H (h)"), ("M", "寿命指数 m"),
            ("TEETH", "齿数"), ("SIDE", "单边除数"), ("TW", "测试墙钟时长 (s)"),
        ]
        for i, (key, label) in enumerate(labels):
            col = tk.Frame(prow)
            col.grid(row=0, column=i, padx=6, sticky="w")
            tk.Label(col, text=label, font=("Microsoft YaHei UI", 8), fg="#52514e").pack(anchor="w")
            var = tk.StringVar(value=str(DEFAULTS[key]))
            ent = tk.Entry(col, textvariable=var, width=13)
            ent.pack()
            ent.bind("<KeyRelease>", lambda e: self.on_param_change())
            self.param_vars[key] = var

        btnrow = tk.Frame(f2)
        btnrow.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btnrow, text="恢复默认值", command=self.reset_params).pack(side="left")
        self.export_btn = ttk.Button(btnrow, text="导出结果 CSV...", command=self.export_csv, state="disabled")
        self.export_btn.pack(side="left", padx=8)
        self.chart_btn = ttk.Button(btnrow, text="损伤-位置分布图（全部关节）...",
                                     command=self.open_grid_chart, state="disabled")
        self.chart_btn.pack(side="left", padx=8)

        # --- 结果表格 ---
        f3 = ttk.LabelFrame(self, text="③ 关节级校核结果（点击表头排序，双击行看单关节分布图）")
        f3.pack(fill="both", expand=True, padx=10, pady=6)

        self.summary_var = tk.StringVar(value="")
        tk.Label(f3, textvariable=self.summary_var, font=("Microsoft YaHei UI", 9),
                 fg="#52514e").pack(anchor="w", padx=8, pady=(4, 0))

        cols = ["legjoint", "npos", "worst_pos", "teq", "damage", "U", "SF", "hours", "nfail", "verdict"]
        col_labels = {
            "legjoint": "关节", "npos": "非零位置数", "worst_pos": "最危险位置(°)",
            "teq": "等效扭矩(N·m)", "damage": "该位置损伤 D", "U": "U=D/D_allow",
            "SF": "安全系数 SF", "hours": "支持寿命(h)", "nfail": "失效位置数",
            "verdict": "判定",
        }
        self.tree = ttk.Treeview(f3, columns=cols, show="headings", height=13)
        for c in cols:
            self.tree.heading(c, text=col_labels[c], command=lambda cc=c: self.sort_by(cc))
            anchor = "w" if c in ("legjoint",) else "e"
            width = 150 if c == "legjoint" else 120
            self.tree.column(c, width=width, anchor=anchor)
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.tag_configure("pass", background="#e8f5e9", foreground="#1b6e1b")
        self.tree.tag_configure("fail", background="#fdecea", foreground="#a11d1d")
        self.tree.bind("<Double-1>", self.on_row_double_click)

        self.sort_key = "SF"
        self.sort_asc = True
        self.row_data_map = {}

    # ---------- 逻辑 ----------
    def read_params(self):
        out = {}
        for k, var in self.param_vars.items():
            try:
                out[k] = float(var.get())
            except ValueError:
                return None
        if any(v <= 0 for v in out.values()):
            return None
        return out

    def reset_params(self):
        for k, v in DEFAULTS.items():
            self.param_vars[k].set(str(v))
        self.recompute()

    def on_param_change(self):
        self.recompute()

    def pick_folder(self):
        folder = filedialog.askdirectory(title="选择包含 12 个 CSV 的数据文件夹")
        if not folder:
            return
        self.folder = folder
        try:
            parsed, matched, missing, unmatched, need = load_folder(folder)
        except Exception as e:
            self.status_var.set("解析失败：" + str(e))
            self.status_label.configure(fg="#a11d1d")
            return

        self.filelist_text.configure(state="normal")
        self.filelist_text.delete("1.0", "end")
        for k in need:
            if k in matched:
                self.filelist_text.insert("end", "OK  {} -> {}\n".format(k, os.path.basename(matched[k])))
            else:
                self.filelist_text.insert("end", "MISSING  {}_{}.csv\n".format(k[:2], k[2:]))
        for m in unmatched:
            self.filelist_text.insert("end", "WARN  " + m + "\n")
        self.filelist_text.configure(state="disabled")

        if missing:
            self.status_var.set("已选文件夹，但缺少 {} 个必需文件，无法计算。".format(len(missing)))
            self.status_label.configure(fg="#a11d1d")
            self.results = None
            self.render_table()
            self.export_btn.configure(state="disabled")
            self.chart_btn.configure(state="disabled")
            return

        self.parsed = parsed
        self.status_var.set("已加载并解析 12 个文件（每关节 57 位置 x 64 扭矩级）。文件夹：" + folder)
        self.status_label.configure(fg="#1b6e1b")
        self.recompute()

    def recompute(self):
        if len(self.parsed) != 12:
            self.results = None
            self.render_table()
            return
        params = self.read_params()
        if params is None:
            self.status_var.set("参数存在非正数或非法值，请检查。")
            self.status_label.configure(fg="#a11d1d")
            return
        try:
            self.results = compute_all(self.parsed, params)
        except Exception as e:
            messagebox.showerror("计算出错", str(e))
            return
        self.render_table()
        self.export_btn.configure(state="normal")
        self.chart_btn.configure(state="normal")

    def sort_by(self, col):
        key_map = {
            "legjoint": lambda r: r["leg"] + r["joint"],
            "npos": lambda r: r["nonzero_positions"],
            "worst_pos": lambda r: r["worst_position_deg"],
            "teq": lambda r: r["worst_damage_equiv_torque_Nm"],
            "damage": lambda r: r["worst_damage_3000h"],
            "U": lambda r: r["max_budget_utilization"],
            "SF": lambda r: r["min_safety_factor"],
            "hours": lambda r: r["supported_hours"],
            "nfail": lambda r: r["positions_failing"],
            "verdict": lambda r: r["verdict"],
        }
        if self.sort_key == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_key = col
            self.sort_asc = True
        self.render_table(sort_fn=key_map.get(col))

    def render_table(self, sort_fn=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.results:
            self.summary_var.set("")
            return

        D_allow = self.results["D_allow"]
        rows = list(self.results["per_joint"])
        if sort_fn is None:
            sort_fn = lambda r: r["min_safety_factor"]
        rows.sort(key=sort_fn, reverse=not self.sort_asc)

        n_fail = sum(1 for r in rows if r["verdict"] == "FAIL")
        self.summary_var.set(
            "D_allow = {}   |   {}/{} 通过, {}/{} 不通过".format(
                fmt_sci(D_allow, 3), len(rows) - n_fail, len(rows), n_fail, len(rows)
            )
        )

        self.row_data_map = {}
        for r in rows:
            key = r["leg"] + r["joint"]
            values = (
                "{} {}".format(r["leg"], JOINT_LABEL[r["joint"]]),
                r["nonzero_positions"],
                fmt_fix(r["worst_position_deg"], 2),
                fmt_fix(r["worst_damage_equiv_torque_Nm"], 2),
                fmt_sci(r["worst_damage_3000h"], 3),
                fmt_fix(r["max_budget_utilization"], 4),
                fmt_num(r["min_safety_factor"]),
                fmt_sci(r["supported_hours"], 3),
                r["positions_failing"],
                r["verdict"],
            )
            tag = "pass" if r["verdict"] == "PASS" else "fail"
            iid = self.tree.insert("", "end", values=values, tags=(tag,), iid=key)
            self.row_data_map[iid] = r

    def on_row_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid or iid not in self.row_data_map:
            return
        joint = self.row_data_map[iid]
        DetailWindow(self, joint)

    def open_grid_chart(self):
        if not self.results:
            return
        GridChartWindow(self, self.results["per_joint"])

    def export_csv(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(
            title="导出位置级结果", defaultextension=".csv",
            initialfile="life_check_per_position_correct.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        pos_headers = ["leg", "joint", "position_deg", "mesh_1side_test", "mesh_1side_3000h",
                       "pseudo_damage_3000h", "damage_equiv_torque_Nm", "max_torque_Nm",
                       "equiv_mesh_at_rated", "budget_utilization", "safety_factor",
                       "supported_hours", "verdict"]
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=pos_headers)
            w.writeheader()
            for p in self.results["per_pos_all"]:
                w.writerow({k: p[k] for k in pos_headers})

        sum_path = os.path.splitext(path)[0] + "_summary.csv"
        sum_headers = ["leg", "joint", "nonzero_positions", "worst_position_deg",
                       "worst_damage_equiv_torque_Nm", "worst_mesh_3000h", "max_budget_utilization",
                       "min_safety_factor", "supported_hours", "positions_failing",
                       "verdict"]
        with open(sum_path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(sum_headers)
            for j in self.results["per_joint"]:
                w.writerow([
                    j["leg"], j["joint"], j["nonzero_positions"], j["worst_position_deg"],
                    j["worst_damage_equiv_torque_Nm"], j["worst_mesh_3000h"],
                    j["max_budget_utilization"], j["min_safety_factor"], j["supported_hours"],
                    j["positions_failing"], j["verdict"],
                ])
        messagebox.showinfo("导出完成", "已导出：\n{}\n{}".format(path, sum_path))


class DetailWindow(tk.Toplevel):
    """单关节损伤-位置分布图（双击表格行打开）"""

    def __init__(self, parent, joint):
        super().__init__(parent)
        self.joint = joint
        self.title("单关节详情 - {} {}".format(joint["leg"], JOINT_LABEL[joint["joint"]]))
        self.geometry("980x640")

        header = tk.Label(
            self,
            text="{} {}   SF={}   {}".format(
                joint["leg"], JOINT_LABEL[joint["joint"]],
                fmt_num(joint["min_safety_factor"]), joint["verdict"],
            ),
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=("#1b6e1b" if joint["verdict"] == "PASS" else "#a11d1d"),
        )
        header.pack(anchor="w", padx=10, pady=8)

        legend = tk.Frame(self)
        legend.pack(anchor="w", padx=10)
        tk.Label(legend, text="■", fg="#d03b3b").pack(side="left")
        tk.Label(legend, text="风险位置（累积占比达 80% 的损伤贡献者）",
                 font=("Microsoft YaHei UI", 9)).pack(side="left", padx=(0, 14))
        tk.Label(legend, text="■", fg="#2a78d6").pack(side="left")
        tk.Label(legend, text="其余位置", font=("Microsoft YaHei UI", 9)).pack(side="left")

        positions, risk_set = augment_with_pct_and_risk(joint)

        canvas = tk.Canvas(self, height=340, bg="#fcfcfb", highlightthickness=0)
        canvas.pack(fill="x", padx=10, pady=8)
        self.update_idletasks()
        w = max(canvas.winfo_width(), 900)
        render_bar_chart(self, canvas, 0, 0, w, 320, positions, risk_set,
                          tick_every=max(1, len(positions) // 26))

        by_damage_desc = sorted(positions, key=lambda p: -p["_pct"])
        risk_rows = [p for p in by_damage_desc if p["position_deg"] in risk_set]
        frame = ttk.LabelFrame(
            self, text="风险位置（累积占比达 80% 的损伤贡献者，共 {} 个）".format(len(risk_rows))
        )
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ["rank", "pos", "mesh", "pct", "cum", "teq", "U", "verdict"]
        labels = {"rank": "排名", "pos": "位置(°)", "mesh": "啮合次数(3000h)", "pct": "损伤占比",
                  "cum": "累积占比", "teq": "等效扭矩", "U": "U", "verdict": "判定"}
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=8)
        for c in cols:
            tree.heading(c, text=labels[c])
            width = 110 if c in ("pos", "mesh") else 90
            tree.column(c, width=width, anchor="center")
        tree.pack(fill="both", expand=True, padx=6, pady=6)
        tree.tag_configure("pass", background="#e8f5e9")
        tree.tag_configure("fail", background="#fdecea")

        cum2 = 0.0
        for i, p in enumerate(risk_rows):
            cum2 += p["_pct"]
            tag = "pass" if p["verdict"] == "PASS" else "fail"
            tree.insert("", "end", values=(
                i + 1, fmt_fix(p["position_deg"], 2), fmt_sci(p["mesh_1side_3000h"], 3),
                fmt_fix(p["_pct"], 2) + "%",
                fmt_fix(cum2, 2) + "%", fmt_fix(p["damage_equiv_torque_Nm"], 2),
                fmt_fix(p["budget_utilization"], 4), p["verdict"],
            ), tags=(tag,))


class GridChartWindow(tk.Toplevel):
    """全部 12 关节的损伤-位置分布图总览（4 行=腿 x 3 列=关节），可滚动，点击任一小图放大看详情"""

    def __init__(self, parent, per_joint_list):
        super().__init__(parent)
        self.parent_app = parent
        self.title("损伤-位置分布图 — 全部关节总览")
        self.geometry("1220x860")

        header = tk.Label(
            self, text="各位置占本关节损伤的百分比；红色 = 累积占比达 80% 的风险位置；点击任一小图放大查看",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        header.pack(anchor="w", padx=12, pady=(10, 4))

        by_key = {(j["leg"], j["joint"]): j for j in per_joint_list}

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        vsb = ttk.Scrollbar(container, orient="vertical")
        canvas = tk.Canvas(container, bg="#fcfcfb", highlightthickness=0,
                            yscrollcommand=vsb.set)
        vsb.configure(command=canvas.yview)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        cell_w, cell_h, title_h = 380, 300, 34
        cols, rows = len(JOINTS), len(LEGS)
        total_w = cols * cell_w
        total_h = rows * cell_h
        canvas.configure(scrollregion=(0, 0, total_w, total_h))

        for r, leg in enumerate(LEGS):
            for c, joint_name in enumerate(JOINTS):
                key = (leg, joint_name)
                if key not in by_key:
                    continue
                jd = by_key[key]
                x0, y0 = c * cell_w, r * cell_h
                positions, risk_set = augment_with_pct_and_risk(jd)
                n_risk = len(risk_set)
                verdict_color = "#1b6e1b" if jd["verdict"] == "PASS" else "#a11d1d"
                title_txt = "{} {}   {} 风险位/{} 位   SF={}   {}".format(
                    leg, JOINT_LABEL[joint_name], n_risk, jd["nonzero_positions"],
                    fmt_num(jd["min_safety_factor"]), jd["verdict"],
                )
                canvas.create_rectangle(x0 + 4, y0 + 2, x0 + cell_w - 4, y0 + cell_h - 4,
                                         outline="#e1e0d9")
                canvas.create_text(x0 + 12, y0 + 16, text=title_txt, anchor="w",
                                    font=("Microsoft YaHei UI", 9, "bold"), fill=verdict_color)

                def make_click_cb(joint_data=jd):
                    return lambda: DetailWindow(self.parent_app, joint_data)

                render_bar_chart(
                    self, canvas, x0 + 6, y0 + title_h, cell_w - 12, cell_h - title_h - 6,
                    positions, risk_set, show_ylabel=True,
                    tick_every=max(1, len(positions) // 8), font_size=7,
                    tooltip=True, click_cb=make_click_cb(),
                )

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_wheel(_e):
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_wheel(_e):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", bind_wheel)
        canvas.bind("<Leave>", unbind_wheel)


if __name__ == "__main__":
    app = App()
    app.mainloop()
