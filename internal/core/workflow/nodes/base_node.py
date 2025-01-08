#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 11:08
@Author : rxccai@gmail.com
@File   : base_node.py
"""
from abc import ABC
from typing import Any

from langchain_core.runnables import RunnableSerializable

from internal.core.workflow.entities.node_entity import BaseNodeData


class BaseNode(RunnableSerializable, ABC):
    _node_data_cls: type[BaseNodeData]
    node_data: BaseNodeData

    def __init__(self, *args: Any, node_data: dict[str, Any], **kwargs: Any):
        super().__init__(*args, node_data=self._node_data_cls(**node_data), **kwargs)
