#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 09:38
@Author : rxccai@gmail.com
@File   : workflow_entity.py
"""

from typing import Any, TypedDict, Annotated
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field

from .node_entity import NodeResult

# 工作流配置校验信息
WORKFLOW_CONFIG_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'
WORKFLOW_CONFIG_DESCRIPTION_MAX_LENGTH = 1024


def _process_dict(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """工作流状态字典归纳函数"""
    left = left or {}
    right = right or {}

    return {**left, **right}


def _process_node_results(left: list[NodeResult], right: list[NodeResult]) -> list[NodeResult]:
    """工作流状态节点结果列表归纳函数"""
    left = left or []
    right = right or []

    return left + right


class WorkflowConfig(BaseModel):
    """工作流配置信息"""
    account_id: UUID  # 用户的唯一标识数据
    name: str = ""  # 工作流名称，必须是英文
    description: str = ""  # 工作流描述信息，用于告知LLM什么时候需要调用工作流
    nodes: list[dict[str, Any]] = Field(default_factory=list)  # 工作流对应的节点列表信息
    edges: list[dict[str, Any]] = Field(default_factory=list)  # 工作流对应的边列表信息


class WorkflowState(TypedDict):
    """工作流图程序状态字典"""
    inputs: Annotated[dict[str, Any], _process_dict]  # 工作流的最初始输入，工具输入
    outputs: Annotated[dict[str, Any], _process_dict]  # 工作流的最终输出结果，工具输出
    node_results: Annotated[list[NodeResult], _process_node_results]  # 各节点的运行结果
