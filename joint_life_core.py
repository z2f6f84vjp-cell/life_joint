# -*- coding: utf-8 -*-
"""
关节摆臂疲劳寿命计算工具 - 核心算法模块
基于双S曲线运动规划（6段，无匀速段）+ 疲劳寿命积分
与原 Gradio 版 joint_life_tool.py 算法完全一致。
"""

import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def dual_s_curve_motion(L, v_max_rpm, theta_max_deg, theta_start_deg):
    """双S曲线6段运动规划（无匀速段）"""
    omega_max = v_max_rpm * 2 * np.pi / 60
    theta_total = theta_max_deg * np.pi / 180
    theta_start = theta_start_deg * np.pi / 180

    Ts = theta_total / (3 * omega_max)
    T_total = 6 * Ts
    alpha_max = omega_max / (2 * Ts)
    jerk_max = omega_max / (2 * Ts**2)

    dt = 0.001
    t = np.arange(0, T_total + dt, dt)
    N = len(t)

    jerk = np.zeros(N)
    accel = np.zeros(N)
    vel = np.zeros(N)
    pos = np.zeros(N)

    t1, t2, t3 = Ts, 2*Ts, 3*Ts
    t4, t5, t6 = 4*Ts, 5*Ts, 6*Ts

    for i in range(N):
        ti = t[i]
        if ti < t1:
            tau = ti
            jerk[i] = jerk_max
            accel[i] = jerk_max * tau
            vel[i] = 0.5 * jerk_max * tau**2
            pos[i] = (1/6) * jerk_max * tau**3
        elif ti < t2:
            tau = ti - t1
            jerk[i] = 0
            accel[i] = alpha_max
            vel[i] = 0.5 * jerk_max * Ts**2 + alpha_max * tau
            pos[i] = (1/6)*jerk_max*Ts**3 + 0.5*jerk_max*Ts**2*tau + 0.5*alpha_max*tau**2
        elif ti < t3:
            tau = ti - t2
            jerk[i] = -jerk_max
            accel[i] = alpha_max - jerk_max * tau
            vel[i] = 0.5*jerk_max*Ts**2 + alpha_max*Ts + alpha_max*tau - 0.5*jerk_max*tau**2
            pos_2 = (1/6)*jerk_max*Ts**3 + 0.5*jerk_max*Ts**2*Ts + 0.5*alpha_max*Ts**2
            pos[i] = pos_2 + (0.5*jerk_max*Ts**2+alpha_max*Ts)*tau + 0.5*alpha_max*tau**2 - (1/6)*jerk_max*tau**3
        elif ti < t4:
            tau = ti - t3
            jerk[i] = -jerk_max
            accel[i] = -jerk_max * tau
            vel[i] = omega_max - 0.5 * jerk_max * tau**2
            pos_3 = 1.5 * omega_max * Ts
            pos[i] = pos_3 + omega_max*tau - (1/6)*jerk_max*tau**3
        elif ti < t5:
            tau = ti - t4
            jerk[i] = 0
            accel[i] = -alpha_max
            vel[i] = omega_max - 0.5*jerk_max*Ts**2 - alpha_max*tau
            pos_4 = 1.5*omega_max*Ts + omega_max*Ts - (1/6)*jerk_max*Ts**3
            pos[i] = pos_4 + (omega_max-0.5*jerk_max*Ts**2)*tau - 0.5*alpha_max*tau**2
        else:
            tau = ti - t5
            jerk[i] = jerk_max
            accel[i] = -alpha_max + jerk_max * tau
            vel[i] = omega_max - 0.5*jerk_max*Ts**2 - alpha_max*Ts - alpha_max*tau + 0.5*jerk_max*tau**2
            pos_5 = 1.5*omega_max*Ts + omega_max*Ts - (1/6)*jerk_max*Ts**3 + (omega_max-0.5*jerk_max*Ts**2)*Ts - 0.5*alpha_max*Ts**2
            pos[i] = pos_5 + (omega_max-0.5*jerk_max*Ts**2-alpha_max*Ts)*tau - 0.5*alpha_max*tau**2 + (1/6)*jerk_max*tau**3

    pos = pos + theta_start
    return t, jerk, accel, vel, pos, Ts, T_total, alpha_max, jerk_max, omega_max


