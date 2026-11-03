# Plan(执行计划)

## 执行前准备

### 资源引用
- D:\7_tool\geer_cycle\gear_fatigue_tool.py: match_key / parse_csv / load_folder(folder) -> parsed, matched, missing, unmatched, need
- D:\7_tool\geer_cycle\gear_fatigue_tool.py: DEFAULTS(齿轮参数默认值)
- D:\7_tool\1_Comprehensive\comprehensive_hub.py: JointLifeTab._read_and_validate(摆臂参数校验规则)

---

## 整体执行步骤说明
共 7 步,按顺序执行,任一校验失败即中止并说明原因。

---

## 详细执行步骤
1. 确认用户选择预设或手动给出摆臂参数,缺项按预设补全并回显
2. 校验: 转速、总角位移、臂长、p、C、N_ref、L10_ref 必须>0;非数字直接报错
3. 校验齿轮文件夹: 按文件名归一化(去空格/下划线,忽略大小写)匹配 12 个 leg×joint
4. 缺失任一文件则中止并列出缺失项;重复匹配的文件标记为忽略
5. 校验每个CSV含 #TITLES 与 #DATA 标记,扭矩级与位置数写入报告
6. 齿轮参数7项均须>0,否则回退并提示
7. 输出标准化输入包给 AA-02 / AA-03

---

## 输出当前活动产物
- arm_params.json(已校验的摆臂参数)
- gear_params.json(已校验的齿轮参数)
- gear_files_report.md(12个文件匹配/缺失/重复清单)

---

## 后置检查

### 执行步骤完整性检查
逐条对照 Checklist,全部满足才算完成。

### 更新待办项
完成后在 WBS 中把 AA-01 标记为已完成。

### 整体输出内容检查
产物文件齐全,数值可追溯到本 AA 的计算结果。

---
