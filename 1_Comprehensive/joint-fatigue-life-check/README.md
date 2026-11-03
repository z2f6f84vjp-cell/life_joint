# 关节疲劳寿命综合校核 PA 包

## 快速开始
环境: Python 3.10 以上 numpy 2.0 以上 matplotlib tkinter(无需显示器)。

```
python runtime/run_pa.py selftest
python runtime/run_pa.py all --gear-folder <12个CSV所在目录> --out out
```

分阶段执行: prepare 然后 arm 与 gear 然后 compare 然后 report 每个阶段结束自动运行质量门禁 失败时退出码为 2。
覆盖参数: `--arm v_max_rpm=150 --gear M=6.61`。预设: anker sanhua high。
中文输出乱码时先设置 PYTHONUTF8=1。

## 目录
- charter.md Plan.md Manifesto.md Identity.md source.md: PA 设计文件
- AAList CAList Refs: 节点详细设计 数据对象 工具规格 知识
- runtime: 可运行脚本 其中 vendor 为原工具原样拷贝
- release: 发布物料(登记物料 验收报告 流程图)
