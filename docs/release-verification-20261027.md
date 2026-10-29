# Release verification / 发布验证 — 2026-10-28

This unpublished 1.0.0 candidate is checked locally on Windows x86_64 with
Python 3.12.15. Exact dependency versions and evidence scope are recorded in
[validation_status.json](../validation_status.json).

本次未发布的 1.0.0 候选版本在 Windows x86_64、Python 3.12.15 上本地验证。
依赖版本和证据范围见上方机器可读记录。

| Check / 检查 | Result / 结果 |
| --- | --- |
| `python -m pytest` | 784 passed; zero failures/errors/skips / 784 项通过，无失败、错误或跳过 |
| `python -m ruff check .` | Passed / 通过 |
| `python -m mypy` | Default configuration, 6 public modules / 默认配置，六个公开模块通过 |
| `python tools/check_examples.py` | 35 example sources / 35 个示例源码离线验证 |
| `python tools/build_docs.py` | Strict bilingual build / 双语严格构建 |
| `python tools/check_docs.py` | 35 mappings and 132 HTML pages/links / 35 个映射、132 页及链接 |
| `python -m build` | Source archive and universal wheel / 源码发行包与通用 wheel |
| `python tools/check_distribution.py` | Contents and isolated offline wheel install / 内容检查及独立离线安装 |

The build backend is pinned in `pyproject.toml`. When the declared build tools
are already installed, `python -m build --no-isolation` can verify the package
offline. Mypy keeps the Python 3.8 compatibility target and six-module public
scope; the existing NumPy/Pydantic import-skip rules also apply to their stubs.
Offline tests use fixtures and localhost and do not execute device experiments.

构建后端由 `pyproject.toml` 固定。已有声明的构建工具时，可使用无隔离构建进行
离线验证。类型检查保持 Python 3.8 目标及六个公开模块的范围，NumPy/Pydantic
的既有跳过规则同样用于类型声明。离线用例使用测试数据及本机回环，不执行设备实验。

## Physical start notifications / 物理层开始通知

Physical tasks accept both `task_started_post` and `custom_task_started_post`
for the active task ID. Only the first matching start is retained, including
start-before-ACK and mixed duplicate aliases. The matching start populates
execution-start and phase-duration metadata and switches from queue timeout
to execution timeout. Circuit-only message-family correlation remains strict.
Local timeouts do not cancel or replay tasks.

Nine additional cases extend coverage for both aliases, wrong IDs, start-before-ACK,
mixed duplicates, public timing metadata and timeout phase. The bug was reproduced
before the fix; the targeted ten-case set and full 784-case suite pass afterward.

物理层对当前任务同时识别通用和专用开始通知；开始先于 ACK 或两个别名重复到达时，
仅保留首次有效时间。有效开始通知填充执行开始、排队和执行时长，并切换至执行超时。
不同任务或不匹配的电路报文仍不会改变状态。本地超时不会取消或重放远端任务。
新增九项用例，目标十项回归及完整 784 项均通过。

## Live client evidence / 实际客户端证据

Earlier client tests passed both circuit modes: true returned probabilities and
8x8 density components; false returned probabilities with empty matrix arrays.
The SDK preserves empty arrays as absent matrix data. Density output requires
Triangulum client 2.0 or newer; actual matrix storage order remains unspecified.

A physical acquisition on 2026-10-28 completed successfully and returned FID
real/imaginary curves with 16000 points each and FFT real/imaginary curves with
16384 points each. That acquisition predates this start-notification fix.
**The notification fix is verified offline; this revision was not rerun against
a live client.** Scientific measurement validation remains separate.

此前两种电路模式均已通过实际客户端测试：true 返回概率与 8×8 密度矩阵，false
返回概率与空矩阵数组，SDK 兼容为空矩阵缺失。密度矩阵要求客户端 2.0 及以上，
矩阵存储顺序仍保持未知。
10 月 28 日已有物理采集成功，FID 两分量各 16000 点、FFT 两分量各 16384 点；
该次采集早于本次开始通知修复。**本次修复已通过离线验证，当前修订未重新连接客户端验证。**
接口证据不代表校准或科学测量精度验证。

## Platform and package scope / 平台及包内容范围

The user confirmed a tester completed Linux/macOS installation and testing.
Exact Python versions, architectures and per-matrix logs were not supplied;
this is recorded as tester-reported platform validation without asserting every
CI matrix entry passed. Current automated local checks cover Windows/Python 3.12.15.

Public artifacts include SDK sources, examples, synthetic protocol fixtures,
tests, bilingual manuals and build tools. Example JSON is restricted to the
public manifest and configuration template. Git history, real connection
profiles, raw device captures, internal reports and build caches are excluded.

Linux/macOS 的安装与测试已由用户确认测试同事完成；未提供具体 Python 版本、
架构及逐项日志，按测试同事反馈记录，不扩大声称所有 CI 矩阵项均已通过。
本地自动化验证环境为 Windows/Python 3.12.15。公开包只包含源码、示例、测试、
合成协议基线、双语文档及工具；排除 Git 历史、本地配置、原始报文、内部报告及缓存。
