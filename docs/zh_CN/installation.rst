从源码安装
==========

SDK 面向 Windows、Linux 和 macOS，两类设备均使用 Python 网络协议。核心功能无需设备 DLL/SO、编译器或 GUI。最低 Python 版本为 3.8，测试目标为 3.8、3.10 和 3.12。自行拉取源码时，推荐使用 Python 3.10 的 Conda 虚拟环境。

创建环境
--------

按 `Conda 官方安装指南 <https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html>`_ 安装 Conda。在已初始化 Conda 的终端运行命令，例如 Windows 的 Anaconda Prompt，或 Linux/macOS 已初始化的 shell：

.. code-block:: console

   conda create --name spinqnmrlink python=3.10 pip
   conda activate spinqnmrlink

若无法激活，参考 `Conda 环境管理指南 <https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html>`_ 完成 shell 初始化。环境名称可自定，命令不依赖仓库内固定的解释器路径。

安装源码
--------

克隆或下载源码后，进入包含 ``pyproject.toml`` 的项目根目录，在已激活的环境中安装：

.. code-block:: console

   python -m pip install -e .
   python -c "from spinqnmrlink import list_experiments; print(len(list_experiments()))"

导入检查应输出 35，不连接设备。可编辑安装使 SDK 源码修改直接生效，无需重新安装；若只需要普通安装，使用 ``python -m pip install .``。

依赖由 ``pyproject.toml`` 定义，通过 Conda 环境中的 pip 安装；本项目不作为 Conda 包分发。IDE 选择该环境的 Python 解释器，并将项目根目录设为工作目录。无需自动创建环境或启动设备的脚本。直接调用 Python 示例的方法见 :doc:`quickstart`。

可选功能与开发
--------------

.. code-block:: console

   python -m pip install -e ".[dev,docs]"

开发安装包含测试、代码检查与文档工具。绘图和拟合使用 ``python -m pip install -e ".[plot]"``；Qt 工具使用 ``python -m pip install -e ".[qt]"``，其可用性取决于操作系统、架构和 Python 版本对应的 GUI 依赖。核心通信、实验目录和离线检查无需这两组依赖。为 extras 加引号可避免部分 shell 将方括号解释为通配符。

每次打开新终端都需激活环境。额外 Conda 包应先于 pip 包安装，项目依赖约束统一维护在 ``pyproject.toml``。Python 3.8 对已停止支持该解释器的依赖设置上限。平台检查与设备联调分别记录于 :doc:`devices` 和 :doc:`validation`。
