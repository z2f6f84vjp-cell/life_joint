# -*- coding: utf-8 -*-
# 数据对象: 先定终态 再倒推过程与输入
DOS = [
    dict(id="DO-07", name="综合校核报告", kind="终态",
         concept="把摆臂寿命 齿轮校核 跨模块对比三类结果合成一份结论先行的评审报告",
         use="供校核工程师评审 决定接受 调整参数或补充数据",
         bound="只汇总上游已落盘的数值 不重新计算 不给出超出数据支持的结论",
         form="Markdown 文件 综合校核报告.md 与 report_summary.json",
         role="AA-05 产出 AA-07 评审时消费", producer="AA-05", consumer="AA-07 校核工程师",
         enough="含总体判定 风险项 各关节明细 建议 交付文件清单五个章节",
         good="每个数字能追溯到上游 json 文件 FAIL 关节全部列出 结论先于细节",
         derive="由 DO-04 DO-05 DO-06 汇总得到"),
    dict(id="DO-06", name="跨模块对比结果", kind="过程",
         concept="以统一寿命指数p比较摆臂基准损伤D1与各关节齿轮损伤D2",
         use="判断各关节的损伤主要来自齿轮接触疲劳还是摆臂模型基准",
         bound="D1是整体基准不区分关节 比值大于1不等于校核失败",
         form="compare_result.json compare_table.csv compare_conclusion.md",
         role="AA-04 产出 AA-05 消费", producer="AA-04", consumer="AA-05",
         enough="D1为正的有限数 每个关节一行 按比值降序",
         good="p与D1 D2中使用的完全一致 结论文字说明了比值的含义边界",
         derive="由 DO-04 的峰值扭矩与循环次数 加 DO-05 各关节最严苛位置推出"),
    dict(id="DO-05", name="齿轮校核结果", kind="过程",
         concept="12个关节逐位置的单边啮合损伤与额定预算对比结果",
         use="给出每个关节PASS或FAIL 安全系数 支持寿命 以及80%损伤风险位置",
         bound="按位置独立判定 取各关节最严苛位置 不跨位置累加",
         form="gear_result.json gear_per_position.csv gear_per_position_summary.csv gear_damage_position.md",
         role="AA-03 产出 AA-04 AA-05 消费", producer="AA-03", consumer="AA-04 AA-05",
         enough="覆盖12个关节 D_allow等于TR的M次方乘NR 每个关节判定与最严苛位置的U一致",
         good="逐位置明细可复算 风险位置清单可直接指导排查",
         derive="由 DO-02 的12个CSV 与 DO-03 的7项参数计算得到"),
    dict(id="DO-04", name="摆臂寿命结果", kind="过程",
         concept="双S曲线运动规划下的摆臂测试寿命 等效扭矩 疲劳积分",
         use="给出摆臂测试寿命小时数 峰值扭矩与循环次数 供对比与评审",
         bound="仅在输入参数描述的单一工况下成立 不外推到其他运动规划",
         form="arm_result.json arm_summary.md arm_figures.png",
         role="AA-02 产出 AA-04 AA-05 消费", producer="AA-02", consumer="AA-04 AA-05",
         enough="Life与Teq为正的有限数 T_total等于6倍Ts",
         good="数值与原桌面工具同参数下一致 图表齐全",
         derive="由 DO-01 摆臂参数集计算得到"),
    dict(id="DO-03", name="齿轮校核参数", kind="输入",
         concept="齿轮接触疲劳校核的7项参数 TR NR LH M TEETH SIDE TW",
         use="决定额定预算D_allow与时间折算系数K",
         bound="只含7项数值参数 不含扭矩数据",
         form="gear_params.json 中的 params 字段",
         role="AA-01 校验后落盘", producer="校核工程师 AA-01", consumer="AA-03",
         enough="7项均为大于0的有限数",
         good="取自工程师确认过的额定值或默认值 且在报告中回显",
         derive="输入"),
    dict(id="DO-02", name="齿轮数据集", kind="输入",
         concept="4条腿乘3个关节共12个CSV 记录各位置各扭矩级的圈数",
         use="提供逐位置逐扭矩级的啮合圈数 供损伤计算",
         bound="文件名须匹配 腿_关节.csv 内容须含 #TITLES 与 #DATA 标记",
         form="12个CSV文件 加 gear_files_report.md 与各文件sha256",
         role="校核工程师提供 AA-01 校验", producer="校核工程师", consumer="AA-01 AA-03",
         enough="12个文件全部匹配 每行数据列数不少于扭矩级数",
         good="文件sha256在AA-01与AA-03之间保持不变",
         derive="输入"),
    dict(id="DO-01", name="摆臂参数集", kind="输入",
         concept="摆臂寿命计算的13项参数 含运动学 质量惯量 疲劳寿命三组",
         use="驱动双S曲线规划与扭矩疲劳积分",
         bound="只含摆臂模型参数 不含齿轮数据",
         form="arm_params.json",
         role="AA-01 解析预设与覆盖项后落盘", producer="校核工程师 AA-01", consumer="AA-02",
         enough="转速 总角位移 臂长 寿命指数 额定扭矩 参考转速 参考寿命均大于0 惯量模式合法",
         good="预设来源与被覆盖的项在报告中可见",
         derive="输入"),
    dict(id="DO-08", name="质量门禁记录", kind="过程",
         concept="每个阶段确定性门禁的逐项PASS或FAIL与证据",
         use="让AA-06和评审人看到哪里失败 以及失败时的数值证据",
         bound="只记录规则判定结果 不做主观评价",
         form="gate_prepare.json gate_arm.json gate_gear.json gate_compare.json gate_report.json",
         role="CA-01 CA-02 CA-03 产出 AA-06 消费", producer="CA-01 CA-02 CA-03", consumer="AA-06",
         enough="每个阶段都有一份记录且含全部检查项",
         good="FAIL项带文件路径或数值证据 可直接定位",
         derive="由各阶段产物与确定性规则得到"),
]

