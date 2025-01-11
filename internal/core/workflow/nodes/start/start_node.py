#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 11:20
@Author : rxccai@gmail.com
@File   : start_node.py
"""
import time
from typing import Optional

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.variable_entity import VARIABLE_TYPE_DEFAULT_VALUE_MAP
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.exception import FailException
from .start_entity import StartNodeData


class StartNode(BaseNode):
    """开始节点"""

    node_data: StartNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """开始节点执行函数,该函数会提取状态中的输入信息并生成节点信息"""
        # 提取节点数据中的输入数据
        start_at = time.perf_counter()
        inputs = self.node_data.inputs

        # 循环遍历输入数据，并提取需要的数据，同时检测必填的数据是否传递，如果未传递则直接报错
        outputs = {}
        for input in inputs:
            input_value = state["inputs"].get(input.name, None)

            # 检测字段是否必填
            if input_value is None:
                if input.required:
                    raise FailException(f"工作流参数生成出错，{input.name}为必填参数")
                else:
                    input_value = VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(input.type)

            # 提取输出数据
            outputs[input.name] = input_value

        # 构建状态数据返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=state["inputs"],
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
