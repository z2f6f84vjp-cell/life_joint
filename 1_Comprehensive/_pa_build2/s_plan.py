# -*- coding: utf-8 -*-
PA_TITLE = "关节疲劳寿命综合校核"
PA_SLUG = "joint-fatigue-life-check"

ROLES = [
    ("R-01", "校核执行引擎", "AI虚拟", "按流程调用原工具函数完成校核并运行质量门禁"),
    ("R-02", "校核工程师", "人工", "提供参数与数据 确认参数 处置门禁失败 评审结果"),
]
PHASES = [
    ("S-01", "输入准备", "校验参数与数据并由人工确认"),
    ("S-02", "并行计算", "摆臂寿命计算与齿轮接触疲劳校核"),
    ("S-03", "对比与交付", "跨模块对比 报告生成与人工评审"),
]

# id, name, phase, role, desc, inputs, outputs, stage, human
AAS = [
    ("AA-01", "参数与数据准备", "S-01", "R-01",
     "解析预设与覆盖项 校验摆臂与齿轮参数 匹配并校验12个齿轮CSV 清除旧的下游结果",
     ["预设名", "摆臂覆盖参数", "齿轮覆盖参数", "齿轮数据文件夹"],
     ["arm_params.json", "gear_params.json", "gear_files_report.md"], "prepare", False),
    ("AA-02", "关节摆臂疲劳寿命计算", "S-02", "R-01",
     "按双S曲线运动规划与扭矩积分计算摆臂测试寿命 等效扭矩 疲劳积分并出图",
     ["arm_params.json"], ["arm_result.json", "arm_summary.md", "arm_figures.png"], "arm", False),
    ("AA-03", "齿轮接触疲劳校核", "S-02", "R-01",
     "对12个关节逐位置计算单边啮合损伤并与额定预算对比 取各关节最严苛位置判定PASS或FAIL",
     ["gear_params.json", "12个齿轮CSV"],
     ["gear_result.json", "gear_per_position.csv", "gear_per_position_summary.csv", "gear_damage_position.md"],
     "gear", False),
    ("AA-04", "跨模块伪损伤对比", "S-03", "R-01",
     "用同一寿命指数p对比摆臂基准损伤D1与各关节齿轮损伤D2 判断主导损伤来源",
     ["arm_result.json", "gear_result.json", "对比用寿命指数p"],
     ["compare_result.json", "compare_table.csv", "compare_conclusion.md"], "compare", False),
    ("AA-05", "结果汇总与报告生成", "S-03", "R-01",
     "汇总三类结果生成结论先行的综合校核报告 列出FAIL 近预算与齿轮主导的风险项",
     ["arm_result.json", "gear_result.json", "compare_result.json"],
     ["综合校核报告.md", "report_summary.json"], "report", False),
    ("AA-06", "参数确认与问题处置", "S-01", "R-02",
     "回显参数与文件清单并取得确认 门禁失败时展示失败项与证据并决定修正或终止",
     ["arm_params.json", "gear_params.json", "gear_files_report.md", "门禁失败证据"],
     ["确认结论", "修正意见"], None, True),
    ("AA-07", "结果评审", "S-03", "R-02",
     "评审综合校核报告 决定接受 调整参数重算或补充数据",
     ["综合校核报告.md", "compare_conclusion.md", "arm_figures.png"], ["评审结论", "调整意见"], None, True),
]
# id, name, phase, role, desc, check_obj, check_out, gates
CAS = [
    ("CA-01", "输入门禁", "S-01", "R-01", "核对参数与数据准备阶段的产物齐全且非空",
     ["arm_params.json", "gear_params.json", "gear_files_report.md"], ["gate_prepare.json"], ["prepare"]),
    ("CA-02", "计算结果门禁", "S-02", "R-01", "核对摆臂与齿轮计算结果的有限性 守恒关系与判定一致性",
     ["arm_result.json", "gear_result.json"], ["gate_arm.json", "gate_gear.json"], ["arm", "gear"]),
    ("CA-03", "交付门禁", "S-03", "R-01", "核对对比结果与报告的完整性并确认FAIL关节全部列入报告",
     ["compare_result.json", "综合校核报告.md"], ["gate_compare.json", "gate_report.json"], ["compare", "report"]),
]
# id, from, to, type, dir, cond, maxloop
EDGES = [
    ("E-01", "AA-01", "CA-01", "串行", "→", "", ""),
    ("E-02", "CA-01", "AA-06", "条件分支", "→", "门禁=PASS", ""),
    ("E-03", "CA-01", "AA-06", "条件分支", "→", "门禁=FAIL", ""),
    ("E-04", "AA-06", "AA-01", "条件分支", "↺", "需修正输入", "3"),
    ("E-05", "AA-06", "AA-02", "条件分支", "→", "参数确认通过", ""),
    ("E-06", "AA-06", "AA-03", "条件分支", "→", "参数确认通过", ""),
    ("E-07", "AA-02", "CA-02", "串行", "→", "", ""),
    ("E-08", "AA-03", "CA-02", "串行", "→", "", ""),
    ("E-09", "CA-02", "AA-04", "条件分支", "→", "门禁=PASS", ""),
    ("E-10", "CA-02", "AA-06", "条件分支", "↺", "门禁=FAIL", "3"),
    ("E-11", "AA-04", "AA-05", "串行", "→", "", ""),
    ("E-12", "AA-05", "CA-03", "串行", "→", "", ""),
    ("E-13", "CA-03", "AA-07", "条件分支", "→", "门禁=PASS", ""),
    ("E-14", "CA-03", "AA-06", "条件分支", "↺", "门禁=FAIL", "3"),
    ("E-15", "AA-07", "AA-01", "条件分支", "↺", "评审要求调整参数重算", "3"),
]
LOOPS = [
    ("LOOP-1", "E-04", "输入修正回路: 校核工程师修正参数或数据后回到AA-01重新准备"),
    ("LOOP-2", "E-10、E-14", "门禁失败处置回路: 计算或交付门禁失败后回到AA-06由人工处置"),
    ("LOOP-3", "E-15", "评审调整回路: 评审要求调整参数后回到AA-01重算"),
]


