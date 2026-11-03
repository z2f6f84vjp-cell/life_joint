# Plan(执行计划)

## 执行前准备

### 资源引用
- D:\7_tool\joint_life_core.py: calculate_life(v_max_rpm, theta_max_deg, theta_start_deg, L, m_arm, m_load, g, inertia_mode, custom_I, life_exponent, C_rated, N_ref, L10_ref)
- D:\7_tool\joint_life_core.py: build_summary(r) / create_figures(fig, r)
- 依赖: numpy>=2.0(使用 np.trapezoid), matplotlib

---

## 整体执行步骤说明
共 8 步,按顺序执行,任一校验失败即中止并说明原因。

---

## 详细执行步骤
1. 读取 arm_params.json
2. 调用双S曲线规划得到 t/jerk/accel/vel/pos,Ts=Δθ/(3ω_max),T_total=6Ts
3. 按惯量模式得 I_total;总扭矩=I_total×accel + (m_arm·g·L/2+m_load·g·L)·cos(pos)
4. 疲劳被积函数 n·|τ|^p,梯形积分得 fatigue_integral
5. L_val=积分/T_total;Life=N_ref·L10_ref·C^p/L_val;Teq=(积分/(N_ref·T_total))^(1/p)
6. 循环次数 cycles = Life×3600/T_total;峰值扭矩=max|τ|
7. 检查 Life/Teq 有限,发散则报错并提示调整参数
8. 生成摘要文本与3x3图表,落盘

---

## 输出当前活动产物
- arm_result.json(Life/Teq/T_total/peak_torque/fatigue_integral/cycles)
- arm_summary.md(运动学/惯量扭矩/疲劳积分/测试寿命)
- arm_figures.png(3x3分析图)

---

## 后置检查

### 执行步骤完整性检查
逐条对照 Checklist,全部满足才算完成。

### 更新待办项
完成后在 WBS 中把 AA-02 标记为已完成。

### 整体输出内容检查
产物文件齐全,数值可追溯到本 AA 的计算结果。

---