def calculate_life(v_max_rpm, theta_max_deg, theta_start_deg, L,
                    m_arm, m_load, g, inertia_mode, custom_I,
                    life_exponent, C_rated, N_ref, L10_ref):
    """核心计算函数，返回结果字典（不含绘图）"""
    t, jerk, accel, vel, pos, Ts, T_total, alpha_max, jerk_max, omega_max = \
        dual_s_curve_motion(L, v_max_rpm, theta_max_deg, theta_start_deg)

    I_arm = (1/3) * m_arm * L**2
    I_load = m_load * L**2
    if inertia_mode == "安克 (0.1828+I_load)":
        I_total = 0.1828 + I_load
    elif inertia_mode == "三花 (0.095+I_load)":
        I_total = 0.095 + I_load
    elif inertia_mode == "理论 (I_arm+I_load)":
        I_total = I_arm + I_load
    else:
        I_total = custom_I + I_load

    gravity_coeff = m_arm * g * (L/2) + m_load * g * L

    torque_inertia = I_total * accel
    torque_gravity = gravity_coeff * np.cos(pos)
    torque_total = torque_inertia + torque_gravity

    speed_rpm = vel * 60 / (2*np.pi)

    torque_abs = np.abs(torque_total)
    fatigue_integrand = speed_rpm * (torque_abs ** life_exponent)
    fatigue_integral = np.trapezoid(fatigue_integrand, t)

    L_val = fatigue_integral / T_total
    Life = (N_ref * L10_ref * (C_rated ** life_exponent)) / L_val
    Teq = (fatigue_integral / (N_ref * T_total)) ** (1/life_exponent)

    return dict(
        t=t, jerk=jerk, accel=accel, vel=vel, pos=pos,
        torque_inertia=torque_inertia, torque_gravity=torque_gravity, torque_total=torque_total,
        Ts=Ts, T_total=T_total, alpha_max=alpha_max, jerk_max=jerk_max, omega_max=omega_max,
        I_arm=I_arm, I_load=I_load, I_total=I_total,
        fatigue_integrand=fatigue_integrand, fatigue_integral=fatigue_integral,
        L_val=L_val, Life=Life, Teq=Teq,
        v_max_rpm=v_max_rpm, theta_max_deg=theta_max_deg, theta_start_deg=theta_start_deg,
        life_exponent=life_exponent, N_ref=N_ref,
    )


def build_summary(r):
    sep = "=" * 45
    torque_total = r["torque_total"]
    torque_abs = np.abs(torque_total)
    return f"""
{sep}
【运动学参数】
{sep}
  每段时长 Ts = {r['Ts']:.4f} s
  总运动时间 T = {r['T_total']:.4f} s
  最大角速度 = {r['omega_max']:.2f} rad/s ({r['v_max_rpm']} rpm)
  最大加速度 = {r['alpha_max']:.2f} rad/s2 ({r['alpha_max']*180/np.pi:.1f} deg/s2)
  最大加加速度 = {r['jerk_max']:.2f} rad/s3 ({r['jerk_max']*180/np.pi:.1f} deg/s3)

{sep}
【惯量与扭矩】
{sep}
  摆臂转动惯量 = {r['I_arm']:.4f} kg*m2
  负载转动惯量 = {r['I_load']:.4f} kg*m2
  总转动惯量 = {r['I_total']:.4f} kg*m2
  扭矩范围 = [{np.min(torque_total):.2f}, {np.max(torque_total):.2f}] N*m
  扭矩绝对值范围 = [{np.min(torque_abs):.2f}, {np.max(torque_abs):.2f}] N*m

{sep}
【疲劳寿命积分】
{sep}
  寿命指数 p = {r['life_exponent']}
  疲劳积分 = {r['fatigue_integral']:.4e}
  等效时间 L = {r['L_val']:.4e}
  等效扭矩 Teq ({r['N_ref']}rpm) = {r['Teq']:.3f} N*m

{sep}
【测试寿命】
{sep}
  测试寿命（等效运行时间） 约 {r['Life']:.1f} 小时
  相当于可完成 约 {(r['Life']*3600/r['T_total']):.0f} 次测试循环（每次循环 {r['T_total']:.3f} s）
"""


