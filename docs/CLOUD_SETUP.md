# GitHub 与 Codex Cloud 配置

本项目提供可检查的仓库内容与安装命令。远程 GitHub 仓库、已安装的 Python 环境和已发布的 Codex Cloud 环境是三个分别需要验证的结果。

## GitHub 访问与上传

目标公开仓库为 [zhai-yuan/quant-research-cloud](https://github.com/zhai-yuan/quant-research-cloud)，由用户创建。2026-10-02 已通过用户浏览器授权 GitHub CLI，再使用 Windows Git 推送至 `main`；已核实 [源码提交 d607d9d](https://github.com/zhai-yuan/quant-research-cloud/commit/d607d9d3741bb83edbdb206bdd3c92e92084a994) 的 64 个源码文件和 13 个锁文件。实际验证范围见 [验证记录](VALIDATION.md)。此前 GitHub App 的 Contents API 写入返回 403 `Resource not accessible by integration`；这次独立的 GitHub CLI 授权与上传成功不表示插件写入权限已修复。

已上传的交付目录作为仓库根目录，远程包含 `pyproject.toml`、`requirements/`、`scripts/`、`src/`、`tests/`、`configs/` 和 `docs/`。无需把 Token 发到聊天里或写入仓库。

`scripts/publish_github.sh` 保留为空仓库首次发布入口，依赖 Git/GitHub CLI 的认证条件，并拒绝覆盖已有远程提交。本次目标仓库已经完成首次上传，后续源码变更应正常提交并推送。

仓库保存依赖清单、锁定版本和安装脚本。当前仓库为公开仓库，上传前应确认提交范围只含源码；`.venv/`、`.venvs/`、原始商业行情、账户密钥及运行账本不应作为源码提交。之后在 Codex Cloud 仓库选择器中确认能够选中目标仓库。

## 本地准备与依赖隔离

从仓库根目录执行：

```bash
bash scripts/setup.sh
.venv/bin/python scripts/doctor.py
.venv/bin/python -m pytest
bash scripts/run.sh demo --output artifacts/demo
```

`setup.sh` 默认选择 `all`，安装项目所支持的研究工具组合。核心环境为 `.venv`，其他组合为 `.venvs/<profile>`；每个组合分别安装和检查，框架之间的包不会自动在另一环境中可用。只检查离线演示时使用 `bash scripts/setup.sh minimal`，完成它只能证明核心环境准备成功。

依赖意图存于 `requirements/*.in`，实际安装使用 `requirements/*.lock` 中的固定版本和哈希。更新依赖时先重新生成对应锁文件、执行安装和导入检查，再提交变更；不要直接删除锁文件来绕过冲突。安装结果记录在 `.environment-status.json`。检查失败时应依据该记录和命令退出状态排查，不能把完成部分组合解释成全部安装成功。

`scripts/maintenance.sh` 用于检查和更新已存在的环境；`scripts/start.sh` 做轻量运行检查。它们的存在不会启动长期交易进程。

## 创建和发布 Cloud 环境

当前官方入口为 **Settings > Codex Cloud > Environments > Create environment**。选择 GitHub 仓库，让 Codex 准备环境，在测试通过后选择 Publish。当前界面将安装命令记录为 Install script，将服务启动说明记录为 Start skill。[OpenAI 官方步骤](https://learn.chatgpt.com/docs/environments/cloud-environments#create-and-publish-an-environment)

把下面内容交给设置环境的 Codex：

```text
使用仓库指定的 Python 版本，在仓库根目录运行 bash scripts/setup.sh。
各研究组合保留在独立虚拟环境中。检查 .environment-status.json，
运行 .venv/bin/python scripts/doctor.py、.venv/bin/python -m pytest，
再运行 bash scripts/run.sh demo --output artifacts/cloud-smoke。
报告每个组合的安装、导入、测试结果及产物路径，处理失败后再发布。
```

Install script 对应命令：

```bash
bash scripts/setup.sh
```

Start skill 可使用以下说明：

```text
进入此仓库根目录，运行 bash scripts/start.sh 验证运行环境。
项目命令通过 bash scripts/run.sh 执行；核心 Python 是 .venv/bin/python。
离线演示不依赖数据账户。真实行情访问前，检查所需变量与网络服务，
仅报告变量是否存在，不打印密钥。长期模拟服务须单独部署与管理。
```

若只希望先测试离线流程，可把 Install script 改成 `bash scripts/setup.sh minimal`；这应标记为核心演示环境。之后完整安装、测试并重新发布，才成为完整研究环境。

上述文件与说明属于准备材料。发布成功应在 Cloud 界面实际出现确认，并能从该环境启动新的任务。

## 数据账户与网络

按 SDK 需要配置变量，例如 `TUSHARE_TOKEN`；它们不是 GitHub 登录凭据。商业数据的订阅、积分、许可证和 API 配额由用户自己的数据账户决定。安装库与导入成功只证明客户端可用。

当前 Cloud 的 Environment variables 将值直接交给程序；Network secrets 通过代理为指定 HTTPS 目标替换凭据占位符，要求 HTTPS 443。需要读取原始 Token 的 SDK 应使用合适的直接变量，理解该值会对任务程序可见。数据源实际协议、端口及认证方式必须测试。[官方变量与网络说明](https://learn.chatgpt.com/docs/environments/cloud-environments#configure-environment-variables-and-network-secrets)

为安装开启 Package managers 域名范围；真实行情另开所需服务的域名与协议。RQData 原厂文档的常见连接示例是 `rqdatad-pro.ricequant.com:16011` 的二进制数据服务，仅允许 HTTPS 域名并不能证明这种连接可用。若当前 Cloud 出站策略不能支持，使用已授权的 HTTPS 数据网关或在可连接的自有环境下载数据后研究。[RQData 原厂说明](https://www.ricequant.com/doc/rqdata/python/manual.html)

## 保存结果与持续模拟

Cloud 新任务使用已发布环境的准备状态。更改公共安装配置后须重新发布；已有任务仍保有自己的状态。把需要保留的研究结果导出到用户控制的持久存储或作为合适的版本化产物保存。[官方状态说明](https://learn.chatgpt.com/docs/environments/cloud-environments#reuse-and-update-saved-state)

本项目的 SQLite 账本用于离线模拟的检查点和恢复。长期按交易日运行时，应在自有服务上配置真实交易日历、调度、持久磁盘、单实例锁、数据补齐、失败重试、日志和状态备份。Cloud 任务中的成功运行与长期服务部署是不同的验证目标。

Windows MiniQMT 的交易客户端需要独立 Windows 网关，无法直接作为 Windows 程序在 Linux Cloud 运行。迅投另提供 Linux 版 xtquant，但原厂文档限定为有相应权限的 `xtdata` 数据获取，未支持 `xttrade` 交易。任何券商连接还需匹配账户授权与客户端环境。[迅投 Linux 版说明](https://dict.thinktrader.net/nativeApi/Linux%E7%89%88xtquant%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B%E6%8C%87%E5%8D%97.html)
