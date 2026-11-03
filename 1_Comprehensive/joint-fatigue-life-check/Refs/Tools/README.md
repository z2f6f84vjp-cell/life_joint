# 工具索引

全部为薄封装: 只调用 runtime/vendor 内的原工具函数 不重写业务逻辑。

| 编号 | 名称 | 封装对象 | 退出码 |
|---|---|---|---|
| T-01 | run_pa prepare | runtime/vendor/gear_fatigue_tool.py: load_folder | 0成功 2校验失败或门禁失败 |
| T-02 | run_pa arm | runtime/vendor/joint_life_core.py: calculate_life build_summary create_figures | 0成功 2结果发散或门禁失败 |
| T-03 | run_pa gear | runtime/vendor/gear_fatigue_tool.py: compute_all augment_with_pct_and_risk | 0成功 2数据变化或门禁失败 |
| T-04 | run_pa compare | 无原函数 公式取自 comprehensive_hub.py 的 ArmVsGearTab.refresh | 0成功 2缺上游或p非法或门禁失败 |
| T-05 | run_pa report | 无原函数 仅汇总上游 json | 0成功 2缺上游或门禁失败 |
| T-06 | run_pa all / selftest | 依次调用 T-01 至 T-05 / 合成数据自检 | 0成功 1自检失败 2阶段失败 |

环境: Python 3.10 以上 numpy 2.0 以上 matplotlib tkinter(无需显示器)。

未纳入主流程的原工具能力: DetailWindow 与 GridChartWindow 是桌面端交互图表 本包不调用 风险位置清单由 gear_damage_position.md 代替。
