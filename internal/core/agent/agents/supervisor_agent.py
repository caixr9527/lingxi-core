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
@Time   : 2025/7/18 12:03
@Author : caixiaorong01@outlook.com
@File   : supervisor_agent.py
"""
from typing import Annotated

from langchain_core.tools import tool, InjectedToolCallId
from langgraph.constants import END
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from internal.core.agent.entities.agent_entity import AgentState
from .react_agent import ReACTAgent


class SupervisorAgent(ReACTAgent):

    def _build_agent(self) -> CompiledStateGraph | None:
        supervisor_agent = super()._build_agent()
        supervisor_agent.name = "supervisor"
        graph = StateGraph(AgentState)
        graph.add_node(supervisor_agent, destinations=tuple(self.collaborative_agent.keys()) + (END,))

        for name in self.collaborative_agent.keys():
            agent = self.collaborative_agent[name]
            graph.add_node(agent)
            graph.add_edge(name, supervisor_agent.name)

        graph.add_edge(START, supervisor_agent.name)
        agent = graph.compile()
        from IPython.display import display, Image
        display(Image(agent.get_graph().draw_mermaid_png()))
        return agent

    def create_handoff_tool(self, *, agent_name: str, description: str | None = None):
        name = f"transfer_to_{agent_name}"
        description = description or f"Ask {agent_name} for help."

        @tool(name, description=description)
        def handoff_tool(
                state: Annotated[MessagesState, InjectedState],
                tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            tool_message = {
                "role": "tool",
                "content": f"Successfully transferred to {agent_name}",
                "name": name,
                "tool_call_id": tool_call_id,
            }
            return Command(
                goto=agent_name,
                update={**state, "messages": state["messages"] + [tool_message]},
                graph=Command.PARENT,
            )

        return handoff_tool
