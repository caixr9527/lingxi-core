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
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentState
from .function_call_agent import FunctionCallAgent


class SupervisorAgent(FunctionCallAgent):

    def _build_agent(self) -> CompiledStateGraph:
        graph = StateGraph(AgentState)
        graph.add_node(self.supervisor_agent, destinations=tuple(self.collaborative_agent.keys()) + (END,))

        for name in self.collaborative_agent.keys():
            agent = self.collaborative_agent[name]
            graph.add_node(agent)
            graph.add_edge(name, self.supervisor_agent.name)

        graph.add_edge(START, self.supervisor_agent.name)
        return graph.compile()
