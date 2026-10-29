# SpinQNMRLink

[English](README.md) | [中文](README.zh_CN.md)

面向 **Lab**、**Triangulum** 的统一 Python SDK。一个 SDK 可管理其中一类或两类设备，分别维护连接、任务和失败状态，提供 35 个实验条目、类型化参数和执行等待时限。

适用于通过统一的配置、参数验证和结果 API 编写两类设备的 Python 实验流程。真实设备执行需要可访问的设备服务、凭据和样品校准；实验目录浏览与参数验证可离线进行。

## 安装

```console
conda create --name spinqnmrlink python=3.10 pip
conda activate spinqnmrlink
python -m pip install -e .
```

推荐使用 Conda 虚拟环境自行安装源码。先安装 Conda，进入包含 `pyproject.toml` 的项目根目录，再执行以上命令。IDE 使用该环境的解释器。最低 Python 版本为 3.8，测试目标为 3.8、3.10、3.12。Windows、Linux 和 macOS 使用同一安装流程，无需平台专属启动脚本。详细步骤见[安装说明](docs/zh_CN/installation.rst)。Lab 使用 TCP 或二进制 WebSocket，Triangulum 由 Python 直接实现 JSON 文本 WebSocket。SDK 不包含设备 DLL/SO，生成平台无关 wheel。具体平台可用性取决于 Python 依赖与实际安装检查。实际检查记录见 [验证证据](validation_status.json)。

## 快速上手

先验证安装，无需设备或凭据：

```console
python -c "from spinqnmrlink import list_experiments; print(len(list_experiments()))"
```

应输出 35。真实设备运行前，按[配置步骤](docs/zh_CN/configuration.rst)从模板创建 `connection_config.local.json` 并填写服务地址。Lab 保留非空的预留账号、密码字段；Triangulum 使用客户端“用户中心”创建的账号、密码。可以直接填写字面值，`env:VARIABLE` 环境变量引用为可选方式。本地配置应保密。脉冲、频率和样品参数应使用实际设备的校准结果。

```python
from spinqnmrlink import SpinQNMRLink, parameters_for

with SpinQNMRLink.from_config("connection_config.local.json") as sdk:
    lab = sdk.device("lab")
    parameters = parameters_for("lab.two.rabi")
    parameters.pulses[0].width_us = 40  # Replace with the calibrated pulse duration (us).
    experiment = lab.create_experiment("lab.two.rabi", parameters=parameters)
    lab.open()
    result = experiment.run(timeout=300, queue_timeout=600)
    print(result.status, result.data)
```

构造对象、验证参数、浏览目录不会连接设备。网络连接和接收线程仅在 `open()` 启动。SDK 退出时清理两个会话。本地等待超时不会终止远端实验；拒绝、失败、终止和提交结果未知分别报错。

`timeout` 从首次开始执行通知起限制执行等待时间；`queue_timeout` 从接受任务后起限制排队等待时间。省略 `queue_timeout` 时不限制排队时长，连接监测仍有效。提交确认使用独立的 `request_timeout`。实验若提供 `sample_frequency_hz`，必须从 `10000`、`20000`、`50000`、`100000`（Hz）中选择一个整数。参数约束和结果计时见[参数说明](docs/zh_CN/parameters.rst)，断连通知见[故障排查](docs/zh_CN/troubleshooting.rst)。

**三角座密度矩阵功能需要三角座客户端 2.0 及以上版本。** 使用 `calc_matrix=True` / `calcMatrix: true` 前请确认客户端版本，详见[线路实验说明](docs/zh_CN/triangulum/circuit.rst)。

## 示例与文档

[examples](examples/README.zh_CN.md) 为全部 35 个实验提供可直接使用的 Python 源码，并提供 Rabi、T1/T2 的扫描分析。基础源码展示明确参数、执行和测量读取。调用 `run_experiment()` 执行设备实验，离线检查、保存和评估使用独立进阶源码。Lab 两比特示例与文档按四章组织。示例无需 GUI，绘图和拟合可安装 `.[plot]`，Qt 工具另安装 `.[qt]`。

阅读[中文开发文档](docs/zh_CN/index.rst)或 [English manual](docs/en/index.rst)。在本地构建支持对应页面语言切换的双语 HTML 文档：

```console
python -m pip install -e ".[dev,docs]"
python tools/build_docs.py
python tools/check_docs.py
```

构建后打开 `docs/_build/html/zh_CN/index.html` 或 `docs/_build/html/en/index.html`。

## 项目结构

- `src/spinqnmrlink/`：SDK 实现与设备适配器。
- `examples/`：全部 35 个实验的可运行示例。
- `docs/`：中英文文档源文件。
- `tests/`：SDK 离线回归测试和协议基线。
- `tools/`：文档、发行包、示例检查及协议生成工具，见 [tools/README.md](tools/README.md)。

## 贡献与支持

开发环境、检查与 PR 流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，架构与扩展方法见[开发说明](docs/zh_CN/development.rst)。使用问题与缺陷报告见 [SUPPORT.md](SUPPORT.md)；疑似漏洞按 [SECURITY.md](SECURITY.md) 私密报告。版本记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

Python 源码遵循 [GPL-3.0-only](LICENSE.txt)。
