#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:18
@Author : rxccai@gmail.com
@File   : base_agent.py
"""
from abc import ABC, abstractmethod

from langchain_core.messages import AnyMessage

from internal.core.agent.entities.agent_entity import AgentConfig


class BaseAgent(ABC):
    agent_config: AgentConfig

    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config

    @abstractmethod
    def run(
            self,
            query: str,
            history: list[AnyMessage] = None,
            long_term_memory: str = ""
    ):
        raise NotImplementedError("Agent智能体run函数未实现")
