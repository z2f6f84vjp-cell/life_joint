# CA-01 输入门禁

- 检查对象: arm_params.json、gear_params.json、gear_files_report.md
- 语义: 阻断 任一项 FAIL 则流程停止 不进入下游
- 为何设在此处: 未通过的输入会污染两条并行计算
- 执行方式: 脚本内联 确定性规则 不调用模型
- 输出: gate_prepare.json
