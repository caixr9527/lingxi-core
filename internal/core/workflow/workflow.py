#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 09:35
@Author : rxccai@gmail.com
@File   : workflow.py
"""
from typing import Any, Optional, Iterator

from flask import current_app
from langchain_core.pydantic_v1 import PrivateAttr, BaseModel, Field, create_model
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

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
    HttpRequestNode
)

NodeClasses = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
    NodeType.LLM: LLMNode,
    NodeType.TEMPLATE_TRANSFORM: TemplateTransformNode,
    NodeType.DATASET_RETRIEVAL: DatasetRetrievalNode,
    NodeType.CODE: CodeNode,
    NodeType.TOOL: ToolNode,
    NodeType.HTTP_REQUEST: HttpRequestNode
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
        # 1.提取开始节点的输入参数信息
        fields = {}
        inputs = next(
            (node.get("inputs", []) for node in workflow_config.nodes if node.get("node_type") == NodeType.START),
            []
        )

        # 2.循环遍历所有输入信息并创建字段映射
        for input in inputs:
            field_name = input.name
            field_type = VARIABLE_TYPE_MAP.get(input.type, str)
            field_required = input.required
            field_description = input.description

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description),
            )

        # 3.调用create_model创建一个BaseModel类，并使用上述分析好的字段
        return create_model("DynamicModel", **fields)

    def _build_workflow(self) -> CompiledStateGraph:
        graph = StateGraph(WorkflowState)
        # 提取nodes和edge信息
        nodes = self._workflow_config.nodes
        edges = self._workflow_config.edges
        # 遍历nodes节点信息添加节点
        for node in nodes:
            node_flag = f"{node.get('node_type')}_{node.get('id')}"
            if node.get("node_type") == NodeType.START:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.START](node_data=node),
                )
            elif node.get("node_type") == NodeType.LLM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.LLM](node_data=node),
                )
            elif node.get("node_type") == NodeType.TEMPLATE_TRANSFORM:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TEMPLATE_TRANSFORM](node_data=node),
                )
            elif node.get("node_type") == NodeType.DATASET_RETRIEVAL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.DATASET_RETRIEVAL](
                        flask_app=current_app._get_current_object(),
                        account_id=self._workflow_config.account_id,
                        node_data=node
                    ),
                )
            elif node.get("node_type") == NodeType.CODE:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.CODE](node_data=node),
                )
            elif node.get("node_type") == NodeType.TOOL:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.TOOL](node_data=node),
                )
            elif node.get("node_type") == NodeType.HTTP_REQUEST:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.HTTP_REQUEST](node_data=node),
                )
            elif node.get("node_type") == NodeType.END:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.END](node_data=node),
                )

        # 遍历edges节点信息添加边
        parallel_edges = {}  # key:终点，value:起点列表
        start_node = ""
        end_node = ""

        for edge in edges:
            # 计算并获取并行边
            source_node = f"{edge.get('source_type')}_{edge.get('source')}"
            target_node = f"{edge.get('target_type')}_{edge.get('target')}"
            if target_node not in parallel_edges:
                parallel_edges[target_node] = [source_node]
            else:
                parallel_edges[target_node].append(source_node)

            # 检测特殊节点（开始、结束）
            if edge.get("source_type") == NodeType.START:
                start_node = f"{edge.get('source_type')}_{edge.get('source')}"
            elif edge.get("target_type") == NodeType.END:
                end_node = f"{edge.get('target_type')}_{edge.get('target')}"

        # 设置开始和终点
        graph.set_entry_point(start_node)
        graph.set_finish_point(end_node)

        # 循环遍历合并边
        for target_node, source_nodes in parallel_edges.items():
            graph.add_edge(source_nodes, target_node)

        # 构建并编译
        return graph.compile()

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        return self._workflow.invoke({"inputs": kwargs})

    def stream(
            self,
            input: Input,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[Output]:
        return self._workflow.stream({"inputs": input})
