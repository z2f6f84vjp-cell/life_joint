# -*- coding: utf-8 -*-
"""
7_tool 综合工具集 —— 页内嵌入式标签页版 Hub
不改动任何原有子工具模块文件，只 import 其中的纯逻辑函数/类，
把界面内容以 ttk.Frame 的形式嵌入到同一个窗口的 Notebook 标签页中，
从而可以直接在本页面查看各模块的完整界面与计算结果，无需跳转到其他窗口。

复用来源（原样 import，不修改）：
  - joint_life_core.py            核心算法：calculate_life / build_summary / create_figures
  - geer_cycle/gear_fatigue_tool.py  load_folder / compute_all / DetailWindow / GridChartWindow 等

双击 启动综合工具.bat 即可运行。
"""
import os
import sys
import time
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL_ROOT = os.path.dirname(HUB_DIR)  # D:\7_tool

if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)

APP_TITLE = "7_tool 综合工具集（本地桌面版）"

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import joint_life_core as jl_core
import geer_cycle.gear_fatigue_tool as gear_mod


# ============================================================
# Tab 1: 关节摆臂疲劳寿命计算工具
# 方法体搬自 joint_life_desktop.JointLifeApp，仅将基类从 tk.Tk 换成 ttk.Frame。
# 所有计算逐字调用 joint_life_core 里的原函数，不重新实现算法。
# ============================================================
class JointLifeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.last_result = None
        self._build_vars()
        self._build_layout()
        self.after(200, self.run_calculation)

    def _build_vars(self):
        self.var_v_max_rpm = tk.DoubleVar(value=100)
        self.var_theta_max_deg = tk.DoubleVar(value=120)
        self.var_theta_start_deg = tk.DoubleVar(value=-150)
        self.var_L = tk.DoubleVar(value=0.3)
        self.var_m_arm = tk.DoubleVar(value=5.176)
        self.var_m_load = tk.DoubleVar(value=2.0)
        self.var_g = tk.DoubleVar(value=9.80)
        self.var_inertia_mode = tk.StringVar(value="安克 (0.1828+I_load)")
        self.var_custom_I = tk.DoubleVar(value=0.0)
        self.var_life_exponent = tk.DoubleVar(value=10 / 3)
        self.var_C_rated = tk.DoubleVar(value=6.03)
        self.var_N_ref = tk.DoubleVar(value=100)
        self.var_L10_ref = tk.DoubleVar(value=3000)
        self.var_status = tk.StringVar(value="就绪")

    def _build_layout(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="🤖 关节摆臂疲劳寿命计算工具", style="Title.TLabel").pack(anchor="w", pady=(0, 8))

        param_frame = ttk.Frame(root)
        param_frame.pack(fill="x", pady=(0, 8))

        self._build_kinematics_group(param_frame).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._build_inertia_group(param_frame).grid(row=0, column=1, sticky="nsew", padx=8)
        self._build_fatigue_group(param_frame).grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        param_frame.columnconfigure(0, weight=1)
        param_frame.columnconfigure(1, weight=1)
        param_frame.columnconfigure(2, weight=1)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(btn_frame, text="🚀 开始计算", style="Run.TButton",
                   command=self.run_calculation).pack(side="left")
        ttk.Button(btn_frame, text="🔹 安克预设", command=self.preset_anker).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🔹 三花预设", command=self.preset_sanhua).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🔹 高速预设", command=self.preset_high).pack(side="left", padx=6)
        ttk.Label(btn_frame, textvariable=self.var_status, foreground="#5a6b7b").pack(side="left", padx=12)

        self.kpi_frame = ttk.Frame(root)
        self.kpi_frame.pack(fill="x", pady=(0, 8))
        self.kpi_labels = {}
        for key, cap in [("life", "测试寿命 (小时)"), ("cycles", "等效循环次数"),
                          ("teq", "等效扭矩 Teq (N·m)"),
                          ("tmax", "峰值扭矩绝对值 (N·m)"), ("integral", "疲劳积分")]:
            box = ttk.Frame(self.kpi_frame, relief="groove", borderwidth=1, padding=8)
            box.pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(box, text=cap, style="KPIcap.TLabel").pack(anchor="w")
            lbl = ttk.Label(box, text="—", style="KPI.TLabel")
            lbl.pack(anchor="w")
            self.kpi_labels[key] = lbl

        result_frame = ttk.Frame(root)
        result_frame.pack(fill="both", expand=True)

        left = ttk.Frame(result_frame)
        left.pack(side="left", fill="y", padx=(0, 8))
        ttk.Label(left, text="📄 计算结果", style="Header.TLabel").pack(anchor="w")
        self.text_summary = tk.Text(left, width=52, height=38, font=("Consolas", 9),
                                     bg="#0f1c28", fg="#d5e8d4", wrap="word")
        self.text_summary.pack(fill="y", expand=True)
        self.text_summary.insert("1.0", "点击「开始计算」查看结果…")
        self.text_summary.config(state="disabled")

        right = ttk.Frame(result_frame)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="📊 分析图表", style="Header.TLabel").pack(anchor="w")

        self.fig = Figure(figsize=(11, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, right)
        toolbar.update()

    def _labeled_entry(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var, width=12).grid(row=row, column=1, sticky="e", pady=3)

    def _build_kinematics_group(self, parent):
        box = ttk.LabelFrame(parent, text="📐 运动学参数", padding=10)
        self._labeled_entry(box, "最大转速 (rpm)", self.var_v_max_rpm, 0)
        self._labeled_entry(box, "总角位移 (°)", self.var_theta_max_deg, 1)
        self._labeled_entry(box, "起始角度 (°)", self.var_theta_start_deg, 2)
        self._labeled_entry(box, "摆臂长度 (m)", self.var_L, 3)
        box.columnconfigure(1, weight=1)
        return box

    def _build_inertia_group(self, parent):
        box = ttk.LabelFrame(parent, text="⚖️ 质量与惯量参数", padding=10)
        self._labeled_entry(box, "摆臂质量 (kg)", self.var_m_arm, 0)
        self._labeled_entry(box, "末端负载质量 (kg)", self.var_m_load, 1)
        self._labeled_entry(box, "重力加速度 (m/s²)", self.var_g, 2)
        ttk.Label(box, text="转动惯量计算方式").grid(row=3, column=0, sticky="w", pady=3)
        combo = ttk.Combobox(box, textvariable=self.var_inertia_mode, state="readonly", width=20,
                             values=["安克 (0.1828+I_load)", "三花 (0.095+I_load)",
                                     "理论 (I_arm+I_load)", "自定义"])
        combo.grid(row=3, column=1, sticky="e", pady=3)
        self._labeled_entry(box, "自定义 I0 (kg·m²)", self.var_custom_I, 4)
        box.columnconfigure(1, weight=1)
        return box

    def _build_fatigue_group(self, parent):
        box = ttk.LabelFrame(parent, text="🔧 疲劳寿命参数", padding=10)
        self._labeled_entry(box, "寿命指数 p", self.var_life_exponent, 0)
        self._labeled_entry(box, "额定扭矩 C (N·m)", self.var_C_rated, 1)
        self._labeled_entry(box, "参考转速 N_ref (rpm)", self.var_N_ref, 2)
        self._labeled_entry(box, "参考寿命 L10_ref (小时)", self.var_L10_ref, 3)
        box.columnconfigure(1, weight=1)
        return box

    def preset_anker(self):
        self._apply_preset(100, 120, -150, 0.3, 5.176, 2.0, 9.80, "安克 (0.1828+I_load)", 0.0, 10 / 3, 6.03, 100, 3000)

    def preset_sanhua(self):
        self._apply_preset(100, 120, -150, 0.3, 2.7, 2.65, 9.80, "三花 (0.095+I_load)", 0.0, 10 / 3, 6.03, 100, 3000)

    def preset_high(self):
        self._apply_preset(150, 120, -150, 0.3, 5.176, 2.0, 9.80, "安克 (0.1828+I_load)", 0.0, 10 / 3, 6.03, 100, 3000)

    def _apply_preset(self, v, dth, th0, L, marm, mload, g, mode, cI, p, C, Nref, L10):
        self.var_v_max_rpm.set(v); self.var_theta_max_deg.set(dth); self.var_theta_start_deg.set(th0)
        self.var_L.set(L); self.var_m_arm.set(marm); self.var_m_load.set(mload); self.var_g.set(g)
        self.var_inertia_mode.set(mode); self.var_custom_I.set(cI); self.var_life_exponent.set(p)
        self.var_C_rated.set(C); self.var_N_ref.set(Nref); self.var_L10_ref.set(L10)
        self.run_calculation()

    def _read_and_validate(self):
        try:
            v = dict(
                v_max_rpm=self.var_v_max_rpm.get(), theta_max_deg=self.var_theta_max_deg.get(),
                theta_start_deg=self.var_theta_start_deg.get(), L=self.var_L.get(),
                m_arm=self.var_m_arm.get(), m_load=self.var_m_load.get(), g=self.var_g.get(),
                inertia_mode=self.var_inertia_mode.get(), custom_I=self.var_custom_I.get(),
                life_exponent=self.var_life_exponent.get(), C_rated=self.var_C_rated.get(),
                N_ref=self.var_N_ref.get(), L10_ref=self.var_L10_ref.get(),
            )
        except tk.TclError:
            raise ValueError("参数输入格式有误，请检查是否为数字")

        errs = []
        if not (v["v_max_rpm"] > 0): errs.append("最大转速必须 > 0")
        if not (v["theta_max_deg"] > 0): errs.append("总角位移必须 > 0")
        if not (v["L"] > 0): errs.append("摆臂长度必须 > 0")
        if not (v["life_exponent"] > 0): errs.append("寿命指数必须 > 0")
        if not (v["C_rated"] > 0): errs.append("额定扭矩必须 > 0")
        if not (v["N_ref"] > 0): errs.append("参考转速必须 > 0")
        if not (v["L10_ref"] > 0): errs.append("参考寿命必须 > 0")
        if errs:
            raise ValueError("；".join(errs))
        return v

    def run_calculation(self):
        self.var_status.set("计算中…")
        self.update_idletasks()
        try:
            params = self._read_and_validate()
            r = jl_core.calculate_life(**params)
            if not np.isfinite(r["Life"]) or not np.isfinite(r["Teq"]):
                raise ValueError("结果发散，请检查参数取值范围")

            summary = jl_core.build_summary(r)
            self.text_summary.config(state="normal")
            self.text_summary.delete("1.0", "end")
            self.text_summary.insert("1.0", summary)
            self.text_summary.config(state="disabled")

            self.kpi_labels["life"].config(text=f"{r['Life']:.1f}")
            self.kpi_labels["cycles"].config(text=f"{(r['Life']*3600/r['T_total']):.0f}")
            self.kpi_labels["teq"].config(text=f"{r['Teq']:.3f}")
            self.kpi_labels["tmax"].config(text=f"{np.max(np.abs(r['torque_total'])):.2f}")
            self.kpi_labels["integral"].config(text=f"{r['fatigue_integral']:.3e}")

            jl_core.create_figures(self.fig, r)
            self.canvas.draw_idle()

            self.last_result = r
            self.var_status.set("✅ 计算完成 " + time.strftime("%H:%M:%S"))
        except Exception as e:
            self.var_status.set("❌ 计算出错")
            messagebox.showerror("计算错误", f"{e}\n\n详细信息已记录，可关闭本提示后调整参数重试。")
            traceback.print_exc()


# ============================================================
# Tab 2: WS2.5 关节齿轮接触疲劳寿命校核工具
# 方法体搬自 geer_cycle.gear_fatigue_tool.App，仅将基类从 tk.Tk 换成 ttk.Frame。
# 所有计算逐字调用 gear_mod 里的原函数/原弹窗类，不重新实现算法或图表逻辑。
# ============================================================
class GearFatigueTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parsed = {}
        self.results = None
        self.folder = None
        self.param_vars = {}
        self.sort_key = "SF"
        self.sort_asc = True
        self.row_data_map = {}
        self._build_ui()

    def _build_ui(self):
        title = tk.Label(
            self, text="WS2.5 关节齿轮接触疲劳寿命校核 —（单边啮合 · 逐位置判据）",
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        title.pack(anchor="w", padx=10, pady=(10, 4))

        subtitle = tk.Label(
            self,
            text=("单边啮合次数 = 圈数 x 齿数 / 2; 损伤 D = |扭矩|^m x 啮合次数; "
                  "判定按每个位置独立与额定预算对比, 取各关节最严苛位置(不跨位置累加)。"
                  "全部计算在本机完成, 不联网、不上传。"),
            font=("Microsoft YaHei UI", 9), fg="#52514e", wraplength=1120, justify="left",
        )
        subtitle.pack(anchor="w", padx=10, pady=(0, 10))

        f1 = ttk.LabelFrame(self, text="① 选择数据文件夹")
        f1.pack(fill="x", padx=10, pady=6)
        row = tk.Frame(f1)
        row.pack(fill="x", padx=8, pady=6)
        ttk.Button(row, text="选择文件夹...", command=self.pick_folder).pack(side="left")
        self.status_var = tk.StringVar(value="尚未选择数据文件夹。请选择包含 12 个 "
                                               "{FL/FR/RL/RR}_{hip/thigh/calf}.csv 文件的目录。")
        self.status_label = tk.Label(row, textvariable=self.status_var, fg="#52514e", anchor="w")
        self.status_label.pack(side="left", padx=10)

        self.filelist_text = tk.Text(f1, height=4, font=("Consolas", 9), wrap="none")
        self.filelist_text.pack(fill="x", padx=8, pady=(0, 8))
        self.filelist_text.configure(state="disabled")

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
            var = tk.StringVar(value=str(gear_mod.DEFAULTS[key]))
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
        self.tree = ttk.Treeview(f3, columns=cols, show="headings", height=10)
        for c in cols:
            self.tree.heading(c, text=col_labels[c], command=lambda cc=c: self.sort_by(cc))
            anchor = "w" if c in ("legjoint",) else "e"
            width = 150 if c == "legjoint" else 118
            self.tree.column(c, width=width, anchor=anchor)
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.tag_configure("pass", background="#e8f5e9", foreground="#1b6e1b")
        self.tree.tag_configure("fail", background="#fdecea", foreground="#a11d1d")
        self.tree.bind("<Double-1>", self.on_row_double_click)

    # ---------- 逻辑：全部原样调用 gear_mod 中的模块级函数 ----------
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
        for k, v in gear_mod.DEFAULTS.items():
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
            parsed, matched, missing, unmatched, need = gear_mod.load_folder(folder)
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
            self.results = gear_mod.compute_all(self.parsed, params)
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
                gear_mod.fmt_sci(D_allow, 3), len(rows) - n_fail, len(rows), n_fail, len(rows)
            )
        )

        self.row_data_map = {}
        for r in rows:
            key = r["leg"] + r["joint"]
            values = (
                "{} {}".format(r["leg"], gear_mod.JOINT_LABEL[r["joint"]]),
                r["nonzero_positions"],
                gear_mod.fmt_fix(r["worst_position_deg"], 2),
                gear_mod.fmt_fix(r["worst_damage_equiv_torque_Nm"], 2),
                gear_mod.fmt_sci(r["worst_damage_3000h"], 3),
                gear_mod.fmt_fix(r["max_budget_utilization"], 4),
                gear_mod.fmt_num(r["min_safety_factor"]),
                gear_mod.fmt_sci(r["supported_hours"], 3),
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
        gear_mod.DetailWindow(self, joint)

    def open_grid_chart(self):
        if not self.results:
            return
        gear_mod.GridChartWindow(self, self.results["per_joint"])

    def export_csv(self):
        if not self.results:
            return
        import csv
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


# ============================================================
# Tab 3: 关节摆臂损伤 VS 齿轮接触疲劳
# 对比模块①的伪损伤基准 D1 = (峰值扭矩1)^p x 循环次数1 x 0.5
# 与模块②各关节的伪损伤 D2_i = (等效扭矩2_i)^p x 啮合次数2_i
# 两侧统一用同一个对比用寿命指数 p（默认 6.61，取自模块②的齿轮实测标定值），
# 不修改模块①②各自面板上的指数设置，只在本标签页里读取它们已经算好的结果。
# ============================================================
class ArmVsGearTab(ttk.Frame):
    def __init__(self, parent, tab1, tab2):
        super().__init__(parent)
        self.tab1 = tab1
        self.tab2 = tab2
        self.var_p = tk.StringVar(value="6.61")
        self._build_ui()

    def _build_ui(self):
        title = tk.Label(
            self, text="关节摆臂损伤 VS 齿轮接触疲劳 —— 跨模块伪损伤对比",
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        title.pack(anchor="w", padx=10, pady=(10, 4))

        subtitle = tk.Label(
            self,
            text=("模块①基准：D1 = (峰值扭矩1)^p x 循环次数1 x 0.5\n"
                  "模块②各关节：D2_i = (等效扭矩2_i)^p x 啮合次数2_i\n"
                  "两侧统一使用下方「对比用寿命指数 p」计算，不影响模块①②各自面板上的指数设置；"
                  "D2÷D1 > 1 表示该关节的齿轮接触疲劳损伤已超过摆臂模型给出的基准损伤。"),
            font=("Microsoft YaHei UI", 9), fg="#52514e", justify="left",
        )
        subtitle.pack(anchor="w", padx=10, pady=(0, 10))

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=10, pady=6)
        ttk.Label(ctrl, text="对比用寿命指数 p：").pack(side="left")
        ttk.Entry(ctrl, textvariable=self.var_p, width=10).pack(side="left", padx=(4, 12))
        ttk.Button(ctrl, text="🔄 刷新对比", command=self.refresh).pack(side="left")
        self.status_var = tk.StringVar(value="尚未对比。请先在模块①完成一次计算、在模块②选择数据文件夹完成计算，再点击「刷新对比」。")
        ttk.Label(ctrl, textvariable=self.status_var, foreground="#5a6b7b").pack(side="left", padx=12)

        base_frame = ttk.LabelFrame(self, text="模块①基准值")
        base_frame.pack(fill="x", padx=10, pady=6)
        self.base_var = tk.StringVar(value="—")
        tk.Label(base_frame, textvariable=self.base_var, font=("Consolas", 9),
                 fg="#0b0b0b", justify="left", anchor="w").pack(anchor="w", padx=8, pady=6)

        table_frame = ttk.LabelFrame(self, text="模块②各关节对比结果（点击表头排序）")
        table_frame.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ["legjoint", "teq2", "mesh2", "d2", "ratio", "dominant"]
        col_labels = {
            "legjoint": "关节", "teq2": "等效扭矩2(N·m)", "mesh2": "啮合次数2(3000h)",
            "d2": "D2", "ratio": "D2÷D1", "dominant": "主导方",
        }
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=col_labels[c], command=lambda cc=c: self.sort_by(cc))
            anchor = "w" if c in ("legjoint", "dominant") else "e"
            width = 150 if c in ("legjoint", "dominant") else 130
            self.tree.column(c, width=width, anchor=anchor)
        self.tree.pack(fill="both", expand=True, padx=8, pady=6)
        self.tree.tag_configure("gear_dominant", background="#fdecea", foreground="#a11d1d")
        self.tree.tag_configure("arm_dominant", background="#e8f5e9", foreground="#1b6e1b")

        note = ("说明：模块②每个关节取其最严苛位置的等效扭矩与该位置对应的 3000h 啮合次数（与模块②主表格"
                "「等效扭矩(N·m)」列同一数据来源）。D1 为模块①单次计算给出的整体基准，不区分关节。")
        tk.Label(self, text=note, font=("Microsoft YaHei UI", 8), fg="#898781",
                 wraplength=1120, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        self.sort_key = "ratio"
        self.sort_asc = False
        self.row_data = []

    def refresh(self):
        r1 = self.tab1.last_result
        if r1 is None:
            self.status_var.set("模块①尚无计算结果，请先切到模块①完成一次计算。")
            return
        results2 = self.tab2.results
        if not results2:
            self.status_var.set("模块②尚无计算结果，请先切到模块②选择数据文件夹完成计算。")
            return

        try:
            p = float(self.var_p.get())
            if not (p > 0):
                raise ValueError
        except ValueError:
            self.status_var.set("对比用寿命指数 p 必须是正数，请检查输入。")
            return

        peak_torque1 = float(np.max(np.abs(r1["torque_total"])))
        cycles1 = r1["Life"] * 3600.0 / r1["T_total"]
        D1 = (peak_torque1 ** p) * cycles1 * 0.5

        self.base_var.set(
            "峰值扭矩1 = {:.3f} N·m   循环次数1 = {:.0f}   p = {:.4f}\n"
            "D1 = (峰值扭矩1)^p x 循环次数1 x 0.5 = {:.6e}".format(
                peak_torque1, cycles1, p, D1
            )
        )

        rows = []
        for j in results2["per_joint"]:
            teq2 = j["worst_damage_equiv_torque_Nm"]
            mesh2 = j["worst_mesh_3000h"]
            D2 = (teq2 ** p) * mesh2
            ratio = D2 / D1 if D1 > 0 else float("inf")
            rows.append({
                "leg": j["leg"], "joint": j["joint"],
                "teq2": teq2, "mesh2": mesh2, "d2": D2, "ratio": ratio,
            })
        self.row_data = rows
        self.status_var.set("对比完成 " + time.strftime("%H:%M:%S"))
        self.render_table()

    def sort_by(self, col):
        key_map = {
            "legjoint": lambda r: r["leg"] + r["joint"],
            "teq2": lambda r: r["teq2"],
            "mesh2": lambda r: r["mesh2"],
            "d2": lambda r: r["d2"],
            "ratio": lambda r: r["ratio"],
            "dominant": lambda r: r["ratio"],
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
        if not self.row_data:
            return
        rows = list(self.row_data)
        if sort_fn is None:
            sort_fn = lambda r: r["ratio"]
        rows.sort(key=sort_fn, reverse=not self.sort_asc)

        for r in rows:
            dominant = "齿轮接触疲劳" if r["ratio"] > 1 else "摆臂模型基准"
            tag = "gear_dominant" if r["ratio"] > 1 else "arm_dominant"
            values = (
                "{} {}".format(r["leg"], gear_mod.JOINT_LABEL[r["joint"]]),
                gear_mod.fmt_fix(r["teq2"], 2),
                gear_mod.fmt_sci(r["mesh2"], 3),
                gear_mod.fmt_sci(r["d2"], 3),
                gear_mod.fmt_fix(r["ratio"], 3),
                dominant,
            )
            self.tree.insert("", "end", values=values, tags=(tag,))


# ============================================================
# Hub 主窗口：Notebook 承载三个 Tab，一次性创建、零延迟切换
# ============================================================
class HubApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1440x900")
        self.minsize(1100, 700)

        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 15, "bold"), foreground="#1a5276")
        style.configure("Header.TLabel", font=("Microsoft YaHei UI", 11, "bold"), foreground="#1a5276")
        style.configure("KPI.TLabel", font=("Microsoft YaHei UI", 13, "bold"), foreground="#1a5276")
        style.configure("KPIcap.TLabel", font=("Microsoft YaHei UI", 9), foreground="#5a6b7b")
        style.configure("Run.TButton", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Sub.TLabel", font=("Microsoft YaHei UI", 9), foreground="#5a6b7b")
        style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 10, "bold"), padding=(14, 7))

        header = ttk.Frame(self, padding=(14, 10, 14, 4))
        header.pack(fill="x")
        ttk.Label(header, text="🛠 " + APP_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="切换下方标签页即可直接查看各模块的完整界面与计算结果，无需跳转到其他窗口。",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab1 = None
        self.tab2 = None

        try:
            self.tab1 = JointLifeTab(notebook)
            notebook.add(self.tab1, text="① 关节摆臂寿命计算")
        except Exception:
            err = ttk.Frame(notebook)
            tk.Label(err, text="模块加载失败，详情：\n" + traceback.format_exc(),
                     fg="#a11d1d", justify="left", anchor="nw").pack(fill="both", expand=True, padx=10, pady=10)
            notebook.add(err, text="① 关节摆臂寿命计算（加载失败）")

        try:
            self.tab2 = GearFatigueTab(notebook)
            notebook.add(self.tab2, text="② WS2.5 齿轮接触疲劳")
        except Exception:
            err = ttk.Frame(notebook)
            tk.Label(err, text="模块加载失败，详情：\n" + traceback.format_exc(),
                     fg="#a11d1d", justify="left", anchor="nw").pack(fill="both", expand=True, padx=10, pady=10)
            notebook.add(err, text="② WS2.5 齿轮接触疲劳（加载失败）")

        try:
            if self.tab1 is not None and self.tab2 is not None:
                tab3 = ArmVsGearTab(notebook, self.tab1, self.tab2)
                notebook.add(tab3, text="③ 关节摆臂损伤 VS 齿轮接触疲劳")
            else:
                raise RuntimeError("模块①或模块②未能正常加载，无法进行跨模块对比。")
        except Exception:
            err = ttk.Frame(notebook)
            tk.Label(err, text="模块加载失败，详情：\n" + traceback.format_exc(),
                     fg="#a11d1d", justify="left", anchor="nw").pack(fill="both", expand=True, padx=10, pady=10)
            notebook.add(err, text="③ 关节摆臂损伤 VS 齿轮接触疲劳（加载失败）")


def main():
    try:
        app = HubApp()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(APP_TITLE, "程序启动失败：\n" + traceback.format_exc())
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
