# A 股量化研究依赖与运行边界

默认 `bash scripts/setup.sh` 安装全部研究组合：主环境 `.venv` 与十一个独立扩展环境 `.venvs/<profile>`。`minimal` 只供离线演示与测试，不能视为完整研究安装。所有依赖意图列在 `requirements/*.in`，解析出的版本与下载哈希列在对应 `*.lock`；Python 版本列在 `requirements/profiles.json`。安装器遇到失败会停止并记录状态，不会把失败组合静默跳过。

范围以 A 股研究为中心，覆盖数据、财报、假设检验、因子、传统与深度学习、优化、回测、模拟账户接口、报告和工程服务。它是广泛且可维护的工具集合；商业数据许可证、券商终端、每个框架的全部实验模型、专有研究平台和 GPU 硬件并不是 Python 依赖能够一并提供的资源。

## 主环境：Python 3.11，NumPy 1.26，pandas 2.x

主环境通过明确版本范围保留传统金融工具兼容性。新增库时先重新解析并验证；不要直接将 NumPy 2 或 pandas 3 装入主环境来覆盖现有锁文件。下表解释直接依赖的用途，实际精确版本以 `main.lock` 为准。

| 研究阶段 | 主要依赖 | 用途 |
| --- | --- | --- |
| 表格、列式与大样本计算 | NumPy、pandas、SciPy、Polars、PyArrow、DuckDB、datasets、xarray、Dask/distributed | 清洗、多源合并、Parquet/Arrow、SQL 分析、并行计算 |
| 计算加速与持久文件 | Numba、Bottleneck、NumExpr、h5py、tables、Zarr | 数值循环、滚动统计、HDF5 与分块数组 |
| Excel 与财报导出 | openpyxl、xlrd、XlsxWriter | 导入和导出工作簿；首次可得时间与修订版本仍须由数据层保存 |
| A 股行情、基本面、股票池 | AKShare、BaoStock、TuShare、RQData/rqdatac | 行情、财务、指数、行业与成分查询；具体接口覆盖、历史口径和权限需核查 |
| 日历与因子分析 | exchange-calendars、pandas-market-calendars、chinese-calendar、alphalens-reloaded、empyrical-reloaded、ffn | 交易日、IC、分组收益、换手与收益风险统计；法定假期库不能替代交易所时段 |
| 海外与宏观数据 | yfinance、pandas-datareader、fredapi、nasdaq-data-link、sec-edgar-downloader | 跨市场对照、经济序列和公开申报文件 |
| 国际模拟与交易客户端 | CCXT、alpaca-py、ib_async | 研究跨市场或对接测试账户；安装不会连接账户、订阅行情或发单 |
| 统计与计量 | statsmodels、arch、linearmodels、Pingouin、lifelines | 回归、面板、波动率、统计检验与存续分析 |
| 时序结构与异常 | ruptures、STUMPY、tsfresh、NetworkX | 结构突变、相似片段、时序特征与关系网络 |
| 传统机器学习 | scikit-learn、imbalanced-learn、LightGBM、XGBoost、CatBoost、joblib | 回归、分类、截面排序、提升树与并行建模 |
| 调参、解释与因果 | Optuna、optuna-integration、SHAP、DoWhy、EconML | 实验搜索、模型解释和因果效应；因果识别仍依赖研究假设 |
| 组合与约束优化 | CVXPY、CVXOPT、Clarabel、OSQP、SCS、PyPortfolioOpt、Riskfolio-Lib | 权重、风险预算、线性/二次/锥规划与组合分析；未提供商业求解器许可证 |
| 通用回测与绩效 | vectorbt、Backtrader、backtesting.py、bt、QuantStats、pyfolio-reloaded | 参数研究、事件/向量回测、收益归因和报告；需显式增加 A 股市场约束 |
| 技术指标与衍生品 | TA-Lib、ta、QuantLib | 常见技术指标、利率/期权模型与定价 |
| 交互研究 | JupyterLab、Notebook、ipykernel、ipywidgets、nbconvert、nbformat、Papermill | 可复现 Notebook、批量参数执行和导出 |
| 图表与研究界面 | Matplotlib、Seaborn、Plotly、Altair、Bokeh、Panel、Streamlit、Dash | 研究图、交互看板和本地服务；安装不等于服务已部署 |
| PDF/HTML 报告 | ReportLab、pdfplumber、pypdf、Jinja2 | 财报提取、PDF 生成和模板报告 |
| 实验与调度 | MLflow、Prefect、APScheduler | 记录实验、参数、产物与任务；远程服务和持久数据库另行部署 |
| API、配置与日志 | FastAPI、Uvicorn、Pydantic、pydantic-settings、PyYAML、python-dotenv、Hydra、OmegaConf、Typer、Rich、Loguru、tqdm、Tenacity | 参数约束、服务端点、日志、重试与命令行 |
| 数据库与云对象存储客户端 | SQLAlchemy、Alembic、psycopg、PyMySQL、Redis、PyMongo、clickhouse-connect、boto3、s3fs、fsspec、azure-storage-blob、google-cloud-storage | SQL/NoSQL、迁移和 S3/Azure/GCS；数据库服务器、凭据和存储桶不是这些包的一部分 |
| 网络与文档解析 | Requests、HTTPX、aiohttp、websockets、BeautifulSoup、lxml、orjson | API、流式消息、HTML/XML 和 JSON |
| 浏览器自动化 | Playwright 与安装脚本配置的 Chromium | 公开公告页面、研究服务检查和浏览器报告；访问条件与数据使用权限仍由具体网站决定 |
| 质量与构建 | pytest、pytest-cov、pytest-asyncio、Ruff、mypy、pandas-stubs、pre-commit、build、pip-audit、setuptools、wheel | 测试、类型、格式、审计和可复现构建 |

