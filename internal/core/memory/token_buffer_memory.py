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
@Time   : 2024/11/12 20:28
@Author : caixiaorong01@outlook.com
@File   : token_buffer_memory.py
"""
from dataclasses import dataclass

from langchain_core.messages import AnyMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.entity.conversation_entity import MessageStatus
from internal.model import Conversation, Message
from pkg.sqlalchemy import SQLAlchemy


@dataclass
class TokenBufferMemory:
    """缓存记忆组件"""

    conversation: Conversation
    db: SQLAlchemy
    model_instance: BaseLanguageModel

    def get_history_prompt_message(
            self,
            max_token_limit: int = 2000,
            message_limit: int = 10,
    ) -> list[AnyMessage]:
        """"获取指定会话模型的历史消息列表"""
        # 判断会话是否存在
        if self.conversation is None:
            return []
        messages = self.db.session.query(Message).filter(
            Message.conversation_id == self.conversation.id,
            Message.answer != "",
            Message.is_deleted == False,
            Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL, MessageStatus.TIMEOUT]),
        ).order_by(desc("created_at")).limit(message_limit).all()
        messages = list(reversed(messages))

        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                self.model_instance.convert_to_human_message(message.query, message.image_urls),
                AIMessage(content=message.answer),
            ])
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
            start_on="human",
            end_on="ai"
        )

    def get_history_prompt_text(
            self,
            human_prefix: str = "Human",
            ai_prefix: str = "AI",
            max_token_limit: int = 2000,
            message_limit: int = 10,
    ) -> str:
        messages = self.get_history_prompt_message(max_token_limit, message_limit)
        return get_buffer_string(messages, human_prefix, ai_prefix)
