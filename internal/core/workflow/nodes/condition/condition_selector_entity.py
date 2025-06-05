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
@Time   : 2025/6/04 20:15
@Author : caixiaorong01@outlook.com
@File   : condition_selector_entity.py
"""
from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity
from langchain_core.pydantic_v1 import Field, validator, BaseModel


class ClassConfig(BaseModel):
    variable: str = Field(default="")
    parameter: str = Field(default="")
    condition_type: str = Field(default="") # 条件判断类型


class ClassConfigGroup(BaseModel):
    condition_group: list[ClassConfig] = Field(default_factory=list)
    logical_type: str = Field(default="")
    priority: int = Field(default=0)
    node_id: str = Field(default="")  # 该分类连接的节点id
    node_type: str = Field(default="")  # 该分类连接的节点类型
    source_handle_id: str = Field(default="")  # 起点句柄id


class ConditionSelectNodeData(BaseNodeData):
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量信息
    outputs: list[VariableEntity] = Field(default_factory=lambda: [])
    classes: list[ClassConfigGroup] = Field(default_factory=list)

    @validator("outputs")
    def validate_outputs(cls, value: list[VariableEntity]):
        """重写覆盖outputs的输出，让其变成一个只读变量"""
        return []