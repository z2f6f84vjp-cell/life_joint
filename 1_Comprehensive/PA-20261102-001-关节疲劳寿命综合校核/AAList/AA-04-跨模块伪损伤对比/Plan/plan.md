# Plan(执行计划)

## 执行前准备

### 资源引用
- D:\7_tool\1_Comprehensive\comprehensive_hub.py: ArmVsGearTab.refresh()(D1/D2/ratio 计算口径)
- 无需新增算法,按上述公式复算即可

---

## 整体执行步骤说明
共 7 步,按顺序执行,任一校验失败即中止并说明原因。

---

## 详细执行步骤
1. 确认 AA-02、AA-03 均已产出结果,缺任一则中止并提示补跑
2. 校验对比用 p>0(默认取 6.61)
3. D1=(峰值扭矩1)^p×循环次数1×0.5,其中循环次数1=Life×3600/T_total
4. 对每个关节取最严苛位置: teq2、mesh2(3000h啮合次数)
5. D2=(teq2)^p×mesh2;ratio=D2÷D1
6. ratio>1 判齿轮接触疲劳主导,否则摆臂模型基准主导
7. 按 ratio 降序输出,汇总主导关节数量与最大比值关节

---

## 输出当前活动产物
- compare_result.json
- compare_table.csv(关节/等效扭矩2/啮合次数2/D2/D2÷D1/主导方)
- compare_conclusion.md

---

## 后置检查

### 执行步骤完整性检查
逐条对照 Checklist,全部满足才算完成。

### 更新待办项
完成后在 WBS 中把 AA-04 标记为已完成。

### 整体输出内容检查
产物文件齐全,数值可追溯到本 AA 的计算结果。

---
