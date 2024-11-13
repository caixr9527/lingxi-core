#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:18
@Author : rxccai@gmail.com
@File   : base_agent.py
"""
from abc import ABC, abstractmethod
from typing import Generator

from langchain_core.messages import AnyMessage

from internal.core.agent.entities.agent_entity import AgentConfig
from internal.core.agent.entities.queue_entity import AgentQueueEvent
from .agent_queue_manager import AgentQueueManager


class BaseAgent(ABC):
    agent_config: AgentConfig
    agent_queue_manager: AgentQueueManager

    def __init__(self, agent_config: AgentConfig, agent_queue_manager: AgentQueueManager):
        self.agent_queue_manager = agent_queue_manager
        self.agent_config = agent_config

    @abstractmethod
    def run(
            self,
            query: str,
            history: list[AnyMessage] = None,
            long_term_memory: str = ""
    ) -> Generator[AgentQueueEvent, None, None]:
        raise NotImplementedError("Agent智能体run函数未实现")