ELEMENTS = [("业务概念", "concept"), ("核心用途", "use"), ("边界", "bound"), ("数据形态", "form"),
            ("流程角色", "role"), ("产出方", "producer"), ("消费方", "consumer"),
            ("够了的标准", "enough"), ("好的标准", "good"), ("推导关系", "derive")]


def render_dos():
    L = ["# 数据对象定义", "", "推导方向: 终态 DO-07 向前推出过程 DO-06 DO-05 DO-04 DO-08 再推出输入 DO-01 DO-02 DO-03。",
         "编号按推导顺序连续 DO-01 至 DO-08 执行主键见 Identity.md。", ""]
    for d in sorted(DOS, key=lambda x: x["id"]):
        L += ["## %s %s(%s)" % (d["id"], d["name"], d["kind"]), "", "| 要素 | 内容 |", "|---|---|"]
        L += ["| %s | %s |" % (zh, d[k]) for zh, k in ELEMENTS]
        L.append("")
    return "\n".join(L)


MANIFESTO = [
    ("价值取向", [
        ("结论先行", "报告第一屏必须是总体判定", "评审人打开报告先看到 PASS 或 FAIL 数量", "把细节堆在前面会让FAIL关节被忽略"),
        ("复用不重写", "校核数值必须来自原工具函数", "任何阶段需要计算时直接调用 vendor 内的原函数", "自行重写公式会使结果与桌面工具不一致 失去已验证属性"),
        ("损伤来源要说清", "跨模块对比只回答损伤来源 不替代校核判定", "比值大于1出现在报告中时", "把比值当成失败会误导工程师处置"),
    ]),
    ("质量底线", [
        ("门禁不通过不往下走", "每个阶段结束必须跑确定性门禁", "任一阶段门禁FAIL时脚本以退出码2终止", "带病的中间结果会被下游当作真值"),
        ("上游被改必须作废下游", "prepare 重新执行必须清除全部下游产物", "工程师改了参数或CSV后重跑", "旧的 arm_result 与新参数并存会生成自相矛盾的报告"),
        ("数据在流程中不得悄悄变化", "AA-03 必须核对12个CSV的sha256与AA-01一致", "prepare 之后又有人替换了某个CSV", "校核基于与确认时不同的数据 结论不可信"),
        ("门禁用规则不用模型", "所有门禁判定都是确定性公式与阈值", "评审门禁时", "让模型打分验证模型产物会互相放行幻觉"),
    ]),
    ("协作契约", [
        ("人工确认在计算之前", "参数与文件清单必须经校核工程师确认再进入AA-02与AA-03", "AA-01完成后", "参数错了才发现会浪费整轮计算并产生错误结论"),
        ("回路最多三轮", "任一回路超过3轮必须终止并升级给人", "反复修正仍门禁失败时", "无退出条件的重试会无限消耗时间并掩盖根因"),
        ("失败要给证据", "报告门禁失败必须同时给出文件路径或数值", "AA-06 向工程师展示失败项时", "只说失败不给证据工程师无法定位"),
    ]),
    ("安全红线", [
        ("包内零凭据", "包内任何文件不得出现 token 密码 密钥的实值", "新增配置或脚本时", "发布即泄密且无法撤回"),
        ("数据不出本机", "运行脚本不得联网 不得上传CSV或结果", "任何阶段", "扭矩与寿命数据属于研发数据 外传会造成泄露"),
        ("只读原工具", "vendor 目录内的原工具文件不得修改", "需要改行为时在 runtime 封装层处理", "改动原文件会使sha256对不上并丢失验证属性"),
    ]),
]


def render_manifesto():
    L = ["# Manifesto(规范和原则)", "", "每条原则包含 规则 触发场景 违反后果。", ""]
    n = 0
    for dim, items in MANIFESTO:
        L += ["## " + dim, ""]
        for title, rule, scene, cons in items:
            n += 1
            L += ["### M-%02d %s" % (n, title), "- 规则: " + rule, "- 触发场景: " + scene, "- 违反后果: " + cons, ""]
    return "\n".join(L)
