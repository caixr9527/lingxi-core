#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/12 20:28
@Author : rxccai@gmail.com
@File   : token_buffer_memory.py
"""
from dataclasses import dataclass

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, trim_messages, get_buffer_string
from sqlalchemy import desc

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
            Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL]),
        ).order_by(desc("created_at")).limit(message_limit).all()
        messages = list(reversed(messages))

        prompt_messages = []
        for message in messages:
            prompt_messages.extend([
                HumanMessage(content=message.query),
                AIMessage(content=message.answer)
            ])
        return trim_messages(
            messages=prompt_messages,
            max_tokens=max_token_limit,
            token_counter=self.model_instance,
            strategy="last",
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
