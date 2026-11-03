# AA-03 齿轮接触疲劳校核

- 职责: 对12个关节逐位置计算单边啮合损伤并与额定预算对比 取各关节最严苛位置判定PASS或FAIL
- 所属阶段: S-02
- 参与角色: R-01
- 运行模式: IC 内联 OC 独立上下文(逐关节交叉核对产物较长)
- 输入: gear_params.json、12个齿轮CSV
- 输出: gear_result.json、gear_per_position.csv、gear_per_position_summary.csv、gear_damage_position.md
