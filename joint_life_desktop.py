# -*- coding: utf-8 -*-
"""
关节摆臂疲劳寿命计算工具 - 桌面版主程序
纯本地 Tkinter 窗口应用，不依赖浏览器、不占用网络端口。
双击 启动关节摆臂寿命计算工具.bat 即可运行。
"""

import os
import sys
import time
import traceback
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import joint_life_core as core

APP_TITLE = "关节摆臂疲劳寿命计算工具（本地桌面版）"
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".instance.lock")


def acquire_single_instance_lock():
    """
    检查锁文件中记录的 PID 是否还存活，自动清理上次异常退出残留的锁文件，
    保证每次启动都不会被历史异常状态卡住。
    """
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            is_alive = True
        except Exception:
            is_alive = False
        if is_alive:
            return False
        else:
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass
    try:
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    return True


def release_single_instance_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError:
        pass


class JointLifeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1440x900")
        self.minsize(1100, 700)

        self._build_vars()
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        self.var_life_exponent = tk.DoubleVar(value=10/3)
        self.var_C_rated = tk.DoubleVar(value=6.03)
        self.var_N_ref = tk.DoubleVar(value=100)
        self.var_L10_ref = tk.DoubleVar(value=3000)
        self.var_status = tk.StringVar(value="就绪")

    def _build_layout(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Header.TLabel", font=("Microsoft YaHei UI", 11, "bold"), foreground="#1a5276")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 15, "bold"))
        style.configure("KPI.TLabel", font=("Microsoft YaHei UI", 13, "bold"), foreground="#1a5276")
        style.configure("KPIcap.TLabel", font=("Microsoft YaHei UI", 9), foreground="#5a6b7b")
        style.configure("Run.TButton", font=("Microsoft YaHei UI", 11, "bold"))

        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="🤖 " + APP_TITLE, style="Title.TLabel").pack(anchor="w", pady=(0, 8))

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
        self.text_summary = tk.Text(left, width=52, height=40, font=("Consolas", 9),
                                     bg="#0f1c28", fg="#d5e8d4", wrap="word")
        self.text_summary.pack(fill="y", expand=True)
        self.text_summary.insert("1.0", "点击「开始计算」查看结果…")
        self.text_summary.config(state="disabled")

        right = ttk.Frame(result_frame)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="📊 分析图表", style="Header.TLabel").pack(anchor="w")

        self.fig = Figure(figsize=(11, 8.5), dpi=100)
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
        self._apply_preset(100, 120, -150, 0.3, 5.176, 2.0, 9.80, "安克 (0.1828+I_load)", 0.0, 10/3, 6.03, 100, 3000)

    def preset_sanhua(self):
        self._apply_preset(100, 120, -150, 0.3, 2.7, 2.65, 9.80, "三花 (0.095+I_load)", 0.0, 10/3, 6.03, 100, 3000)

    def preset_high(self):
        self._apply_preset(150, 120, -150, 0.3, 5.176, 2.0, 9.80, "安克 (0.1828+I_load)", 0.0, 10/3, 6.03, 100, 3000)

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
            r = core.calculate_life(**params)
            if not np.isfinite(r["Life"]) or not np.isfinite(r["Teq"]):
                raise ValueError("结果发散，请检查参数取值范围")

            summary = core.build_summary(r)
            self.text_summary.config(state="normal")
            self.text_summary.delete("1.0", "end")
            self.text_summary.insert("1.0", summary)
            self.text_summary.config(state="disabled")

            self.kpi_labels["life"].config(text=f"{r['Life']:.1f}")
            self.kpi_labels["cycles"].config(text=f"{(r['Life']*3600/r['T_total']):.0f}")
            self.kpi_labels["teq"].config(text=f"{r['Teq']:.3f}")
            self.kpi_labels["tmax"].config(text=f"{np.max(np.abs(r['torque_total'])):.2f}")
            self.kpi_labels["integral"].config(text=f"{r['fatigue_integral']:.3e}")

            core.create_figures(self.fig, r)
            self.canvas.draw_idle()

            self.var_status.set("✅ 计算完成 " + time.strftime("%H:%M:%S"))
        except Exception as e:
            self.var_status.set("❌ 计算出错")
            messagebox.showerror("计算错误", f"{e}\n\n详细信息已记录，可关闭本提示后调整参数重试。")
            traceback.print_exc()

    def _on_close(self):
        release_single_instance_lock()
        self.destroy()


def main():
    if not acquire_single_instance_lock():
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            APP_TITLE,
            "检测到工具已经在运行中。\n\n"
            "如果确认之前的窗口已经关闭但仍看到此提示，\n"
            "说明上次是异常退出导致锁文件残留，请再次启动本程序，\n"
            "系统会自动清理残留状态。"
        )
        root.destroy()
        return

    try:
        app = JointLifeApp()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(APP_TITLE, "程序启动失败，请查看 logs 目录下的日志文件。")
            root.destroy()
        except Exception:
            pass
    finally:
        release_single_instance_lock()


if __name__ == "__main__":
    main()
