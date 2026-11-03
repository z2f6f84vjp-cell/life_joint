# Manifesto(规范和原则)

## 通用原则
- 只读复用原工具源码,不修改 `joint_life_core.py`、`gear_fatigue_tool.py`、`comprehensive_hub.py`。
- 所有数值以函数实际计算结果为准,不得估算、补造或四舍五入后回填。
- 参数校验失败立即中止并告知用户具体是哪一项,不静默使用默认值替代。
- 下游 AA 只读取上游 AA 落盘的文件,不重新计算上游结果。
- 无界面运行: 直接 import 核心函数,不启动 Tk 窗口。

## 环境约束
- Python 3,numpy>=2.0(`np.trapezoid`),matplotlib。
- `gear_fatigue_tool.py` 模块顶层 import tkinter,运行环境需安装 tkinter(无需显示器)。

---
