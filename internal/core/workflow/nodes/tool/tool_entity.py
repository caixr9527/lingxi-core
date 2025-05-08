#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright [2025] [caixiaorong]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@Time   : 2025/1/9 21:32
@Author : caixiaorong01@outlook.com
@File   : tool_entity.py.py
"""
from typing import Any, Literal

from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType


class ToolNodeData(BaseNodeData):
    """工具节点数据"""
    tool_type: Literal["builtin_tool", "api_tool", ""] = Field(alias="type")  # 工具类型
    provider_id: str  # 工具提供者id
    tool_id: str  # 工具id
    params: dict[str, Any] = Field(default_factory=dict)  # 内置工具设置参数
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量列表
    outputs: list[VariableEntity] = Field(
        exclude=True,
        default_factory=lambda: [
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED})
        ]
    )  # 输出字段列表信息
