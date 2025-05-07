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
@Time   : 2025/1/5 21:58
@Author : caixiaorong01@outlook.com
@File   : helper.py
"""
from typing import Any

from internal.core.workflow.entities.variable_entity import (
    VariableEntity,
    VariableValueType,
    VARIABLE_TYPE_MAP,
    VARIABLE_TYPE_DEFAULT_VALUE_MAP,
)
from internal.core.workflow.entities.workflow_entity import WorkflowState


def extract_variables_from_state(variables: list[VariableEntity], state: WorkflowState) -> dict[str, Any]:
    """从状态中提取变量映射值信息"""
    # 构建变量字典信息
    variables_dict = {}

    # 循环遍历输入变量实体
    for variable in variables:
        # 获取数据变量类型
        variable_type_cls = VARIABLE_TYPE_MAP.get(variable.type)

        # 判断数据是引用还是直接输入
        if variable.value.type == VariableValueType.LITERAL:
            variables_dict[variable.name] = variable_type_cls(variable.value.content)
        else:
            # 引用or生成数据类型，遍历节点获取数据
            for node_result in state["node_results"]:
                if node_result.node_data.id == variable.value.content.ref_node_id:
                    # 提取数据并完成数据强制转换
                    variables_dict[variable.name] = variable_type_cls(node_result.outputs.get(
                        variable.value.content.ref_var_name,
                        VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(variable.type)
                    ))
    return variables_dict
