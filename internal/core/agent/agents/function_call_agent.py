#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 21:30
@Author : rxccai@gmail.com
@File   : function_call_agent.py
"""
import json
import time
import uuid
from threading import Thread
from typing import Literal, Generator

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, RemoveMessage, ToolMessage
from langchain_core.messages import messages_to_dict
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledGraph

from internal.core.agent.entities.agent_entity import AgentState, AGENT_SYSTEM_PROMPT_TEMPLATE, \
    DATASET_RETRIEVAL_TOOL_NAME
from internal.core.agent.entities.queue_entity import AgentQueueEvent, QueueEvent
from internal.exception import FailException
from .base_agent import BaseAgent


class FunctionCallAgent(BaseAgent):
    """基于函数调用/工具调用的智能体"""

    def run(
            self,
            query: str,
            history: list[AnyMessage] = None,
            long_term_memory: str = ""
    ) -> Generator[AgentQueueEvent, None, None]:
        if history is None:
            history = []
        agent = self._build_agent()
        thread = Thread(target=agent.invoke,
                        args=(
                            {
                                "messages": [HumanMessage(content=query)],
                                "history": history,
                                "long_term_memory": long_term_memory,
                            },
                        ))
        thread.start()
        yield from self.agent_queue_manager.listen()

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
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=uuid.uuid4(),
                task_id=self.agent_queue_manager.task_id,
                event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                observation=long_term_memory,
            ))

        preset_messages = [
            SystemMessage(AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                preset_prompt=self.agent_config.preset_prompt,
                long_term_memory=long_term_memory,
            ))
        ]
        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            if len(history) % 2 != 0:
                raise FailException("智能体历史消息列表格式错误")
            preset_messages.extend(history)
        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(human_message.content))

        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
        }

    def _llm_node(self, state: AgentState) -> AgentState:
        id = uuid.uuid4()
        start_at = time.perf_counter()
        llm = self.agent_config.llm
        if hasattr(llm, "bind_tools") and callable(getattr(llm, "bind_tools")) and len(self.agent_config.tools) > 0:
            llm = llm.bind_tools(self.agent_config.tools)

        gathered = None
        is_first_chunk = True
        generation_type = ""
        for chunk in llm.stream(state["messages"]):
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

            if not generation_type:
                if chunk.tool_calls:
                    generation_type = "thought"
                elif chunk.content:
                    generation_type = "message"

            if generation_type == "message":
                self.agent_queue_manager.publish(AgentQueueEvent(
                    id=id,
                    task_id=self.agent_queue_manager.task_id,
                    event=QueueEvent.AGENT_MESSAGE,
                    thought=chunk.content,
                    messages=messages_to_dict(state["messages"]),
                    answer=chunk.content,
                    latency=(time.perf_counter() - start_at)
                ))

        if generation_type == "thought":
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=id,
                task_id=self.agent_queue_manager.task_id,
                event=QueueEvent.AGENT_THOUGHT,
                messages=messages_to_dict(state["messages"]),
                latency=(time.perf_counter() - start_at)
            ))
        elif generation_type == "message":
            self.agent_queue_manager.stop_listen()

        return {"messages": [gathered]}

    def _tools_node(self, state: AgentState) -> AgentState:
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        tool_calls = state["messages"][-1].tool_calls

        messages = []
        for tool_call in tool_calls:
            id = uuid.uuid4()
            start_at = time.perf_counter()

            tool = tools_by_name[tool_call["name"]]
            tool_result = tool.invoke(tool_call["args"])
            messages.append(ToolMessage(
                tool_call_id=tool_call["id"],
                content=json.dumps(tool_result),
                name=tool_call["name"],
            ))
            event = (
                QueueEvent.AGENT_ACTION
                if tool_call["name"] != DATASET_RETRIEVAL_TOOL_NAME
                else QueueEvent.DATASET_RETRIEVAL
            )
            self.agent_queue_manager.publish(AgentQueueEvent(
                id=id,
                task_id=self.agent_queue_manager.task_id,
                event=event,
                observation=json.dumps(tool_result),
                tool=tool_call["name"],
                tool_input=tool_call["args"],
                latency=(time.perf_counter() - start_at)
            ))
        return {"messages": messages}

    @classmethod
    def _tools_condition(cls, state: AgentState) -> Literal["tools", "__end__"]:
        """检测下一个节点是执行tools节点，还是直接结束"""
        messages = state["messages"]
        ai_message = messages[-1]

        # 检测是否存在tools_call参数
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END
