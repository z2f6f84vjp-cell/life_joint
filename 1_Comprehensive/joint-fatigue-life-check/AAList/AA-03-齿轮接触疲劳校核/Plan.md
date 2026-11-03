# AA-03 Plan

## 内部步骤
1. 读取 gear_params.json
2. 重新解析12个CSV 并核对每个文件sha256与 prepare 时一致 不一致则终止
3. 调用 compute_all 得到逐位置与逐关节结果
4. 导出位置级CSV与关节级汇总CSV
5. 对每个关节按损伤占比降序累计到80% 写出风险位置清单
6. 写 gear_result.json 并运行 gear 门禁
