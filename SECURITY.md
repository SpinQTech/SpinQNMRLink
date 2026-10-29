# Security reporting / 安全问题报告

Do not post credentials, session identifiers, private connection profiles or raw sensitive traffic in public issues. For a vulnerability, use the hosting repository's private security advisory mechanism when available, or contact its maintainers through a private channel. Include affected SDK versions, reproduction steps and sanitized logs.

请勿在公开问题中提供凭据、会话标识、真实连接配置或敏感通信报文。漏洞优先通过代码托管平台的私密安全报告机制反馈；平台未开启时，通过私密渠道联系维护者。提供受影响版本、复现步骤与脱敏日志。

## Version and disclosure information / 版本与披露信息

The SDK version is defined in `src/spinqnmrlink/_core/_version.py`; release notes
are in [CHANGELOG.md](CHANGELOG.md). This repository does not currently specify
a security maintenance window for individual releases or a fixed response time.
Include the exact SDK version or source revision in your report. Coordinate
publication of reproduction details with maintainers through the private report.
For non-security bugs and usage questions, see [SUPPORT.md](SUPPORT.md).

SDK 版本定义于 `src/spinqnmrlink/_core/_version.py`，版本记录见
[CHANGELOG.md](CHANGELOG.md)。本仓库目前未规定各版本的安全维护周期或固定响应时间。
报告中注明准确的 SDK 版本或源码版本，通过私密报告与维护者协调复现细节的公开时间。
普通缺陷与使用问题见 [SUPPORT.md](SUPPORT.md)。