def cells(items):
    return "、".join(items)


def render_plan():
    L = ["# " + PA_TITLE, "", "## 角色", "| 角色编号 | 角色名称 | 角色类型 | 角色描述 |", "|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |" % r for r in ROLES]
    L += ["", "## 阶段", "| 阶段编号 | 阶段名称 | 阶段描述 |", "|---|---|---|"]
    L += ["| %s | %s | %s |" % p for p in PHASES]
    L += ["", "## 活动节点", "| 节点编号 | 节点名称 | 所属阶段 | 参与角色 | 节点描述 | 节点输入 | 节点输出 |", "|---|---|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | %s | %s | %s |" % (a[0], a[1], a[2], a[3], a[4], cells(a[5]), cells(a[6])) for a in AAS]
    L += ["", "## 检查节点", "| 节点编号 | 节点名称 | 所属阶段 | 参与角色 | 节点描述 | 检查对象 | 检查输出 |", "|---|---|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | %s | %s | %s |" % (c[0], c[1], c[2], c[3], c[4], cells(c[5]), cells(c[6])) for c in CAS]
    L += ["", "## 边", "| 边编号 | 起点 | 终点 | 边类型 | 方向 | 条件 | 最大循环次数 |", "|---|---|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | %s | %s | %s |" % e for e in EDGES]
    L += ["", "## 循环回路收敛规则", "",
          "| 回路 | 边 | 说明 | max_attempts | 幂等契约 | 超限后 |", "|---|---|---|---|---|---|"]
    L += ["| %s | %s | %s | 3 | 重跑覆盖同名文件 且prepare先清除全部下游结果 | 终止并把门禁证据交给校核工程师与工具维护人 |" % l for l in LOOPS]
    L += ["", "说明: 运行脚本的每条命令彼此独立 不记录回路轮次 轮次由PA在对话中计数并在AA-06记录 超过3轮必须终止。",
          "", "## 依赖说明", "",
          "- AA-02与AA-03只依赖AA-06确认后的AA-01产物 互不依赖 可并行。",
          "- AA-04必须等CA-02对AA-02和AA-03的门禁都通过。",
          "- AA-05只读取AA-02 AA-03 AA-04已落盘的文件 不重新计算。",
          "- 入口节点为AA-01 末端节点为AA-07 流程终点由AA-07的评审结论决定。"]
    return "\n".join(L)
