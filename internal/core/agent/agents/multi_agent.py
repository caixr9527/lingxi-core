#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright [2025] [caixiaorong]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@Time   : 2025/7/24 22:50
@Author : caixiaorong01@outlook.com
@File   : multi_agent.py
"""
import json
import logging
import time
import uuid
from typing import Any, Literal

from langchain_core.messages import ToolMessage
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentState
from internal.core.agent.entities.queue_entity import QueueEvent, AgentThought
from .function_call_agent import FunctionCallAgent


class MultiAgent(FunctionCallAgent):

    def _build_agent(self) -> CompiledStateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("preset_operation", self._preset_operation_node)
        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)

        path_map = {END: END, "tools": "tools"}
        if len(self.collaborative_agent) > 0:
            for name in self.collaborative_agent.keys():
                graph.add_node(name, self._sub_agent)
                graph.add_edge(name, "llm")
                path_map[name] = name

        graph.set_entry_point("preset_operation")
        graph.add_conditional_edges("preset_operation", self._preset_operation_condition)
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges("llm",
                                    self._get_sub_agent_condition,
                                    path_map
                                    )
        graph.add_edge("tools", "llm")
        agent = graph.compile()
        return agent

    def _sub_agent(self, state: AgentState) -> AgentState:

        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}
        tool_calls = state["messages"][-1].tool_calls

        tool_message = []
        messages = []
        for tool_call in tool_calls:
            id = uuid.uuid4()
            start_at = time.perf_counter()
            sub_agent = self.collaborative_agent.get(tool_call["name"])

            agent_state = None
            try:
                tool = tools_by_name[tool_call["name"]]
                args = {
                    "task_description": tool_call["args"]["task_description"],
                    "history": state["history"],
                    "long_term_memory": state["long_term_memory"]
                }
                agent_state = tool.invoke(args)
                answer = f"成功调度智能体《{sub_agent.zh_name}》"
            except Exception as e:
                # 添加错误工具信息
                answer = f"{sub_agent.zh_name}执行出错: {str(e)}"
                logging.exception(answer)

            tool_message.append(ToolMessage(
                tool_call_id=tool_call["id"],
                content=json.dumps(answer, ensure_ascii=False),
                name=tool_call["name"],
            ))
            if agent_state:
                messages.extend(agent_state["messages"])
            self.agent_queue_manager.publish(state["task_id"], AgentThought(
                id=id,
                task_id=state["task_id"],
                event=QueueEvent.AGENT_DISPATCH,
                observation=json.dumps(answer, ensure_ascii=False),
                tool=tool_call["name"],
                tool_input=tool_call["args"],
                latency=(time.perf_counter() - start_at),
            ))

        return {"messages": tool_message + messages,
                "iteration_count": state["iteration_count"],
                "task_id": state["task_id"],
                "history": state["history"],
                "long_term_memory": state["long_term_memory"]}

    def _get_sub_agent_condition(self, state: AgentState):
        agent_names = list(self.collaborative_agent.keys())
        return_type = Literal[tuple(agent_names) + ("tools", "__end__")] if agent_names else Literal["tools", "__end__"]

        def _sub_agent_condition() -> return_type:
            messages = state["messages"]
            ai_message = messages[-1]
            if (hasattr(ai_message, "tool_calls")
                    and len(ai_message.tool_calls) > 0):
                if not self._is_tools(ai_message.tool_calls):
                    return ai_message.tool_calls[0]["name"]
                else:
                    return "tools"
            return END

        return _sub_agent_condition()

    @classmethod
    def _is_tools(cls, tool_calls: list[Any]) -> bool:
        for tool_call in tool_calls:
            if tool_call["name"].startswith("transfer_to_"):
                return False

        return True
