# -*- coding: utf-8 -*-
CMD = "python runtime/run_pa.py"

# 工具规格: 薄封装 只引用既有脚本与函数
TOOLS = [
    dict(id="T-01", name="run_pa prepare", script="runtime/run_pa.py prepare",
         wraps="runtime/vendor/gear_fatigue_tool.py: load_folder",
         args="--out DIR --preset anker|sanhua|high --arm K=V(可重复) --gear K=V(可重复) --gear-folder DIR",
         timeout="30秒", exits="0成功 2校验失败或门禁失败",
         io="读: 12个CSV 写: arm_params.json gear_params.json gear_files_report.md gate_prepare.json 并清除旧下游结果"),
    dict(id="T-02", name="run_pa arm", script="runtime/run_pa.py arm",
         wraps="runtime/vendor/joint_life_core.py: calculate_life build_summary create_figures",
         args="--out DIR", timeout="60秒", exits="0成功 2结果发散或门禁失败",
         io="读: arm_params.json 写: arm_result.json arm_summary.md arm_figures.png gate_arm.json"),
    dict(id="T-03", name="run_pa gear", script="runtime/run_pa.py gear",
         wraps="runtime/vendor/gear_fatigue_tool.py: compute_all augment_with_pct_and_risk",
         args="--out DIR", timeout="120秒", exits="0成功 2数据变化或门禁失败",
         io="读: gear_params.json 12个CSV 写: gear_result.json 两个CSV gear_damage_position.md gate_gear.json"),
    dict(id="T-04", name="run_pa compare", script="runtime/run_pa.py compare",
         wraps="无原函数 公式取自 comprehensive_hub.py 的 ArmVsGearTab.refresh",
         args="--out DIR --p 6.61", timeout="10秒", exits="0成功 2缺上游或p非法或门禁失败",
         io="读: arm_result.json gear_result.json 写: compare_result.json compare_table.csv compare_conclusion.md gate_compare.json"),
    dict(id="T-05", name="run_pa report", script="runtime/run_pa.py report",
         wraps="无原函数 仅汇总上游 json",
         args="--out DIR", timeout="10秒", exits="0成功 2缺上游或门禁失败",
         io="读: 三个 result json 写: 综合校核报告.md report_summary.json gate_report.json"),
    dict(id="T-06", name="run_pa all / selftest", script="runtime/run_pa.py all|selftest",
         wraps="依次调用 T-01 至 T-05 / 合成数据自检",
         args="all 接受以上全部参数 selftest 无参数", timeout="all 约5分钟内 selftest 约1分钟",
         exits="0成功 1自检失败 2阶段失败", io="selftest 只写系统临时目录并在结束时删除"),
]


def render_tool(t):
    return "\n".join(["# %s %s" % (t["id"], t["name"]), "", "- 脚本: `%s`" % t["script"], "- 封装对象: %s" % t["wraps"],
                      "- 命令格式: `%s %s`" % (CMD.split()[0] + " " + t["script"].split()[0], t["args"]),
                      "- 参数: %s" % t["args"], "- 超时约定: %s" % t["timeout"], "- 退出码: %s" % t["exits"],
                      "- 输入输出: %s" % t["io"], "- credential_ref: 无(本工具不使用任何凭据 不联网)"])


def render_tools_readme():
    L = ["# 工具索引", "", "全部为薄封装: 只调用 runtime/vendor 内的原工具函数 不重写业务逻辑。", "",
         "| 编号 | 名称 | 封装对象 | 退出码 |", "|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |" % (t["id"], t["name"], t["wraps"], t["exits"]) for t in TOOLS]
    L += ["", "环境: Python 3.10 以上 numpy 2.0 以上 matplotlib tkinter(无需显示器)。",
          "", "未纳入主流程的原工具能力: DetailWindow 与 GridChartWindow 是桌面端交互图表 本包不调用 风险位置清单由 gear_damage_position.md 代替。"]
    return "\n".join(L)


KNOW = [
    ("orchestration.md", "编排契约",
     "本文件不涉及 joint_life_core 与 gear_fatigue_tool 的内部算法 相关内容见 runtime/vendor 下的原文件。",
     ["阶段顺序固定为 prepare arm gear compare report 其中 arm 与 gear 互相独立",
      "每个阶段的产物与门禁文件名固定 见 Refs/Tools/README.md",
      "所有阶段只通过 out 目录下的文件交换数据 不共享内存状态",
      "prepare 会清除全部下游产物 因此改动任何输入后必须从 prepare 重新开始"]),
    ("gate-rules.md", "门禁规则",
     "本文件只描述门禁判定口径 不涉及校核公式本身 公式见原工具函数。",
     ["文件存在且非空", "摆臂: Life 与 Teq 为正的有限数 T_total 等于 6 倍 Ts omega_max 与转速换算一致 峰值扭矩与扭矩范围一致",
      "齿轮: D_allow 等于 TR 的 M 次方乘 NR PASS 加 FAIL 等于关节数 判定与最严苛位置的 U 一致 关节数为12",
      "对比: D1 为正的有限数 行数等于关节数 按比值降序", "报告: 含总体判定章节 且所有 FAIL 关节均被列出",
      "所有门禁均为确定性规则 不调用模型 失败时给出文件路径或数值证据"]),
    ("troubleshooting.md", "排障手册",
     "本文件不涉及校核结论的工程解释 只处理运行失败。",
     ["提示缺少运行依赖: 安装 Python3 numpy 2.0 以上 matplotlib 并确认 tkinter 可导入 无需显示器",
      "提示缺少必需文件: 检查12个CSV命名是否为 腿_关节.csv 例如 FL_hip.csv 不区分大小写 下划线或空格会被忽略",
      "提示文件在 prepare 之后被修改: 重新执行 prepare",
      "提示摆臂结果发散: 检查转速 角位移 臂长 寿命指数是否在合理量级",
      "控制台中文乱码: 设置环境变量 PYTHONUTF8=1 输出文件本身是 UTF-8",
      "selftest 失败: 把完整输出交给工具维护人 不要修改 vendor 内文件"]),
]


def render_know(k):
    return "\n".join(["# " + k[1], "", "> 边界声明: " + k[2], ""] + ["- " + x for x in k[3]])
