# quant-research-cloud

面向 A 股的 Python 量化研究起点：将假设记录、时间顺序验证、含交易约束的回测和本地模拟账本接成可运行的离线流程，并提供 Codex Cloud 安装脚本。示例使用合成行情，用来检查工程流程；收益数字不代表真实市场表现。

源码和环境配置已上传至公开仓库 [zhai-yuan/quant-research-cloud](https://github.com/zhai-yuan/quant-research-cloud) 的 `main` 分支，已核实 [源码提交 d607d9d](https://github.com/zhai-yuan/quant-research-cloud/commit/d607d9d3741bb83edbdb206bdd3c92e92084a994)。Codex Cloud 环境尚未创建或发布；接下来的设置步骤见 [Cloud 配置](docs/CLOUD_SETUP.md)。

## 已配置的研究工具

主环境覆盖 A 股行情与财务数据、因子评价、统计与因果分析、机器学习、组合优化、回测、技术指标、衍生品、Notebook、报告和数据存储。另配置 11 个独立环境：贝叶斯研究、PyTorch/NLP/强化学习、TensorFlow、Qlib、RQAlpha、Nautilus、Zipline、VeighNa、Spark、高频订单簿研究、掘金仿真 SDK。默认安装主环境及全部扩展；许可证、模型权重、行情与券商终端按实际研究资源另配。

每个环境都有固定版本与哈希锁文件；Python/NumPy 的冲突通过独立环境解决。详细库名和用途见 [依赖清单](docs/DEPENDENCIES.md)，当前交付的实测范围见 [验证记录](docs/VALIDATION.md)。锁定成功、安装成功、真实数据/模拟账户连通、Cloud 发布分别记录，避免把一个结果解释为全部完成。

## 快速运行

在仓库根目录使用 Linux、WSL 或支持 Bash 的环境。Python 版本与各依赖组合见项目的依赖配置。

```bash
# 默认安装全部受支持的依赖组合，分别放进独立虚拟环境。
bash scripts/setup.sh

# 无数据账户、无联网行情要求的演示。
bash scripts/run.sh demo --output artifacts/demo

# 验证核心代码。
.venv/bin/python -m pytest

# 检查运行环境。
.venv/bin/python scripts/doctor.py
```

只验证核心演示与测试时，可将第一条命令改为 `bash scripts/setup.sh minimal`。它不会安装完整研究工具集。主环境是 `.venv`，扩展组合放在 `.venvs/<profile>`；在对应环境内运行该组合的 Python，避免把不同框架的依赖混在一起。

## 演示会生成什么

`artifacts/demo/` 下生成数据、假设、训练集参数选择、保留样本信号、回测结果与 SQLite 本地模拟账本。关键入口包括：

| 路径 | 内容 |
| --- | --- |
| `data/synthetic_prices.csv` | 固定随机种子的合成行情 |
| `hypothesis.yaml` | 演示假设与检验设置 |
| `research/parameter_selection.csv` | 训练区间参数比较 |
| `research/validation.json` | 时间切分与验证记录 |
| `backtest/metrics.json`、`backtest/equity.png` | 回测指标和资金曲线 |
| `backtest/orders.csv`、`backtest/trades.csv` | 订单与成交记录 |
| `paper/paper.sqlite` | 本地模拟交易状态与检查点 |
| `manifest.json` | 本次运行的产物清单 |

配置文件为 `configs/research.yaml`。演示的撮合模型包含 T+1、默认 100 股整数单位、停牌、给定涨跌停价格，以及可配置费用与滑点；股票池固定，日历采用工作日，未建模真实盘口队列、流动性容量和完整公司行动。A 股实证研究需要先替换这些简化，详见 [研究工作流](docs/ASHARE_WORKFLOW.md)。

## 使用自己的数据

本地模拟命令读取符合项目字段约定的 CSV，并将状态保存在指定 SQLite 文件中：

```bash
bash scripts/run.sh paper \
  --data artifacts/demo/data/synthetic_prices.csv \
  --database artifacts/paper/paper.sqlite \
  --config configs/research.yaml \
  --lookback 20 \
  --mode local-paper
```

该命令支持本地历史回放：相同输入可恢复且避免重复入账，追加行情或修改参数会创建新的隔离运行。CSV 字段与股票池要求见研究工作流。真实行情接入、商业数据权限、长期运行服务与券商交易网关需要另外配置。安装 TuShare、RQData 或交易框架的 Python 包不会赋予数据账户权限，也不会自动接通券商。

## 放入 Codex Cloud

依赖清单、源码和脚本已在 GitHub 仓库中。创建 Cloud 环境并让 Codex 执行 `bash scripts/setup.sh`，验证离线演示与测试，再发布环境。仓库文件描述如何安装，依赖实际安装在 Cloud 的运行环境中。[OpenAI 官方 Cloud 文档](https://learn.chatgpt.com/docs/environments/cloud-environments)

本项目交付研究与模拟流程的工程起点，未提供经过真实数据验证的完整生产策略。持续模拟需要维护独立的存储、调度和服务生命周期；Cloud 对话中的一次运行不能证明这些服务已部署。
