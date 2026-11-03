# 编排契约

> 边界声明: 本文件不涉及 joint_life_core 与 gear_fatigue_tool 的内部算法 相关内容见 runtime/vendor 下的原文件。

- 阶段顺序固定为 prepare arm gear compare report 其中 arm 与 gear 互相独立
- 每个阶段的产物与门禁文件名固定 见 Refs/Tools/README.md
- 所有阶段只通过 out 目录下的文件交换数据 不共享内存状态
- prepare 会清除全部下游产物 因此改动任何输入后必须从 prepare 重新开始
