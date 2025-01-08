#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 14:44
@Author : rxccai@gmail.com
@File   : end_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class EndNodeData(BaseNodeData):
    """结束节点数据"""
    outputs: list[VariableEntity] = Field(default_factory=list)  # 结束节点需要输出的数据
