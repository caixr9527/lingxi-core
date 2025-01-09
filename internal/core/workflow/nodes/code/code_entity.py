#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/9 21:09
@Author : rxccai@gmail.com
@File   : code_entity.py
"""
from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity

# 默认的代码
DEFAULT_CODE = """
def main(params):
    return params
"""


class CodeNodeData(BaseNodeData):
    """Python代码执行节点数据"""
    code: str = DEFAULT_CODE  # 需要执行的Python代码
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量列表
    outputs: list[VariableEntity] = Field(default_factory=list)  # 输出变量列表
