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
@Time   : 2025/4/14 20:16
@Author : caixiaorong01@outlook.com
@File   : question_classifier_node.py
"""
import json
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.constants import END

from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from .question_classifier_entity import QuestionClassifierNodeData, QUESTION_CLASSIFIER_SYSTEM_PROMPT


class QuestionClassifierNode(BaseNode):
    """问题分类器节点"""
    node_data: QuestionClassifierNodeData

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> str:
        """覆盖重写invoke实现问题分类器节点，执行问题分类后返回节点的名称，如果LLM判断错误默认返回第一个节点名称"""
        # 企图节点输入变量字典映射
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 构建问题分类提示prompt模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUESTION_CLASSIFIER_SYSTEM_PROMPT),
            ("human", "{query}"),
        ])

        # 创建LLM实例客户端，使用gpt-4o-mini作为基座模型，并配置温度与最大输出tokens
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=512,
        )

        # 构建分类链
        chain = prompt | llm | StrOutputParser()

        # 获取分类调用结果
        node_flag = chain.invoke({
            "preset_classes": json.dumps(
                [
                    {
                        "query": class_config.query,
                        "class": f"qc_source_handle_{str(class_config.source_handle_id)}"
                    } for class_config in self.node_data.classes
                ]
            ),
            "query": inputs_dict.get("query", "用户没有输入任何内容")
        })

        # 获取所有分类信息
        all_classes = [f"qc_source_handle_{str(item.source_handle_id)}" for item in self.node_data.classes]

        # 检测获取的分类标识是否在规定列表内，并提取节点标识
        if len(all_classes) == 0:
            node_flag = END
        elif node_flag not in all_classes:
            node_flag = all_classes[0]

        return node_flag
