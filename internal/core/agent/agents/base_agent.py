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
@Time   : 2024/11/12 21:18
@Author : caixiaorong01@outlook.com
@File   : base_agent.py
"""
import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Any, Iterator

from langchain_core.load import Serializable
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from pydantic import PrivateAttr

from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import AgentResult, AgentThought, QueueEvent
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.exception import FailException
from .agent_queue_manager import AgentQueueManager


class BaseAgent(Serializable, Runnable):
    name: Optional[str] = None
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
        # 调用stream方法获取流式事件输出数据
        content = input["messages"][0].content
        query = ""
        image_urls = []
        if isinstance(content, str):
            query = content
        elif isinstance(content, list):
            query = content[0]["text"]
            image_urls = [chunk["image_url"]["url"] for chunk in content if chunk.get("type") == "image_url"]
        agent_result = AgentResult(query=query, image_urls=image_urls)
        agent_thoughts = {}
        for agent_thought in self.stream(input, config):
            # 提取事件id并转换成字符串
            event_id = str(agent_thought.id)

            # 除了ping事件，其他事件全部记录
            if agent_thought.event != QueueEvent.PING:
                # 单独处理agent_message事件，因为该事件为数据叠加
                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    # 检测是否已存储了事件
                    if event_id not in agent_thoughts:
                        # 初始化智能体消息事件
                        agent_thoughts[event_id] = agent_thought
                    else:
                        # 叠加智能体消息事件
                        agent_thoughts[event_id] = agent_thoughts[event_id].model_copy(update={
                            "thought": agent_thoughts[event_id].thought + agent_thought.thought,
                            "answer": agent_thoughts[event_id].answer + agent_thought.answer,
                            "latency": agent_thought.latency,
                        })
                    # 更新智能体消息答案
                    agent_result.answer += agent_thought.answer
                else:
                    # 处理其他类型的智能体事件，类型均为覆盖
                    agent_thoughts[event_id] = agent_thought

                    # 单独判断是否为异常消息类型，如果是则修改状态并记录错误
                    if agent_thought.event in [QueueEvent.STOP, QueueEvent.TIMEOUT, QueueEvent.ERROR]:
                        agent_result.status = agent_thought.event
                        agent_result.error = agent_thought.observation if agent_thought.event == QueueEvent.ERROR else ""

        # 将推理字典转换成列表并存储
        agent_result.agent_thoughts = [agent_thought for agent_thought in agent_thoughts.values()]

        # 完善message
        agent_result.message = next(
            (agent_thought.message for agent_thought in agent_thoughts.values()
             if agent_thought.event == QueueEvent.AGENT_MESSAGE),
            []
        )

        # 更新总耗时
        agent_result.latency = sum([agent_thought.latency for agent_thought in agent_thoughts.values()])

        return agent_result

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
