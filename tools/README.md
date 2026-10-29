# Developer tools / 开发工具

Run these tools from the repository root using the Python environment described
in [CONTRIBUTING.md](../CONTRIBUTING.md).

在项目根目录、按 [贡献指南](../CONTRIBUTING.md)配置的 Python 环境中运行。

| Tool / 工具 | Purpose / 用途 |
| --- | --- |
| `build_docs.py` | Build English and Chinese HTML documentation / 构建中英文 HTML 文档 |
| `check_docs.py` | Check experiment coverage, page correspondence and HTML links / 检查实验覆盖、页面对应关系和 HTML 链接 |
| `check_distribution.py` | Reject local profiles and unapproved example JSON, then check contents and isolated installation / 拒绝本地配置及未获准的示例 JSON，再检查发行包和独立安装 |
| `check_examples.py` | Validate all 35 example sources offline / 离线验证全部 35 个示例 |
| `generate_protocol.py` | Regenerate Protobuf code in the pinned tool environment / 在固定工具环境中重新生成 Protobuf 代码 |

```console
python tools/build_docs.py
python tools/check_docs.py
python -m build
python tools/check_distribution.py
python tools/check_examples.py
```

For Protobuf generation prerequisites, see
[development](../docs/en/development.rst) /
[开发说明](../docs/zh_CN/development.rst).

The build and check commands above do not submit hardware experiments. Protocol
tests may use a local loopback server. Hardware batch validation and historical
report processing are maintained separately from these public developer tools.

上述构建和检查命令不会提交实机实验；协议测试可能使用本机回环服务器。
实机批量验证和历史报告处理单独维护。

Only `examples/manifest.json` and `examples/connection_config.example.json` are
included as example JSON in source archives. Adding public example JSON requires
updating both `MANIFEST.in` and the distribution check's allowlist. Git ignore
rules alone do not control archive contents. Check the actual delivery artifacts.

源码包中的示例 JSON 仅包含 `examples/manifest.json` 与
`examples/connection_config.example.json`。新增公开示例 JSON 时，同步更新
`MANIFEST.in` 和发行包检查的允许名单。Git 忽略规则不决定打包内容；
必须检查实际准备交付的发行包。
