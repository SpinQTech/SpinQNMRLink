"""Render parameter tables directly from public model JSON schemas."""

import json

from docutils.statemachine import StringList
from sphinx.util.docutils import SphinxDirective


class ParameterTable(SphinxDirective):
    required_arguments = 1

    def run(self):
        from spinqnmrlink import parameters_for

        parameters = parameters_for(self.arguments[0])
        schema = type(parameters).model_json_schema()
        values = parameters.model_dump(mode="json")
        chinese = self.config.language == "zh_CN"
        labels = (
            ("字段", "类型与约束", "参考值", "说明")
            if chinese
            else ("Field", "Type / constraints", "Reference", "Description")
        )
        lines = [".. list-table::", "   :header-rows: 1", "   :widths: 20 25 20 35", ""]
        lines += ["   * - " + labels[0]] + ["     - " + label for label in labels[1:]]
        for name, info in schema["properties"].items():
            alternatives = info.get("anyOf", [info])
            kind = " / ".join(
                part.get("type", part.get("$ref", "model").rsplit("/", 1)[-1])
                for part in alternatives
            )
            constraints = {
                k: info[k]
                for k in (
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "minItems",
                    "maxItems",
                    "enum",
                    "const",
                )
                if k in info
            }
            reference = json.dumps(values[name], ensure_ascii=False)
            if len(reference) > 70:
                reference = reference[:67] + "..."
            description = info.get("description", "Validated by the device-specific serializer.")
            description = description.replace("\n", " ")
            if name == "sample_frequency":
                description = (
                    "Sampling frequency in integer Hz; select exactly one of the enum values."
                )
            if chinese:
                descriptions = {
                    "freq_h": "氢共振频率，单位 MHz；序列化为 Hz。",
                    "freq_p": "磷共振频率，单位 MHz；序列化为 Hz。",
                    "custom_freq": "是否使用自定义共振频率；关闭时使用设备锁场频率。",
                    "relaxation_seconds": "弛豫时间，单位秒；适配器处理设备单位转换。",
                    "sample_delay_us": "采集延迟，单位微秒。",
                    "sample_count": "采集点数；设备及模式约束由序列化器验证。",
                    "sample_frequency": "采样频率，整数 Hz；必须从 enum 所列档位中选择一个。",
                    "sample_path": "采集通道；-1 表示全部（仅支持此值的模型适用）。",
                    "sample_qubits": "从零编号的采集比特；THREE 适配器转换为协议编号。",
                    "make_pps": "是否制备赝纯态 PPS。",
                    "calc_matrix": "是否请求矩阵计算。",
                    "pulses": "脉冲序列；宽度为微秒，幅度为百分比，相位为度，失谐为 Hz。",
                    "pulse": "三比特脉冲与梯度容器；h_pulse 只接受通道 0。",
                    "gradients": "梯度序列；电压为 V，时长为微秒。",
                    "circuit": "公共量子线路定义，门比特索引从零编号。",
                    "qubits_num": "线路比特数，由实际线路定义确定。",
                    "repeat": "设备协议定义的重复次数设置。",
                    "step_list": "Pauli 测量步骤，按设备及模式验证。",
                    "calibrate_sample": "设备端已经校准的样品序号。",
                    "using_pulse": "是否使用脉冲序列而不是量子门线路。",
                    "state_initialization": "是否执行量子态初始化。",
                }
                description = descriptions.get(name, description)
            if name == "sample_qubits" and self.arguments[0] == "triangulum.physical":
                description = (
                    "Triangulum 采集编号沿用 sampleQubit 协议原值，不执行 Lab THREE 的编号转换。"
                    if chinese
                    else "Triangulum acquisition indices retain the sampleQubit wire values; "
                    "the Lab THREE index conversion does not apply."
                )
            lines += [
                "   * - ``" + name + "``",
                "     - " + str(kind) + (" " + json.dumps(constraints) if constraints else ""),
                "     - ``" + reference.replace("`", "'") + "``",
                "     - " + description,
            ]
        from docutils import nodes

        node = nodes.container()
        self.state.nested_parse(StringList(lines), self.content_offset, node)
        return node.children


def setup(app):
    app.add_directive("sdk-parameters", ParameterTable)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
