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
@Time   : 2025/4/14 20:15
@Author : rxccai@gmail.com
@File   : question_classifier_entity.py
"""
from langchain_core.pydantic_v1 import Field, validator, BaseModel

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType
from internal.exception import FailException

# 问题分类器系统预设prompt
QUESTION_CLASSIFIER_SYSTEM_PROMPT = """# 角色
你是一个文本分类引擎，负责对输入的文本进行分类，并返回相应的分类名称，如果没有匹配的分类则返回第一个分类，预设分类会以json列表的名称提供，请注意正确识别。

## 技能
### 技能1：文本分类
- 接收用户输入的文本内容。
- 使用自然语言处理技术分析文本特征。
- 根据预设的分类信息，将文本准确划分至相应类别，并返回分类名称。
- 分类名称格式为xxx_uuid，例如: qc_source_handle_1e3ac414-52f9-48f5-94fd-fbf4d3fe2df7，请注意识别。

## 预设分类信息
预设分类信息如下:
{preset_classes}

## 限制
- 仅处理文本分类相关任务。
- 输出仅包含分类名称，不提供额外解释或信息。
- 确保分类结果的准确性，避免错误分类。
- 使用预设的分类标准进行判断，不进行主观解释。 
- 如果预设的分类没有符合条件，请直接返回第一个分类。"""


class ClassConfig(BaseModel):
    """问题分类器配置，存储分类query、连接的节点类型/id"""
    query: str = Field(default="")  # 问题分类对应的query描述
    node_id: str = Field(default="")  # 该分类连接的节点id
    node_type: str = Field(default="")  # 该分类连接的节点类型
    source_handle_id: str = Field(default="")  # 起点句柄id


class QuestionClassifierNodeData(BaseNodeData):
    """问题分类器/意图识别节点数据"""
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量信息
    outputs: list[VariableEntity] = Field(default_factory=lambda: [])
    classes: list[ClassConfig] = Field(default_factory=list)

    @validator("inputs")
    def validate_inputs(cls, value: list[VariableEntity]):
        """校验输入变量信息"""
        # 判断是否只有一个输入变量，如果有多个则抛出错误
        if len(value) != 1:
            raise FailException("问题分类节点输入变量信息出错")

        # 判断输入变量类型及字段名称是否出错
        query_input = value[0]
        if query_input.name != "query" or query_input.type != VariableType.STRING or query_input.required is False:
            raise FailException("问题分类节点输入变量名字/类型/必填属性出错")

        return value

    @validator("outputs")
    def validate_outputs(cls, value: list[VariableEntity]):
        """重写覆盖outputs的输出，让其变成一个只读变量"""
        return []
