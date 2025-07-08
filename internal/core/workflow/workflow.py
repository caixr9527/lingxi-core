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
@Time   : 2025/1/5 09:35
@Author : caixiaorong01@outlook.com
@File   : workflow.py
"""
from typing import Any, Optional, Iterator

from flask import current_app
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import PrivateAttr, BaseModel, Field, create_model

from internal.exception import ValidateException
from .entities.node_entity import NodeType
from .entities.variable_entity import VARIABLE_TYPE_MAP
from .entities.workflow_entity import WorkflowConfig, WorkflowState
from .nodes import (
    StartNode,
    EndNode,
    LLMNode,
    TemplateTransformNode,
    DatasetRetrievalNode,
    CodeNode,
    ToolNode,
    HttpRequestNode,
    QuestionClassifierNode,
    QuestionClassifierNodeData,
    IterationNode,
    ConditionSelectorNode,
    ConditionSelectNodeData,
)

NodeClasses = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
    NodeType.TEMPLATE_TRANSFORM: TemplateTransformNode,
    NodeType.DATASET_RETRIEVAL: DatasetRetrievalNode,
    NodeType.CODE: CodeNode,
    NodeType.TOOL: ToolNode,
    NodeType.HTTP_REQUEST: HttpRequestNode,
    NodeType.QUESTION_CLASSIFIER: QuestionClassifierNode,
    NodeType.ITERATION: IterationNode,
    NodeType.CONDITION_SELECTOR: ConditionSelectorNode,
}


class Workflow(BaseTool):
    """工作流工具类"""
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            args_schema=self._build_args_schema(workflow_config),
            **kwargs
        )

        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    @classmethod
    def _build_args_schema(cls, workflow_config: WorkflowConfig) -> type[BaseModel]:
        """构建输入参数结构体"""
        # 提取开始节点的输入参数信息
        fields = {}
        inputs = next(
            (node.inputs for node in workflow_config.nodes if node.node_type == NodeType.START),
            []
        )

        # 循环遍历所有输入信息并创建字段映射
        for input in inputs:
            field_name = input.name
            field_type = VARIABLE_TYPE_MAP.get(input.type, str)
            field_required = input.required
            field_description = input.description

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description),
            )

        # 调用create_model创建一个BaseModel类，并使用上述分析好的字段
        return create_model("DynamicModel", **fields)

    def _build_workflow(self) -> CompiledStateGraph:
        """构建编译后的工作流图程序"""
        # 创建graph图程序结构
        graph = StateGraph(WorkflowState)

        # 提取nodes和edges信息
        nodes = self._workflow_config.nodes
        edges = self._workflow_config.edges

        # 循环遍历nodes节点信息添加节点
        for node in nodes:
            node_flag = f"{node.node_type.value}_{node.id}"
            if node.node_type == NodeType.START:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.START](node_data=node),
                )
            elif node.node_type == NodeType.LLM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.LLM](node_data=node),
                )
            elif node.node_type == NodeType.TEMPLATE_TRANSFORM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TEMPLATE_TRANSFORM](node_data=node),
                )
            elif node.node_type == NodeType.DATASET_RETRIEVAL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.DATASET_RETRIEVAL](
                        flask_app=current_app._get_current_object(),
                        account_id=self._workflow_config.account_id,
                        node_data=node,
                    ),
                )
            elif node.node_type == NodeType.CODE:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.CODE](node_data=node),
                )
            elif node.node_type == NodeType.TOOL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TOOL](node_data=node),
                )
            elif node.node_type == NodeType.HTTP_REQUEST:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.HTTP_REQUEST](node_data=node),
                )
            elif node.node_type == NodeType.END:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.END](node_data=node),
                )
            elif node.node_type == NodeType.QUESTION_CLASSIFIER:
                # 问题分类节点为条件边对应的节点，可以添加一个虚拟起始节点并返回空字典什么都不处理，让条件边可以快速找到起点
                graph.add_node(
                    node_flag,
                    lambda state: {"node_results": []}
                )

                # 同步获取意图识别节点的数据，添加虚拟终止节点(每个分类一个节点)并返回空字典什么都不处理，让意图节点实现并行运行
                assert isinstance(node, QuestionClassifierNodeData)
                for item in node.classes:
                    graph.add_node(
                        f"qc_source_handle_{str(item.source_handle_id)}",
                        lambda state: {"node_results": []}
                    )

                # 将虚拟起点和终点使用条件边进行拼接
                graph.add_conditional_edges(
                    node_flag,
                    NodeClasses[NodeType.QUESTION_CLASSIFIER](node_data=node)
                )
            elif node.node_type == NodeType.CONDITION_SELECTOR:
                graph.add_node(
                    node_flag,
                    lambda state: {"node_results": []}
                )
                assert isinstance(node, ConditionSelectNodeData)
                for item in node.classes:
                    graph.add_node(
                        f"cn_source_handle_{str(item.source_handle_id)}",
                        lambda state: {"node_results": []}
                    )

                graph.add_conditional_edges(
                    node_flag,
                    NodeClasses[NodeType.CONDITION_SELECTOR](node_data=node)
                )

            elif node.node_type == NodeType.ITERATION:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.ITERATION](node_data=node)
                )
            else:
                raise ValidateException("工作流节点类型错误，请核实后重试")

        # 循环遍历edges信息添加边
        parallel_edges = {}  # key:终点，value:起点列表
        start_node = ""
        end_node = ""
        non_parallel_nodes = []  # 用于存储不能并行执行的节点列表信息(主要用来处理意图节点的虚拟起点和终点)
        for edge in edges:
            # 计算并获取并行边
            source_node = f"{edge.source_type.value}_{edge.source}"
            target_node = f"{edge.target_type.value}_{edge.target}"
            if edge.source_type == NodeType.QUESTION_CLASSIFIER:
                # 更新意图识别的起点，使用虚拟节点进行拼接
                source_node = f"qc_source_handle_{str(edge.source_handle_id)}"
                non_parallel_nodes.extend([source_node, target_node])

            if edge.source_type == NodeType.CONDITION_SELECTOR:
                source_node = f"cn_source_handle_{str(edge.source_handle_id)}"
                non_parallel_nodes.extend([source_node, target_node])

            if target_node not in parallel_edges:
                parallel_edges[target_node] = [source_node]
            else:
                parallel_edges[target_node].append(source_node)

            # 检测特殊节点（开始节点、结束节点），需要写成两个if的格式，避免只有一条边的情况识别失败
            if edge.source_type == NodeType.START:
                start_node = f"{edge.source_type.value}_{edge.source}"
            if edge.target_type == NodeType.END:
                end_node = f"{edge.target_type.value}_{edge.target}"

        # 设置开始和终点
        graph.set_entry_point(start_node)
        graph.set_finish_point(end_node)

        # 循环遍历合并边
        for target_node, source_nodes in parallel_edges.items():
            # 循环遍历意图识别节点的下一条边并单独添加
            source_nodes_tmp = [*source_nodes]
            for item in non_parallel_nodes:
                if item in source_nodes_tmp:
                    source_nodes_tmp.remove(item)
                    graph.add_edge(item, target_node)

            # 正常添加其他边
            if len(source_nodes_tmp) > 0:
                graph.add_edge(source_nodes_tmp, target_node)

        # 构建图程序并编译
        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        # 调用工作流获取结果
        result = self._workflow.invoke({"inputs": kwargs})
        return result.get("outputs", {})

    def stream(
            self,
            input: Input,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        return self._workflow.stream({"inputs": input})
