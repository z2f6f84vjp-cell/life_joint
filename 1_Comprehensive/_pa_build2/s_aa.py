# -*- coding: utf-8 -*-
from s_plan import AAS, CAS

# 每个 AA: 内部步骤 输入检查 输出检查 工具 运行模式
AA_DETAIL = {
    "AA-01": dict(
        mode="IC 内联 OC 内联",
        steps=["确认预设 默认 anker 可选 sanhua high", "解析 --arm 与 --gear 覆盖项 未知键直接报错",
               "校验摆臂参数 转速 总角位移 臂长 寿命指数 额定扭矩 参考转速 参考寿命必须大于0",
               "校验齿轮参数7项均为大于0的有限数", "按文件名归一化匹配12个CSV 缺失任一则终止并列出",
               "校验每个文件含 #TITLES 与 #DATA 且每行数据列数不少于扭矩级数", "计算每个文件sha256",
               "清除全部下游产物 写出三个落盘文件并运行 prepare 门禁"],
        ic=["已拿到齿轮数据文件夹路径", "已知道使用哪个预设 未指定则默认 anker"],
        oc=["arm_params.json 含13项且惯量模式合法", "gear_params.json 含7项参数 文件夹路径 12个文件的sha256",
            "gear_files_report.md 列出12行与未匹配文件", "gate_prepare.json 全部 PASS"],
        tools=["T-01"]),
    "AA-02": dict(
        mode="IC 内联 OC 内联",
        steps=["读取 arm_params.json 缺失则终止", "调用 calculate_life 完成双S曲线规划与疲劳积分",
               "检查 Life 与 Teq 为有限数 否则报发散并终止", "派生循环次数 峰值扭矩 并写 arm_result.json",
               "生成文字摘要与3乘3图表", "运行 arm 门禁"],
        ic=["arm_params.json 存在且来自本轮 prepare"],
        oc=["arm_result.json 含 Life_h Teq_Nm T_total_s peak_torque_Nm cycles", "arm_summary.md 与 arm_figures.png 非空", "gate_arm.json 全部 PASS"],
        tools=["T-02"]),
    "AA-03": dict(
        mode="IC 内联 OC 独立上下文(逐关节交叉核对产物较长)",
        steps=["读取 gear_params.json", "重新解析12个CSV 并核对每个文件sha256与 prepare 时一致 不一致则终止",
               "调用 compute_all 得到逐位置与逐关节结果", "导出位置级CSV与关节级汇总CSV",
               "对每个关节按损伤占比降序累计到80% 写出风险位置清单", "写 gear_result.json 并运行 gear 门禁"],
        ic=["gear_params.json 存在", "12个CSV仍在原路径且sha256未变"],
        oc=["gear_result.json 含12个关节与 D_allow", "两个CSV可用表格软件打开", "gear_damage_position.md 每个关节一节", "gate_gear.json 全部 PASS"],
        tools=["T-03"]),
    "AA-04": dict(
        mode="IC 内联 OC 内联",
        steps=["确认 CA-02 对摆臂与齿轮的门禁均通过", "校验对比用寿命指数 p 大于0 默认 6.61",
               "计算 D1 等于 峰值扭矩的p次方 乘 循环次数 乘 0.5", "对每个关节计算 D2 等于 等效扭矩的p次方 乘 3000小时啮合次数",
               "比值 D2 除以 D1 大于1 判齿轮主导", "按比值降序写出三个文件并运行 compare 门禁"],
        ic=["arm_result.json 与 gear_result.json 均存在", "p 是正数"],
        oc=["compare_table.csv 行数等于关节数", "compare_conclusion.md 含比值含义边界说明", "gate_compare.json 全部 PASS"],
        tools=["T-04"]),
    "AA-05": dict(
        mode="IC 内联 OC 内联",
        steps=["读取三个 result json", "写总体判定 与关键数值", "列出 FAIL 关节 近预算关节 齿轮主导关节",
               "按 SF 升序写各关节明细", "写建议与交付文件清单", "运行 report 门禁"],
        ic=["三个 result json 均存在"],
        oc=["综合校核报告.md 含总体判定 风险项 各关节明细 建议 交付文件五节", "所有 FAIL 关节出现在报告中", "gate_report.json 全部 PASS"],
        tools=["T-05"]),
    "AA-06": dict(
        mode="人工节点 无脚本",
        steps=["向校核工程师回显预设 被覆盖的参数 12个文件清单与sha256前缀 未匹配文件",
               "取得明确确认后才放行到 AA-02 与 AA-03", "门禁失败时逐条展示 FAIL 项与证据",
               "由工程师决定修正输入重跑 或终止", "记录当前回路轮次 超过3轮必须终止"],
        ic=["已有 gate 记录或 prepare 产物"], oc=["确认结论或修正意见已记录", "回路轮次已记录"], tools=[]),
    "AA-07": dict(
        mode="人工节点 无脚本",
        steps=["向校核工程师展示综合校核报告首屏结论", "说明比值大于1不等于失败", "收集评审结论 接受 调整参数重算 补充数据",
               "选择重算则回到 AA-01 并记录轮次"],
        ic=["综合校核报告.md 已通过 CA-03"], oc=["评审结论已记录"], tools=[]),
}


def aa_files(aid):
    a = next(x for x in AAS if x[0] == aid)
    d = AA_DETAIL[aid]
    ident = "\n".join(["# %s %s" % (aid, a[1]), "", "- 职责: " + a[4], "- 所属阶段: " + a[2], "- 参与角色: " + a[3],
                       "- 运行模式: " + d["mode"], "- 输入: " + "、".join(a[5]), "- 输出: " + "、".join(a[6])])
    plan = "\n".join(["# %s Plan" % aid, "", "## 内部步骤"] + ["%d. %s" % (i + 1, s) for i, s in enumerate(d["steps"])])
    ic = "\n".join(["# %s 输入检查清单" % aid, ""] + ["- [ ] " + x for x in d["ic"]])
    oc = "\n".join(["# %s 输出检查清单" % aid, ""] + ["- [ ] " + x for x in d["oc"]])
    tool = "\n".join(["# %s Tools" % aid, ""] + (["- 引用 Refs/Tools/%s.md" % t for t in d["tools"]] or ["- 人工节点 不调用脚本"]))
    return {"Identity.md": ident, "Plan.md": plan, "AAInputCheckList.md": ic, "AAOutputCheckList.md": oc, "Tools/tool.md": tool}


def ca_files(cid):
    c = next(x for x in CAS if x[0] == cid)
    stages = c[7]
    ident = "\n".join(["# %s %s" % (cid, c[1]), "", "- 检查对象: " + "、".join(c[5]), "- 语义: 阻断 任一项 FAIL 则流程停止 不进入下游",
                       "- 为何设在此处: " + {"CA-01": "未通过的输入会污染两条并行计算", "CA-02": "错误的计算结果会被对比与报告当作真值",
                                          "CA-03": "报告交付给评审后再改成本最高"}[cid],
                       "- 执行方式: 脚本内联 确定性规则 不调用模型", "- 输出: " + "、".join(c[6])])
    chk = ["- [ ] 对应阶段 %s 的门禁记录存在且全部 PASS" % "、".join(stages),
           "- [ ] FAIL 项已向 AA-06 展示并附证据",
           "- [ ] 凭据零泄露扫描: 运行 python runtime/scan_credentials.py . 结果为未发现"]
    return {"Identity.md": ident, "Checklist.md": "\n".join(["# %s 检查清单" % cid, ""] + chk)}
