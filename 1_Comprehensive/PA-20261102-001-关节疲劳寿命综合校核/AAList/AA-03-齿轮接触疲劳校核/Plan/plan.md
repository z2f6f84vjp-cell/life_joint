# Plan(执行计划)

## 执行前准备

### 资源引用
- D:\7_tool\geer_cycle\gear_fatigue_tool.py: compute_all(parsed, params) -> per_joint, per_pos_all, D_allow, K
- D:\7_tool\geer_cycle\gear_fatigue_tool.py: augment_with_pct_and_risk(joint)(80%风险位置)
- D:\7_tool\geer_cycle\gear_fatigue_tool.py: DetailWindow / GridChartWindow(损伤-位置分布图,仅桌面端)

---

## 整体执行步骤说明
共 8 步,按顺序执行,任一校验失败即中止并说明原因。

---

## 详细执行步骤
1. 读取 gear_params.json 与 12 个关节矩阵
2. K=LH×3600/TW;D_allow=TR^M×NR
3. 对每个位置每个扭矩级(圈数z>0):单边啮合次数 n=z×TEETH/SIDE;损伤 d=|T|^M×n
4. 位置级: Teq=(Σd/Σn)^(1/M);mesh3000=Σn×K;D3000=Σd×K
5. U=D3000/TR^M/NR;SF=1/U;支持寿命=SF×LH;U<=1 判 PASS 否则 FAIL
6. 关节级: 取U最大的位置为最严苛位置,不跨位置累加;统计失效位置数
7. 对每个关节按损伤占比降序累计至80%,标出风险位置
8. 导出位置级CSV与关节级汇总CSV(utf-8-sig)

---

## 输出当前活动产物
- gear_result.json(per_joint/per_pos_all/D_allow/K)
- gear_per_position.csv
- gear_per_position_summary.csv
- gear_damage_position.md(各关节80%损伤风险位置清单)

---

## 后置检查

### 执行步骤完整性检查
逐条对照 Checklist,全部满足才算完成。

### 更新待办项
完成后在 WBS 中把 AA-03 标记为已完成。

### 整体输出内容检查
产物文件齐全,数值可追溯到本 AA 的计算结果。

---
