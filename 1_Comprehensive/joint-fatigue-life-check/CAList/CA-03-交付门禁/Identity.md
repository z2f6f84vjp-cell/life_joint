# CA-03 交付门禁

- 检查对象: compare_result.json、综合校核报告.md
- 语义: 阻断 任一项 FAIL 则流程停止 不进入下游
- 为何设在此处: 报告交付给评审后再改成本最高
- 执行方式: 脚本内联 确定性规则 不调用模型
- 输出: gate_compare.json、gate_report.json
