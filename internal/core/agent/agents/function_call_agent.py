#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:30
@Author : rxccai@gmail.com
@File   : function_call_agent.py
"""
from typing import Literal

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledGraph

from internal.core.agent.entities.agent_entity import AgentState
from .base_agent import BaseAgent


class FunctionCallAgent(BaseAgent):
    """基于函数调用/工具调用的智能体"""

    def run(self, query: str, history: list[AnyMessage] = None, long_term_memory: str = ""):
        if history is None:
            history = []
        agent = self._build_agent()

        return agent.invoke({
            "messages": [HumanMessage(content=query)],
            "history": history,
            "long_term_memory": long_term_memory,
        })

    def _build_agent(self) -> CompiledGraph:
        graph = StateGraph(AgentState)
        # 添加节点
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm", self._tools_condition)
        graph.add_edge("tools", "llm")

        agent = graph.compile()
        return agent

    def _long_term_memory_recall_node(self, state: AgentState) -> AgentState:
        """长期记忆召回节点"""
        pass

    def _llm_node(self, state: AgentState) -> AgentState:
        pass

    def _tools_node(self, state: AgentState) -> AgentState:
        pass

    @classmethod
    def _tools_condition(cls, state: AgentState) -> Literal["tools", "__end__"]:
        """检测下一个节点是执行tools节点，还是直接结束"""
        messages = state["messages"]
        ai_message = messages[-1]

        # 检测是否存在tools_call参数
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END
