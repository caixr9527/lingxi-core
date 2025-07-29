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
@Time   : 2025/7/28 18:58
@Author : caixiaorong01@outlook.com
@File   : handoff_tool.py
"""
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from .base_agent import BaseAgent


class QuerySchema(BaseModel):
    task_description: str = Field(description="描述下一个代理应该做什么，包括所有相关的上下文。")


class HandoffTool(BaseTool):
    _agent: BaseAgent = PrivateAttr(None)

    def __init__(self, agent: BaseAgent, **kwargs: Any):
        super().__init__(
            name=agent.name,
            description=agent.description,
            args_schema=QuerySchema,
            **kwargs
        )
        self._agent = agent

    def _run(self, *args: Any, **kwargs: Any) -> str:
        task_description = kwargs.get("task_description", "")
        if not task_description:
            return "请输入正确的任务描述信息"
        agent_state = {
            "messages": [self._agent.llm.convert_to_human_message(task_description, [])],
            "history": [],
            "long_term_memory": "",
        }
        result = self._agent.invoke(input=agent_state)
        return result.answer