def create_figures(fig, r):
    """在传入的 Figure 上绘制 3x3 分析图（复用已有 Figure，避免重复创建窗口）"""
    fig.clear()
    axes = fig.subplots(3, 3)
    fig.suptitle('关节摆臂双S曲线 - 寿命计算报告', fontsize=13, fontweight='bold', color='#1a5276')

    t = r["t"]; T_total = r["T_total"]; Ts = r["Ts"]
    jerk = r["jerk"]; accel = r["accel"]; vel = r["vel"]; pos = r["pos"]
    torque_inertia = r["torque_inertia"]; torque_gravity = r["torque_gravity"]; torque_total = r["torque_total"]
    fatigue_integrand = r["fatigue_integrand"]; fatigue_integral = r["fatigue_integral"]
    alpha_max = r["alpha_max"]; omega_max = r["omega_max"]; jerk_max = r["jerk_max"]
    theta_max_deg = r["theta_max_deg"]; theta_start_deg = r["theta_start_deg"]; v_max_rpm = r["v_max_rpm"]
    life_exponent = r["life_exponent"]

    time_points = np.array([1, 2, 3, 4, 5, 6]) * Ts
    colors = ['#e74c3c', '#e67e22', '#2980b9', '#27ae60', '#8e44ad', '#16a085']

    ax = axes[0, 0]
    ax.plot(t, jerk*180/np.pi, 'r-', linewidth=1.5, label='Jerk')
    ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('角加加速度 (deg/s3)', fontsize=8)
    ax.set_title(f'角加加速度 (J_max={jerk_max*180/np.pi:.0f} deg/s3)', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=7); ax.tick_params(labelsize=7)

    ax = axes[0, 1]
    ax.plot(t, accel*180/np.pi, 'orange', linewidth=1.5, label='Accel')
    ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax.axhline(y=alpha_max*180/np.pi, color='r', linestyle=':', alpha=0.4)
    ax.axhline(y=-alpha_max*180/np.pi, color='r', linestyle=':', alpha=0.4)
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('角加速度 (deg/s2)', fontsize=8)
    ax.set_title(f'角加速度 (a_max={alpha_max*180/np.pi:.0f} deg/s2)', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=7); ax.tick_params(labelsize=7)

    ax = axes[0, 2]
    ax.plot(t, vel*180/np.pi, 'b-', linewidth=1.5, label='Velocity')
    ax.axhline(y=omega_max*180/np.pi, color='r', linestyle='--', alpha=0.5)
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total]); ax.set_ylim([0, np.max(vel)*180/np.pi*1.1])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('角速度 (deg/s)', fontsize=8)
    ax.set_title(f'角速度 (w_max={v_max_rpm} rpm)', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=7); ax.tick_params(labelsize=7)

    ax = axes[1, 0]
    ax.plot(t, pos*180/np.pi, 'g-', linewidth=1.5, label='Position')
    ax.axhline(y=theta_start_deg, color='r', linestyle='--', alpha=0.4, label=f'起始({theta_start_deg}°)')
    ax.axhline(y=theta_start_deg+theta_max_deg, color='m', linestyle='--', alpha=0.4,
               label=f'终止({theta_start_deg+theta_max_deg}°)')
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('角位移 (°)', fontsize=8)
    ax.set_title(f'角位移 (Δθ={theta_max_deg}°)', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=6); ax.tick_params(labelsize=7)

    ax = axes[1, 1]
    ax.plot(t, torque_inertia, color='#e74c3c', linewidth=1.2, label='惯性扭矩', alpha=0.7)
    ax.plot(t, torque_gravity, color='#27ae60', linewidth=1.2, label='重力扭矩', alpha=0.7)
    ax.plot(t, torque_total, 'b-', linewidth=2, label='总扭矩')
    ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('扭矩 (N*m)', fontsize=8)
    ax.set_title(f'扭矩分解 ({np.min(torque_total):.1f}~{np.max(torque_total):.1f} N*m)', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=6); ax.tick_params(labelsize=7)

    ax = axes[1, 2]
    torque_abs = np.abs(torque_total)
    ax.fill_between(t, 0, torque_abs, alpha=0.3, color='blue')
    ax.plot(t, torque_abs, 'b-', linewidth=1.5, label='|tau|')
    ax.axhline(y=np.max(torque_abs), color='r', linestyle='--', alpha=0.5, label=f'Max={np.max(torque_abs):.1f}')
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('|扭矩| (N*m)', fontsize=8)
    ax.set_title('扭矩绝对值', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=7); ax.tick_params(labelsize=7)

    ax = axes[2, 0]
    ax.plot(t, fatigue_integrand, 'purple', linewidth=1.5, label=f'n*|tau|^{life_exponent:.2f}')
    ax.fill_between(t, 0, fatigue_integrand, alpha=0.2, color='purple')
    for tp in time_points:
        ax.axvline(x=tp, color=colors[1], linestyle='--', alpha=0.3)
    ax.set_xlim([0, T_total])
    ax.set_xlabel('时间 (s)', fontsize=8); ax.set_ylabel('n*|tau|^p', fontsize=8)
    ax.set_title(f'被积函数 (∫={fatigue_integral:.2e})', fontsize=9)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=7); ax.tick_params(labelsize=7)

    ax = axes[2, 1]
    scatter = ax.scatter(pos*180/np.pi, torque_total, c=t, cmap='viridis', s=2, alpha=0.8)
    ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax.set_xlabel('角位移 (°)', fontsize=8); ax.set_ylabel('扭矩 (N*m)', fontsize=8)
    ax.set_title('扭矩-角位移 相位图', fontsize=9)
    ax.grid(True, alpha=0.3); ax.tick_params(labelsize=7)
    fig.colorbar(scatter, ax=ax, label='时间 (s)')

    ax = axes[2, 2]
    ax.barh(['测试寿命(循环)'], [fatigue_integral], color='#3498db', height=0.4, alpha=0.8,
            label=f'疲劳积分={fatigue_integral:.2e}')
    ax.set_title(f'疲劳积分 = {fatigue_integral:.2e}', fontsize=9)
    ax.set_xlabel('疲劳积分值', fontsize=8)
    ax.legend(fontsize=7, loc='lower right'); ax.grid(True, alpha=0.3, axis='x')
    ax.tick_params(labelsize=7)

    fig.tight_layout()