详细接口从原厂文档开始：[AKShare](https://akshare.akfamily.xyz/)、[BaoStock](http://baostock.com/baostock/index.php/Python_API%E6%96%87%E6%A1%A3)、[TuShare](https://tushare.pro/document/2)、[RQData](https://www.ricequant.com/doc/rqdata/python/manual.html)。访问公共接口也应记录来源、请求时间、频率与数据使用条件；库安装不能保证每个上游接口持续可用。

## 默认安装的独立组合

这些组合按冲突边界分别安装，并非安装器静默省略的“可选项”。工具之间交换 Parquet/CSV、配置与实验产物；运行时选择各自解释器。所有组合都不自动下载大模型权重、商业行情或框架数据包。

| Profile | Python | 核心依赖与目标 | 分开安装的原因和外部条件 |
| --- | --- | --- | --- |
| `bayesian` | 3.11 | PyMC、ArviZ、NumPyro、CPU JAX、Dynesty、HMMlearn、Copulas、DEAP、SALib | 贝叶斯假设、层级模型、状态切换、尾部与敏感性研究；现代 NumPy/PyTensor/JAX 与传统金融栈分开 |
| `torch-ml` | 3.11 | CPU PyTorch、TorchVision、TorchAudio、Lightning、Transformers、Sentence Transformers、PEFT、spaCy/jieba、ONNX Runtime、Gymnasium、Stable-Baselines3、SB3-Contrib、PettingZoo、Ray、Darts、NeuralForecast、PyTorch Forecasting、GluonTS、sktime、StatsForecast、HierarchicalForecast、Prophet | 深度学习、公告文本、强化学习与预测栈很大；PyTorch 由安装器指定 CPU backend，模型权重和 spaCy 语言模型需另取。Prophet 自定义 Stan 模型另需编译工具 |
| `tensorflow` | 3.11 | TensorFlow 2.18、Keras 3、TensorFlow Probability 0.25、tf-keras 2.18、Optuna | TFP 0.25 按上游已验证组合约束在 TF 2.18，TFP 使用单独的 `tf_keras`，与 Keras 3 名称分开；不启用 `and-cuda` |
| `qlib` | 3.11 | Microsoft `pyqlib`、LightGBM/XGBoost/CatBoost、CPU Torch、Qlib RL、Alphalens 与 A 股数据客户端 | Qlib 的因子、模型、组合流程；legacy Gym/Tianshou 与主环境隔离，MLflow 约束 `<3.13`；官方数据入口有可用性限制，需准备获授权的本地数据 |
| `rqalpha` | 3.11 | RQAlpha、RQData、AKShare/BaoStock/TuShare、Alphalens、QuantStats | A 股事件回测引擎；行情 bundle 与商业接口权限另行配置 |
| `nautilus` | 3.12 | NautilusTrader 1.x、IB 接口与可视化 extras | 当前稳定发行需要 Python 3.12+；Linux wheel 需 glibc 2.35+。IB 连接需独立 Gateway/TWS 与账户；引擎安装不自动实现 A 股规则 |
| `zipline` | 3.11 | Zipline Reloaded、exchange-calendars、Alphalens、empyrical、pyfolio | 独立 bundle ingestion 与事件回测；A 股数据格式和 T+1/涨跌停/停牌撮合仍需适配 |
| `vnpy` | 3.11 | VeighNa 4.x/alpha、CTA 策略/回测、组合策略、算法交易、数据录制、SQLite、RQData/TuShare、paperaccount 与 Binance adapter | 框架依赖 NumPy 2.2+ 和 Qt；独立环境防止覆盖主环境。Cloud 未提供 GUI 桌面；paperaccount 是工具而非已连接的模拟账户 |
| `spark` | 3.11 | PySpark SQL/ML/MLlib/Connect、Delta Spark、Fugue | 需要 Java 17+；可本地运行，分布式集群、Delta Maven artifact 下载和对象存储权限另配 |
| `hft` | 3.11 | HftBacktest、NumPy 2、Numba、Polars、HoloViews、Databento 客户端 | 订单簿、排队与延迟模拟；Linux wheel 需 glibc 2.28+，逐笔/L2 数据和 Databento 许可另配 |
| `gm` | 3.10 | 掘金 `gm`、`gmtrade` 仿真 SDK、pandas 1.5、protobuf 3 | gmtrade 已发布的 Linux wheel 只到 CPython 3.10；gm 需要 pandas 1/protobuf 3，与主环境冲突。需要独立 Token、仿真账户与服务连接 |

例如在相应解释器中运行：

```bash
bash scripts/python.sh qlib -c 'import qlib; print(qlib.__version__)'
bash scripts/python.sh rqalpha -c 'import rqalpha; import importlib.metadata; print(importlib.metadata.version("rqalpha"))'
bash scripts/python.sh torch-ml -c 'import torch; print(torch.__version__, torch.cuda.is_available())'
bash scripts/python.sh gm -c 'import gm.api; import gmtrade.api; print("SDK imports OK")'
```

框架和兼容性依据：[Qlib 上游](https://github.com/microsoft/qlib)、[Qlib PyPI wheel](https://pypi.org/project/pyqlib/)、[RQAlpha](https://pypi.org/project/rqalpha/)、[NautilusTrader 稳定包元数据](https://pypi.org/project/nautilus-trader/)、[Zipline Reloaded](https://pypi.org/project/zipline-reloaded/)、[VeighNa 包元数据](https://pypi.org/project/vnpy/)、[HftBacktest](https://pypi.org/project/hftbacktest/)。Nautilus 上游 develop 文档可能描述 2.x，项目锁定的 1.x API 应使用对应发行版文档。

TensorFlow Probability 0.25 官方发布说明列明 TensorFlow 2.18 与 legacy tf-keras 兼容要求；TensorFlow 官方 pip 文档将不带 CUDA extras 的安装列为 CPU 用法。[TFP 0.25 发布说明](https://github.com/tensorflow/probability/releases/tag/v0.25.0)、[TensorFlow 安装说明](https://www.tensorflow.org/install/pip)。

## 原生依赖和外部服务

`scripts/system.sh` 为 Debian/Ubuntu 安装编译工具、BLAS/LAPACK/OpenMP、SSL/FFI/XML/HDF5、PostgreSQL client headers、ZeroMQ、Qt 常用运行库、Java 17、Graphviz、中文字体、ffmpeg 和 Pandoc。它不启动数据库、MLflow、Prefect 或券商服务。需要管理员权限，其他发行版应使用给定 Dockerfile 或匹配安装这些系统包。

TA-Lib 从 0.6.5 开始提供包含底层 C 库的 Linux x86_64/arm64 wheel；本项目目标平台优先使用 wheel。若改架构或版本而转为源码构建，需按上游说明另装对应 C 库。[TA-Lib wheel 说明](https://github.com/TA-Lib/ta-lib-python#wheels)。Spark 4 需要 Java 17+，Python 3.10+；Python 包安装通过不代表已启动 JVM 或计算集群。[Spark 官方要求](https://spark.apache.org/docs/latest/index.html)。

RQData Python SDK 常见连接使用 `rqdatad-pro.ricequant.com:16011`；仅开放 HTTPS 443 的策略不能证明此 TCP 服务可达。若采用供应商授权的 HTTP API，认证与接口不同，应单独实现和验证。[RQData Python 手册](https://www.ricequant.com/doc/rqdata/python/manual.html)、[RQData HTTP 文档](https://www.ricequant.com/doc/rqdata/http/data-process)。

掘金 `gm` 有 Linux x86_64 wheel；`gmtrade` 仿真 API 原厂示例连接 `api.myquant.cn:9000`，需要已申请的仿真账户与 Token。导入 SDK 不代表端口可达、登录成功或仿真发单通过。本仓库不会运行示例中的报单函数。[gm 发行文件](https://pypi.org/project/gm/)、[gmtrade 发行文件](https://pypi.org/project/gmtrade/)、[掘金官方仿真接口](https://sim.myquant.cn/sim/help/Python.html)。

迅投提供单独 Linux 版 xtquant，原厂限定为有相应权限的 `xtdata` 数据获取，不支持 `xttrade`。原厂发布渠道、授权和二进制包需要按其指引配置，不能将公开 PyPI 的同名包安装当作已完成 Linux 数据授权。Windows MiniQMT/QMT 交易终端应部署在独立 Windows 网关。CTP/XTP 等券商原生网关涉及供应商库与账户授权，未列入默认未经验证的网关部署。[迅投 Linux 原厂说明](https://dict.thinktrader.net/nativeApi/Linux%E7%89%88xtquant%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B%E6%8C%87%E5%8D%97.html)。

所有组合按 CPU 研究环境配置；安装不会创造 GPU、券商账户、交易所 L2 许可或无限 API 配额。NLP 权重、GPU driver/CUDA、真实行情、RQAlpha/Qlib bundles、数据库/对象存储和长期调度服务应作为后续明确资源准备并记录。

## 怎样判断完成到哪一步

锁文件存在表示依赖在指定 Python/Linux 目标上成功解析，不能代替下载、原生加载或实际 API 验证。`bash scripts/setup.sh` 成功、`uv pip check` 和 `scripts/doctor.py --profile <profile>` 通过后，才能说明对应组合已安装并通过本地包检查。检查只覆盖已声明分发包的版本及选定框架入口导入，不是所有函数或外部服务的集成测试。

`.environment-status.json` 记录此次安装结果；查看实际结果再判断哪些组合就绪。只有 minimal 或 main 验证通过时，不得称十一个扩展环境都已安装。真实 A 股研究还需要数据一致性、时间可得性、历史股票池、板块交易规则与模拟账户回报验证；这些按 [A 股工作流](ASHARE_WORKFLOW.md) 逐项实现。Codex Cloud 发布须按 [Cloud 配置](CLOUD_SETUP.md) 在界面中完成并验证。

贝叶斯框架依据：[PyMC](https://www.pymc.io/)、[NumPyro](https://num.pyro.ai/)、[JAX CPU 安装](https://docs.jax.dev/en/latest/installation.html)。
