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
@Time   : 2025/1/5 21:53
@Author : caixiaorong01@outlook.com
@File   : template_transform_node.py.py
"""
import time
from typing import Optional

from internal.core.workflow.utils.helper import extract_variables_from_state
from jinja2 import Template
from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from .template_transform_entity import TemplateTransformNodeData


class TemplateTransformNode(BaseNode):
    """模板转换节点，将多个变量信息合并成一个"""
    node_data: TemplateTransformNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """模板转换节点执行函数，将传递的多个变量合并成字符串后返回"""
        # 提取节点中的输入数据
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 使用jinja2格式模板信息
        template = Template(self.node_data.template)
        template_value = template.render(**inputs_dict)

        # 提取并构建输出数据结构
        outputs = {"output": template_value}

        # 构建响应状态并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
