# 交付验证记录

检查日期：2026-10-02。此记录描述本地准备、验证与已核实的 GitHub 源码上传；Codex Cloud 环境尚未创建或发布。

| 项目 | 结果 |
| --- | --- |
| 主环境安装 | Python 3.11.17；464 个锁定第三方分发包已安装，138 个直接依赖版本及选定框架入口检查通过 |
| 核心演示与测试 | minimal 与 main 环境分别通过 29 项测试；默认合成数据演示通过；回测与 SQLite 模拟账本核对一致 |
| 代码与脚本 | Ruff 检查通过；Bash 语法检查通过 |
| 启动检查 | 完整 main 通过；未完成安装和缺失扩展安装被拒绝 |
| 扩展环境 | 11 个环境均解析成功并生成版本/哈希锁文件；未全部执行物理安装、导入或模型验证 |
| 原生系统包 | 未在本机执行需要管理员权限的整套 apt 安装；安装脚本与 Dockerfile 已提供。验证使用了用户目录内的 OpenMP 运行库 |
| Chromium | Python 客户端已安装；本地没有安装浏览器或执行启动验证。默认完整安装会安装依赖并检查浏览器启动 |
| Docker | Dockerfile 已检查并修复浏览器原生依赖路径；本机 Docker/WSL 集成不可用，未执行镜像构建 |
| 真实数据/券商 | 未连接实际数据账户、L2 订阅或券商模拟账户；未发送任何外部订单 |
| GitHub | 经用户浏览器授权 GitHub CLI，Windows Git 成功推送至公开仓库 [zhai-yuan/quant-research-cloud](https://github.com/zhai-yuan/quant-research-cloud) 的 `main`；已核实 [源码提交 d607d9d](https://github.com/zhai-yuan/quant-research-cloud/commit/d607d9d3741bb83edbdb206bdd3c92e92084a994) 的 64 个源码文件、13 个锁文件及必需文件 |
| GitHub CI | 源码提交的自动离线工作流 [已通过](https://github.com/zhai-yuan/quant-research-cloud/actions/runs/37005745928)；完整环境的手动安装工作流尚未执行 |
| Codex Cloud | 未创建或发布实际 Cloud 环境；仓库安装说明与测试入口已准备 |

本地主要验证命令：

```bash
bash scripts/setup.sh minimal
INSTALL_SYSTEM_PACKAGES=0 INSTALL_BROWSER=0 bash scripts/setup.sh main
.venv/bin/python -m ruff check src tests scripts examples
bash scripts/start.sh
```

前两个安装模式先后在同一核心虚拟环境中检查，当前本地安装状态是 main。完整云端安装应使用默认 `bash scripts/setup.sh`，它会安装主环境及全部扩展、系统依赖和浏览器；任一组件失败时停止，完成状态不会标为成功。

新环境仍需验证真实数据可得性、网络协议与授权、交易日历、板块/证券规则以及模拟账户回报。示例的合成工作日数据、固定股票池、100 股单位和开盘撮合属于已声明简化。持续实时模拟服务尚未部署。

各锁文件的校验和、Python 目标和包数量见 [机器可读记录](validation.json)。Cloud 创建与发布步骤见 [配置说明](CLOUD_SETUP.md)。
