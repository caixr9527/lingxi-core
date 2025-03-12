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
@Time   : 2025/1/5 10:20
@Author : rxccai@gmail.com
@File   : node_entity.py.py
"""
from enum import Enum
from typing import Any
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field


class NodeType(str, Enum):
    """节点类型枚举"""
    START = "start"
    LLM = "llm"
    TOOL = "tool"
    CODE = "code"
    DATASET_RETRIEVAL = "dataset_retrieval"
    HTTP_REQUEST = "http_request"
    TEMPLATE_TRANSFORM = "template_transform"
    END = "end"


class BaseNodeData(BaseModel):
    """基础节点数据"""

    class Position(BaseModel):
        """节点坐标基础模型"""
        x: float = 0
        y: float = 0

    class Config:
        allow_population_by_field_name = True  # 允许通过字段名进行赋值

    id: UUID  # 节点id，数值必须唯一
    node_type: NodeType  # 节点类型
    title: str = ""  # 节点标题，数据也必须唯一
    description: str = ""  # 节点描述信息
    position: Position = Field(default_factory=lambda: {"x": 0, "y": 0})  # 节点对应的坐标信息


class NodeStatus(str, Enum):
    """节点状态"""
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NodeResult(BaseModel):
    """节点运行结果"""
    node_data: BaseNodeData  # 节点基础数据
    status: NodeStatus = NodeStatus.RUNNING  # 节点运行状态
    inputs: dict[str, Any] = Field(default_factory=dict)  # 节点的输入数据
    outputs: dict[str, Any] = Field(default_factory=dict)  # 节点的输出数据
    latency: float = 0  # 节点响应耗时
    error: str = ""  # 节点运行错误信息
