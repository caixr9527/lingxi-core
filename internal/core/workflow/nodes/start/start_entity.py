#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 11:11
@Author : rxccai@gmail.com
@File   : start_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    inputs: list[VariableEntity] = Field(default_factory=list)  # 开始节点的输入变量信息
