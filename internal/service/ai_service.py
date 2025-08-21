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
@Time   : 2024/12/9 21:32
@Author : caixiaorong01@outlook.com
@File   : ai_service.py
"""
import json
from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.ai_entity import OPTIMIZE_PROMPT_TEMPLATE, SUPERVISOR_DEFAULT_PROMPT_TEMPLATE
from internal.exception import ForbiddenException
from internal.model import Account, Message, App, AppConfigVersion
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .conversation_service import ConversationService


@inject
@dataclass
class AIService(BaseService):
    db: SQLAlchemy
    conversation_service: ConversationService

    def auto_generate_prompt(self, app_id: UUID) -> str:
        app: App = self.get(App, app_id)
        config: AppConfigVersion = app.draft_app_config

        work_agents = []
        if config.agents:
            for id in config.agents:
                agent: App = self.get(App, id)
                work_agents.append(f"- {agent.name}: {agent.description}")

        prompt = SUPERVISOR_DEFAULT_PROMPT_TEMPLATE.format(agents="\n".join(work_agents))
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_PROMPT_TEMPLATE),
            ("human", "{prompt}")
        ])

        llm = ChatOpenAI(model="o4-mini", temperature=0.5)
        optimize_chain = prompt_template | llm | StrOutputParser()
        return optimize_chain.invoke({"prompt": prompt})
        # return prompt

    def generate_suggested_questions_from_message_id(self, message_id: UUID, account: Account) -> list[str]:
        message = self.get(Message, message_id)
        if not message or message.created_by != account.id:
            raise ForbiddenException("该消息不存在或无权限")

        histories = f"Human: {message.query}\nAI: {message.answer}"

        return self.conversation_service.generate_suggested_questions(histories)

    @classmethod
    def optimize_prompt(cls, prompt: str) -> Generator[str, None, None]:
        """根据传递的prompt进行优化生成"""
        # 构建优化prompt的提示词模板
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", OPTIMIZE_PROMPT_TEMPLATE),
            ("human", "{prompt}")
        ])

        # 构建LLM
        llm = ChatOpenAI(model="o4-mini", temperature=0.5)

        # 组装优化链
        optimize_chain = prompt_template | llm | StrOutputParser()

        # 调用链并流式事件返回
        for optimize_prompt in optimize_chain.stream({"prompt": prompt}):
            # 组装响应数据
            data = {"optimize_prompt": optimize_prompt}
            yield f"event: optimize_prompt\ndata: {json.dumps(data)}\n\n"
