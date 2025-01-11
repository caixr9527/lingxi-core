#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 16:07
@Author : rxccai@gmail.com
@File   : llm_node.py
"""
from typing import Optional

from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from internal.core.workflow.entities.node_entity import NodeStatus, NodeResult
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .llm_entity import LLMNodeData


class LLMNode(BaseNode):
    _node_data_cls = LLMNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 使用jinja2格式化模板信息
        template = Template(self.node_data.prompt)
        prompt_value = template.render(**inputs_dict)

        # todo:3.根据配置创建LLM实例，等待多LLM接入时需要完善
        llm = ChatOpenAI(
            model=self.node_data.language_model_config.get("model", "gpt-4o-mini"),
            **self.node_data.language_model_config.get("parameters", {}),
        )

        # 使用stream来代替invoke，避免接口长时间未响应超时
        content = llm.invoke(prompt_value).content

        # 提取并构建输出数据结构
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = content
        else:
            outputs["output"] = content

        # 构建响应状态并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                )
            ]
        }
