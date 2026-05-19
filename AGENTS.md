# AGENTS.md

本文件记录对当前项目的通读结果，供后续维护者或代码代理快速接手。内容以当前仓库结构和源码为准。

## 项目定位

这是一个围绕“缠中说禅教你炒股票 108 课”的资料整理与缠论技术分析实现项目。

项目包含两部分内容：

- 原始资料整理：`108/` 保存 108 课及相关评论、配图；根目录 `README.md` 介绍资料来源；`mergeMarkdownFiles.js` 可把 `108/` 下的 Markdown 合并成总文档。
- Python 分析系统：`chan_theory/` 实现缠论分析流水线，支持 K 线包含处理、分型、笔、线段、中枢、背驰、买卖点、多级别分析、可视化和策略建议。

核心使用场景是对 A 股 OHLCV 数据做缠论结构化分析，并生成报告和图表。

## 技术栈与依赖

- 主要语言：Python 3.10+。
- 辅助脚本：Node.js，主要用于合并 Markdown 资料。
- Python 依赖见 `requirements.txt`：
  - `matplotlib>=3.5.0`：绘图和图表输出。
  - `tushare>=1.2.89`：Tushare A 股数据源。
  - `pandas>=1.3.0`：数据处理，Ashare/Tushare 转换会用到。
- `Ashare/` 是随仓库放置的数据获取工具，封装新浪/腾讯行情接口，不需要 token，但需要网络。

当前仓库没有发现标准测试目录、`pyproject.toml`、`setup.py` 或 CI 配置；运行通常从仓库根目录直接执行脚本。

## 重要目录与文件

| 路径 | 作用 |
| --- | --- |
| `chan_theory/` | 缠论分析核心 Python 包。 |
| `Ashare/` | 第三方/内置行情数据工具，核心文件是 `Ashare.py` 和 `MyTT.py`。 |
| `docs/` | 项目文档、教程、复盘说明和教程图片。 |
| `docs/images/` | 教程图表资源，由 `generate_tutorial_charts.py` 生成。 |
| `108/` | 缠论 108 课 Markdown 原文、评论和配图。 |
| `demo.py` | 综合 demo，支持合成数据、Tushare、CSV。 |
| `demo_ashare.py` | 推荐的免费真实行情 demo，使用 Ashare 获取 A 股数据。 |
| `demo_300014.py` | 亿纬锂能 `300014.SZ` 的专项 demo，Tushare 失败时回退到合成数据。 |
| `generate_tutorial_charts.py` | 生成 `docs/images/` 中的教程图表。 |
| `mergeMarkdownFiles.js` | 合并 `108/` 下 Markdown，输出 `108/108-All.md` 和 `108/108-artileOnly.md`。 |
| `tushare_token.txt` | 本地 Tushare token 文件；涉及敏感信息，改动和展示时要谨慎。 |

## 核心包结构

`chan_theory/` 是项目最重要的部分，主要模块如下：

| 模块 | 职责 |
| --- | --- |
| `data_types.py` | 定义核心枚举和数据结构：`RawKLine`、`KLine`、`Fractal`、`Bi`、`Segment`、`Hub`、`Signal`、`TrendMonitor`、`Gap` 等。 |
| `kline_processor.py` | K 线包含关系处理，按趋势上下文合并相邻包含 K 线。 |
| `fractal.py` | 顶/底分型识别，强弱分型判断，并强制分型顶底交替。 |
| `bi.py` | 根据相邻分型构造笔，要求分型间至少有足够 K 线间隔。 |
| `segment.py` | 根据笔构造线段，包含第一/第二种终结情况的近似实现。 |
| `hub.py` | 从笔或线段识别中枢，处理延伸、扩展、移动，并判断趋势/盘整。 |
| `divergence.py` | EMA、MACD、MACD 面积和背驰相关计算。 |
| `signals.py` | 识别三类买点/卖点：B1/B2/B3、S1/S2/S3。 |
| `indicators.py` | 辅助指标：SMA、BOLL、均线吻、缺口检测与分类。 |
| `strategies.py` | 走势完成监控、中枢震荡交易、同级别机械操作、三段走势阶段判断。 |
| `multi_level.py` | 多级别联立、区间套、级别共振、跨级别状态汇总。 |
| `data_source.py` | Tushare 与 Ashare 数据源封装，并提供 CSV/DataFrame 转 `RawKLine`。 |
| `visualize.py` | 绘制 K 线、分型、笔、线段、中枢、买卖点、BOLL、MACD 和策略信号。 |
| `chan.py` | `ChanAnalyzer` 主分析器，串联完整分析流水线。 |
| `__init__.py` | 对外导出核心类型、`ChanAnalyzer` 和 `MultiLevelAnalyzer`。 |

## 主分析流程

主入口是 `chan_theory.chan.ChanAnalyzer`。典型调用方式：

```python
from chan_theory import ChanAnalyzer

analyzer = ChanAnalyzer()
analyzer.load(raw_klines)
analyzer.analyze()
summary = analyzer.summary()
```

`analyze()` 的流水线大致为：

