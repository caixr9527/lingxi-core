#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:18
@Author : rxccai@gmail.com
@File   : base_agent.py
"""
import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Any, Iterator

from langchain_core.language_models import BaseLanguageModel
from langchain_core.load import Serializable
from langchain_core.pydantic_v1 import PrivateAttr
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import AgentResult, AgentThought
from internal.exception import FailException
from .agent_queue_manager import AgentQueueManager


class BaseAgent(Serializable, Runnable):
    llm: BaseLanguageModel
    agent_config: AgentConfig
    _agent: CompiledStateGraph = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self,
                 llm: BaseLanguageModel,
                 agent_config: AgentConfig,
                 *args,
                 **kwargs):
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            invoke_from=agent_config.invoke_from
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        raise NotImplementedError("_build_agent函数未实现")

    def invoke(self, input: AgentState, config: Optional[RunnableConfig] = None) -> AgentResult:
        pass

    def stream(
            self,
            input: AgentState,
            config: Optional[RunnableConfig] = None,
            **kwargs: Optional[Any],
    ) -> Iterator[AgentThought]:
        if not self._agent:
            raise FailException("智能体未成功构建，请核实后尝试")

        input["task_id"] = input.get("task_id", uuid.uuid4())
        input["history"] = input.get("history", [])
        input["iteration_count"] = input.get("iteration_count", 0)
        thread = Thread(
            target=self._agent.invoke,
            args=(input,)
        )
        thread.start()

        yield from self._agent_queue_manager.listen(input["task_id"])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        return self._agent_queue_manager
