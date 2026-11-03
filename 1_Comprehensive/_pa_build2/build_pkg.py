# -*- coding: utf-8 -*-
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s_plan as P
import s_do as D
import s_aa as A
import s_refs as R

ROOT = r"D:\7_tool\1_Comprehensive\joint-fatigue-life-check"
N = {"n": 0}


def w(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip("\n") + "\n")
    N["n"] += 1


CHARTER = """# 立项书: 关节疲劳寿命综合校核

## 目标
把「综合工具集」的三个标签页(摆臂寿命 / 齿轮接触疲劳 / 跨模块对比)做成可重复执行的 PA:
用户给出摆臂参数与12个齿轮CSV后 一次跑完三项校核 并得到带结论的评审报告。

## 角色
- R-01 校核执行引擎(AI虚拟): 调用原工具函数 运行门禁
- R-02 校核工程师(人工): 提供数据 确认参数 处置门禁失败 评审结果

## 范围
- 包含: 摆臂寿命计算 齿轮接触疲劳逐位置校核 跨模块伪损伤对比 报告生成
- 不包含: 桌面端交互图表(DetailWindow GridChartWindow) 实测数据采集 校核标准本身的合理性判断

## AA 数量说明
共7个AA 其中AA-06与AA-07是人工节点 脚本类AA为5个 与三个标签页加参数准备加报告相对应 在3到8的区间内。

## 适配性判定
判定为 PA 信心度 黄色: 有人工确认与评审节点 有独立质量门禁 但不需要跨会话持久化
所有状态都落在 out 目录的文件里 因此可以在新会话里从任一阶段继续。

## 成功标准
- 同参数同数据下 摆臂 Life 与 Teq 和原桌面工具一致 齿轮 12 个关节的 U 与独立公式一致(selftest 回归覆盖)
- 缺文件 非法参数 上游缺失 都在计算前被拦截并指明原因
- 报告中每个数字都能追溯到上游 json
"""

IDENTITY = """# Identity: 关节疲劳寿命综合校核

## 核心能力
- 按双S曲线运动规划计算摆臂测试寿命 等效扭矩 疲劳积分
- 对12个关节逐位置计算单边啮合损伤 与额定预算对比 取各关节最严苛位置判定 PASS 或 FAIL
- 用统一寿命指数对比摆臂基准损伤与各关节齿轮损伤 判断损伤来源
- 每个阶段结束运行确定性质量门禁

## 能力边界
- 只在输入参数与数据描述的工况内成立 不外推
- 不判断校核标准或额定参数是否合理
- 不采集数据 不联网 不上传
- 比值大于1只说明损伤来源 不等于失败 失败只以齿轮校核的 PASS 或 FAIL 为准

## 执行主键
- 一轮校核由 out 目录标识 目录内 gear_params.json 的 files 字段记录12个CSV的 sha256
- 同一 out 目录内重新执行 prepare 视为新的一轮 旧下游产物全部作废
"""

SOURCE = """# 一手信息源

| 来源 | 内容 | sha256 |
|---|---|---|
| runtime/vendor/joint_life_core.py | 摆臂寿命核心算法 | a9a33e431f632230805eee8a9e04079635c755f0fec8dc4ed58b78743363ce10 |
| runtime/vendor/gear_fatigue_tool.py | 齿轮接触疲劳校核核心函数 | 81784b0dba927a51ec025790b3b379ea738188d62df25c26b606e78a96236e82 |
| comprehensive_hub.py(第三标签页) | 跨模块对比公式口径 | cbf952ec832797c5122eba48f156f954c72e5c61c32c784a24afd32a7b9a93ae |

vendor 内两个文件与原路径逐字节一致 原路径分别为 joint_life_core.py 与 geer_cycle 目录下的 gear_fatigue_tool.py。
"""

INSIGHT = """# InsightCollection

## cd-data
- 12个关节CSV是整条流程唯一的外部大数据输入 其完整性与不变性决定结论可信度 因此引入 sha256 核对。
- 摆臂参数与齿轮参数的寿命指数不同(10/3 与 6.61) 跨模块比较必须使用同一指数 因此单设 AA-04。

## cd-flow
- 摆臂计算与齿轮校核互相独立 可并行 对比与报告依赖二者。
- 人工确认放在计算之前 评审放在报告之后。

## pd-tool
- 全部工具为对原函数的薄封装 见 Refs/Tools。

## pd-know
- 编排契约 门禁规则 排障手册 三份 见 Refs/Knowledge。

## pd-aa
- 5个脚本AA加2个人工AA 回路均限3轮。
"""

EXAMPLE = """{
  "_说明": "本包不需要任何凭据 也不联网 此文件仅作为可选默认值模板",
  "preset": "anker",
  "gear_folder": "D:/path/to/gear_csv_folder",
  "compare_p": 6.61
}
"""

README = """# 关节疲劳寿命综合校核 PA 包

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
"""


def main():
    w("charter.md", CHARTER)
    w("Identity.md", IDENTITY)
    w("source.md", SOURCE)
    w("Plan.md", P.render_plan())
    w("Manifesto.md", D.render_manifesto())
    w("README.md", README)
    w("config.json.example", EXAMPLE)
    for a in P.AAS:
        d = "AAList/%s-%s" % (a[0], a[1])
        for name, text in A.aa_files(a[0]).items():
            w("%s/%s" % (d, name), text)
    for c in P.CAS:
        d = "CAList/%s-%s" % (c[0], c[1])
        for name, text in A.ca_files(c[0]).items():
            w("%s/%s" % (d, name), text)
    w("Refs/DataObjects/DataObjects.md", D.render_dos())
    w("Refs/Insight/InsightCollection.md", INSIGHT)
    for k in R.KNOW:
        w("Refs/Knowledge/" + k[0], R.render_know(k))
    for t in R.TOOLS:
        w("Refs/Tools/%s.md" % t["id"], R.render_tool(t))
    w("Refs/Tools/README.md", R.render_tools_readme())
    print("written", N["n"], "files")


main()
