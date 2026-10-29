# Contributing / 贡献指南

## Report an issue or propose a change / 报告问题或提出变更

Read [SUPPORT.md](SUPPORT.md), search the repository's existing issues, and use
the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for defects.
Describe the problem and expected behavior with a minimal public API example.
For a substantial API or protocol change, describe the proposed scope in an
issue before implementation. Report vulnerabilities privately following
[SECURITY.md](SECURITY.md).

先阅读 [SUPPORT.md](SUPPORT.md)，搜索仓库已有问题。缺陷报告使用
[问题模板](.github/ISSUE_TEMPLATE/bug_report.md)，提供最小公开 API 示例及预期行为。
较大的 API 或协议变更先通过问题说明范围。漏洞按 [SECURITY.md](SECURITY.md) 私密报告。

## Development setup and conventions / 开发环境与约定

Use Python 3.8-compatible syntax. Follow the [source installation guide](docs/en/installation.rst) to create a Conda environment, then run `python -m pip install -e ".[dev,docs]"` from the repository root. Keep device wire protocols and parameter units stable. New code belongs in the public API, shared core or private device adapter according to its responsibility. Public API examples must not import private adapters.

新增代码使用兼容 Python 3.8 的语法。按[源码安装说明](docs/zh_CN/installation.rst)创建 Conda 环境，在项目根目录运行 `python -m pip install -e ".[dev,docs]"`。保持设备通信协议及参数单位兼容，按职责划分公开 API、共享核心、内部设备适配器。公开示例不得导入内部适配器。

## Local validation / 本地验证

Run these commands from the repository root with your development environment activated:

在项目根目录、已激活的开发环境中运行：

```console
python -m pytest
python -m ruff check .
python -m mypy
python tools/build_docs.py
python tools/check_docs.py
python -m build
python tools/check_distribution.py
python tools/check_examples.py
```

Before a PR, complete the checks above. Add meaningful regression tests for lifecycle, parameter and protocol changes. Update both languages together, including runnable examples. Generated Protobuf code is regenerated using `tools/generate_protocol.py` in its pinned tool environment; see [development](docs/en/development.rst) for the generation commands. HTML in `docs/_build/` is generated and ignored by Git; edit the sources in `docs/en/` and `docs/zh_CN/`.

提交 PR 前完成以上检查。生命周期、参数或协议变更须补充回归测试。两种语言同时更新，并引用可运行示例。Protobuf 由固定工具环境运行 `tools/generate_protocol.py` 再生成，命令见[开发说明](docs/zh_CN/development.rst)。`docs/_build/` 为 Git 忽略的生成 HTML，修改 `docs/en/` 和 `docs/zh_CN/` 下的源文件。

Record real-device results separately from offline fixture checks in `validation_status.json`. Include firmware and non-sensitive configuration; never commit credentials or real connection profiles. A configured CI job or a completed task is not, by itself, passed scientific validation.

Default mypy checks six public source modules against Python 3.8. The existing
NumPy/Pydantic import-skip policy also applies to their stubs, whose syntax can
target newer Python versions. This does not type-check those dependencies or
private adapters; runtime and protocol tests remain required. Source archives
include only the public example JSON manifest and template. Check newly built
artifacts with `tools/check_distribution.py`; `.gitignore` does not govern packaging.

真实设备测量与离线基线检查分别记录在 `validation_status.json`。注明固件及非敏感配置，不提交凭据或真实连接配置。配置了 CI 或任务已完成，本身不代表科学验证通过。

默认 mypy 按 Python 3.8 目标检查六个公开源码模块；NumPy/Pydantic 已有的导入
跳过规则也应用于可能使用新版 Python 语法的类型声明。这不表示这些依赖或内部
适配器已通过类型检查，仍需运行功能与协议测试。源码包中的示例 JSON 只包含
公开清单与配置模板。新构建的发行包须运行 `tools/check_distribution.py`；
`.gitignore` 不决定打包排除规则。
Keep SDK code and examples portable across Windows, Linux and macOS. Use pathlib, the active Python interpreter and Python resource management; avoid fixed interpreter paths or OS-specific launch commands. Core checks run without GUI extras. CI includes Windows/Linux/macOS Intel on Python 3.8/3.10/3.12 and macOS ARM64 on Python 3.10/3.12; publish only verification supported by recorded evidence.

SDK 和示例需支持 Windows、Linux、macOS，使用 pathlib、当前环境的 Python 解释器及 Python 资源管理，避免固定解释器路径和平台专属启动命令。核心检查不安装 GUI extras。CI 覆盖 Windows/Linux/macOS Intel 的 Python 3.8/3.10/3.12，以及 macOS ARM64 的 Python 3.10/3.12；平台通过状态以实际验证记录为准。

## Pull requests / 提交 PR

Create a focused branch from the repository's default branch and submit the PR
to that branch. Keep commits descriptive and scoped to the change; no mandatory
branch-name or commit-message format is currently specified. Use the
[PR template](.github/pull_request_template.md): explain the trigger, resulting
behavior, validation and any configuration or API migration. Mark hardware
checks pending when you have not performed them. Respond to review feedback
with updated code and validation evidence.

从仓库默认分支创建范围明确的工作分支，PR 提交到该默认分支。
提交说明应清楚描述变更，本仓库目前未规定强制分支名或提交消息格式。
按 [PR 模板](.github/pull_request_template.md)说明触发问题、最终行为、验证与
配置/API 迁移。未执行的硬件检查标记为待验证，按评审意见更新代码与验证证据。
