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
@Time   : 2025/4/16 20:41
@Author : rxccai@gmail.com
@File   : iteration_entity.py.py
"""
from uuid import UUID

from langchain_core.pydantic_v1 import Field, validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType, VariableValueType
from internal.exception import FailException


class IterationNodeData(BaseNodeData):
    """迭代节点数据"""
    workflow_ids: list[UUID]  # 需要迭代的工作流id
    inputs: list[VariableEntity] = Field(default_factory=lambda: [
        VariableEntity(
            name="inputs",
            type=VariableType.LIST_STRING,
            value={"type": VariableValueType.LITERAL, "content": []}
        )
    ])  # 输入变量列表
    outputs: list[VariableEntity] = Field(default_factory=list)

    @validator("workflow_ids")
    def validate_workflow_ids(cls, value: list[UUID]):
        """校验迭代的工作流数量是否小于等于1"""
        if len(value) > 1:
            raise FailException("迭代节点只能绑定一个工作流")
        return value

    @validator("inputs")
    def validate_inputs(cls, value: list[VariableEntity]):
        """校验输入变量是否正确"""
        # 判断是否一个输入变量，如果不是则抛出错误
        if len(value) != 1:
            raise FailException("迭代节点输入变量信息错误")

        # 判断输入变量类型及字段是否出错
        iteration_inputs = value[0]
        allow_types = [
            VariableType.LIST_STRING,
            VariableType.LIST_INT,
            VariableType.LIST_FLOAT,
            VariableType.LIST_BOOLEAN,
        ]
        if (
                iteration_inputs.name != "inputs"
                or iteration_inputs.type not in allow_types
                or iteration_inputs.required is False
        ):
            raise FailException("迭代节点输入变量名字/类型/必填属性出错")

        return value

    @validator("outputs")
    def validate_outputs(cls, value: list[VariableEntity]):
        """固定节点的输出为列表型字符串，该节点会将工作流中的所有结果迭代存储到该列表中"""
        return [
            VariableEntity(name="outputs", value={"type": VariableValueType.GENERATED})
        ]
