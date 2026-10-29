# Support / 使用支持

## Before reporting / 报告前检查

Read the [troubleshooting guide](docs/en/troubleshooting.rst),
[device support](docs/en/devices.rst) and [validation evidence](docs/en/validation.rst).
Confirm the active Python environment and reproduce the issue with the smallest
public API example possible. Offline checks do not require device credentials.

先阅读[故障排查](docs/zh_CN/troubleshooting.rst)、[设备支持](docs/zh_CN/devices.rst)
和[验证证据](docs/zh_CN/validation.rst)。确认当前 Python 环境，使用尽可能小的
公开 API 示例复现。离线检查无需设备凭据。

## SDK issues / SDK 问题

Use the issue tracker of the repository from which you obtained the source.
Search existing reports first, then use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).
Include SDK/Python versions, OS/architecture, expected and observed behavior,
minimal code and sanitized logs. For device runs, include the experiment key,
device type, firmware and whether the failure occurs during connection,
submission or result retrieval. Remove credentials, session identifiers and
private connection profiles. Report suspected vulnerabilities through
[SECURITY.md](SECURITY.md).

在获取源码的仓库中先搜索已有问题，再按[缺陷报告模板](.github/ISSUE_TEMPLATE/bug_report.md)
提交。提供 SDK/Python 版本、操作系统与架构、预期与实际行为、最小代码和脱敏日志。
设备实验另附实验键、设备类型、固件及出错阶段（连接、提交或结果读取）。
移除凭据、会话标识和真实连接配置。疑似漏洞按 [SECURITY.md](SECURITY.md) 私密报告。

## Support scope / 支持范围

The issue tracker is for SDK defects and documentation feedback. Device service
access, firmware setup, sample preparation and calibration require the equipment's
support provider. No support response time or commercial support terms are
specified in this repository.

仓库问题跟踪器用于 SDK 缺陷与文档反馈。设备服务访问、固件部署、样品准备和校准
需联系设备支持方。本仓库未规定支持响应时限或商业支持条款。
