# CA-02 计算结果门禁

- 检查对象: arm_result.json、gear_result.json
- 语义: 阻断 任一项 FAIL 则流程停止 不进入下游
- 为何设在此处: 错误的计算结果会被对比与报告当作真值
- 执行方式: 脚本内联 确定性规则 不调用模型
- 输出: gate_arm.json、gate_gear.json
