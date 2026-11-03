# AA-02 Plan

## 内部步骤
1. 读取 arm_params.json 缺失则终止
2. 调用 calculate_life 完成双S曲线规划与疲劳积分
3. 检查 Life 与 Teq 为有限数 否则报发散并终止
4. 派生循环次数 峰值扭矩 并写 arm_result.json
5. 生成文字摘要与3乘3图表
6. 运行 arm 门禁
