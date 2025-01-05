#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 09:35
@Author : rxccai@gmail.com
@File   : workflow.py
"""
from typing import Any, Optional, Iterator

from langchain_core.pydantic_v1 import PrivateAttr
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from .entities.workflow_entity import WorkflowConfig, WorkflowState


class Workflow(BaseTool):
    """工作流工具类"""
    _workflow_config: WorkflowConfig = PrivateAttr(None), WorkflowState
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs: Any):
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            **kwargs)
        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        graph = StateGraph(WorkflowState)
        # 提取nodes和edge信息
        # 遍历nodes节点信息添加节点
        # 遍历edges节点信息添加边
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