1. `process_inclusion()`：处理 K 线包含关系。
2. `detect_fractals()`：识别顶/底分型。
3. `analyze_fractal_strength()`：判断强、弱、普通分型。
4. `construct_bis()`：由分型构造笔。
5. `construct_segments()`：由笔构造线段。
6. `detect_hubs_from_bis()` / `detect_hubs_from_segments()`：识别笔级别和线段级别中枢。
7. `detect_hub_migration()`：识别中枢移动。
8. `compute_macd()`：计算 MACD。
9. `compute_bollinger_bands()`、`classify_ma_kisses()`、`detect_gaps()`：计算辅助指标。
10. `detect_signals()`：识别 B1/B2/B3 和 S1/S2/S3。
11. `classify_trend()`：基于中枢判断上涨、下跌、盘整或未知。
12. `monitor_trend_completion()`：监控走势完成状态。
13. `mechanical_trading_signals()`、`hub_oscillation_signals()`：生成策略信号。
14. `three_phase_analysis()`：估计底部构造、中间连接、顶部构造等阶段。

## 数据源与输入格式

所有数据源最终都应转换为 `RawKLine`：

```python
RawKLine(
    index=i,
    dt="20240101",
    open=10.0,
    close=10.5,
    high=10.8,
    low=9.9,
    volume=1000000,
)
```

可用数据源：

- `TushareDataSource`：支持日线、周线、月线、分钟线、多级别数据、股票搜索；需要 Tushare token，可从参数传入，也可使用环境变量 `TUSHARE_TOKEN`。
- `AshareDataSource`：使用仓库内 `Ashare/Ashare.py`，支持日线、周线、月线和分钟线；常用代码格式包括 `sz300014`、`sh600519`、`300014.SZ`、`600519.SH`。
- `TushareDataSource.from_csv()`：从 CSV 离线导入。
- `TushareDataSource.from_dataframe()`：从 pandas DataFrame 导入。

注意：真实行情数据依赖外部网络，受接口可用性和权限影响；离线调试可优先使用 `demo.py` 的合成数据或 CSV。

## 常用运行命令

从仓库根目录运行：

```bash
pip install -r requirements.txt
python demo.py
python demo.py --csv your_data.csv
python demo.py --token YOUR_TOKEN --code 000001.SZ --start 20240101 --end 20251231
python demo_ashare.py
python demo_ashare.py --code sh600519 --count 300
python demo_ashare.py --code 000001.SZ --count 400
python generate_tutorial_charts.py
node mergeMarkdownFiles.js
```

运行 demo 后常见输出文件：

- `chan_analysis_demo.png`
- `chan_analysis_<股票代码>.png`
- `chan_analysis_csv.png`
- `docs/images/*.png`
- `108/108-All.md`
- `108/108-artileOnly.md`

## 可视化约定

- `visualize.py` 使用 `matplotlib.use("Agg")`，适合无图形界面的环境直接保存 PNG。
- A 股颜色约定已经按中文市场习惯处理：红色表示上涨阳线，绿色表示下跌阴线。
- demo 脚本会尝试配置中文字体；如果环境缺少 CJK 字体，图中中文可能显示异常。

## 文档现状

- `docs/DOCUMENTATION.md` 是偏 API/架构的英文说明。
- `docs/TUTORIAL.md` 是较完整的英文教程，包含缠论概念、流水线、运行 demo、课程到代码映射。
- `docs/notes.md` 是中文概念和定理摘录。
- `docs/LESSON_REVIEW_SUMMARY.md` 是一次实现复盘记录；其中有历史问题、修复状态和剩余建议。阅读时要以当前源码为最终依据，因为复盘文档里部分状态描述可能带有历史上下文。

## 已知近似与维护注意事项

这些点在源码和文档中已经有所说明，后续改动时尤其要注意：

- `segment.py` 的线段构造是实用近似：它用笔到笔的比较模拟特征序列法，没有完整实现特征序列元素的标准化和包含处理。
- `multi_level.py` 的 `interval_nesting()` 当前按信号日期接近度匹配下级别信号，不是真正验证高低级别区间包含。
- `strategies.py` 的 `three_phase_analysis()` 主要根据中枢数量和最后一笔方向推断阶段，不是完整的第 108 课级别构造。
- `signals.py` 的第一类买卖点需要趋势前提；当前代码已经区分 B1 需要下跌趋势、S1 需要上涨趋势。
- `hub.py` 的趋势判断使用第 20 课外边界规则：上涨要求后一个中枢 `DD >` 前一个中枢 `GG`，下跌要求后一个中枢 `GG <` 前一个中枢 `DD`。
- `classify_post_divergence()` 判断背驰后走势时，核心阈值是中枢核心区间 `[ZD, ZG]`，不是外边界 `[DD, GG]`。
- 策略信号和分析结果是技术分析辅助，不应在文档或 UI 中表达成投资保证。
- `Ashare/` 下有独立 `.git` 目录，像是外部项目拷贝；除非修数据源问题，不建议随意重构。
- 不要在输出、提交信息或文档中暴露 `tushare_token.txt` 的实际内容；优先建议使用环境变量传 token。

## 开发建议

- 处理核心算法时，优先从 `data_types.py`、`chan.py` 和相关模块 docstring 入手，保持对象字段和流水线顺序一致。
- 新增功能时尽量让输入仍归一到 `RawKLine`，不要让数据源格式直接渗透进分析模块。
- 如果调整中枢、趋势、买卖点逻辑，需要同步检查 `docs/TUTORIAL.md`、`docs/DOCUMENTATION.md`、`generate_tutorial_charts.py` 和 demo 输出文案。
- 修改可视化时要保留 A 股红涨绿跌约定。
- 目前没有自动化测试；如果改动核心算法，建议补最小单元测试或至少用合成数据、CSV、Ashare demo 各跑一次。
- 生成的 PNG、合并后的 `108/108-*.md`、PDF 等多为产物，提交前应确认是否确实需要纳入版本管理。

