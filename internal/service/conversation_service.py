#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/10 20:33
@Author : rxccai@gmail.com
@File   : conversation_service.py
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from flask import Flask
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from internal.core.agent.entities.queue_entity import AgentThought
from internal.core.agent.entities.queue_entity import QueueEvent
from internal.entity.conversation_entity import (
    InvokeFrom, MessageStatus,
)
from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
    SUGGESTED_QUESTIONS_TEMPLATE,
    SuggestedQuestions
)
from internal.exception import NotFoundException
from internal.model import Conversation, Account
from internal.model import Message, MessageAgentThought
from internal.schema.conversation_schema import GetConversationMessagesWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class ConversationService(BaseService):
    db: SQLAlchemy

    def get_conversation(self, conversation_id: UUID, account: Account) -> Conversation:
        """根据传递的会话id+account，获取指定的会话信息"""
        conversation = self.get(Conversation, conversation_id)
        if (
                not conversation
                or conversation.created_by != account.id
                or conversation.is_deleted
        ):
            raise NotFoundException("该会话不存在或被删除，请核实后重试")

        return conversation

    def get_message(self, message_id: UUID, account: Account) -> Message:
        """根据传递的消息id+账号，获取指定的消息"""
        message = self.get(Message, message_id)
        if (
                not message
                or message.created_by != account.id
                or message.is_deleted
        ):
            raise NotFoundException("该消息不存在或被删除，请核实后重试")

        return message

    def get_conversation_messages_with_page(
            self,
            conversation_id: UUID,
            req: GetConversationMessagesWithPageReq,
            account: Account,
    ) -> tuple[list[Message], Paginator]:
        """根据传递的会话id+请求数据，获取当前账号下该会话的消息分页列表数据"""
        conversation = self.get_conversation(conversation_id, account)

        paginator = Paginator(db=self.db, req=req)
        filters = []
        if req.created_at.data:
            created_at_datetime = datetime.fromtimestamp(req.created_at.data)
            filters.append(Message.created_at <= created_at_datetime)

        messages = paginator.paginate(
            self.db.session.query(Message).options(joinedload(Message.agent_thoughts)).filter(
                Message.conversation_id == conversation.id,
                Message.status.in_([MessageStatus.STOP, MessageStatus.NORMAL]),
                Message.answer != "",
                ~Message.is_deleted,
                *filters,
            ).order_by(desc("created_at"))
        )

        return messages, paginator

    def delete_conversation(self, conversation_id: UUID, account: Account) -> Conversation:
        """根据传递的会话id+账号删除指定的会话记录"""
        conversation = self.get_conversation(conversation_id, account)

        self.update(conversation, is_deleted=True)

        return conversation

    def delete_message(self, conversation_id: UUID, message_id: UUID, account: Account) -> Message:
        """根据传递的会话id+消息id删除指定的消息记录"""
        conversation = self.get_conversation(conversation_id, account)

        message = self.get_message(message_id, account)

        if conversation.id != message.conversation_id:
            raise NotFoundException("该会话下不存在该消息，请核实后重试")

        self.update(message, is_deleted=True)

        return message

    def update_conversation(self, conversation_id: UUID, account: Account, **kwargs) -> Conversation:
        """根据传递的会话id+账号+kwargs更新会话信息"""
        conversation = self.get_conversation(conversation_id, account)

        self.update(conversation, **kwargs)

        return conversation

    @classmethod
    def summary(cls, human_message: str, ai_message: str, old_summary: str = "") -> str:
        """总结生成新摘要"""
        prompt = ChatPromptTemplate.from_template(SUMMARIZER_TEMPLATE)
        # 构建llm设置温度降低幻觉概率
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
        summary_chain = prompt | llm | StrOutputParser()
        new_summary = summary_chain.invoke({
            "summary": old_summary,
            "new_lines": f"Human: {human_message}\nAI: {ai_message}",
        })

        return new_summary

    @classmethod
    def generate_conversation_name(cls, query: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", CONVERSATION_NAME_TEMPLATE),
            ("human", "{query}")
        ])
        # 构建llm设置温度降低幻觉概率
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        structured_llm = llm.with_structured_output(ConversationInfo)

        chain = prompt | structured_llm
        if len(query) > 2000:
            query = query[:300] + "...[TRUNCATED]..." + query[-300:]
        query = query.replace("\n", " ")

        conversation_info = chain.invoke({"query": query})
        name = "新的会话"
        try:
            if conversation_info and hasattr(conversation_info, "subject"):
                name = conversation_info.subject
        except Exception as e:
            logging.exception("提取会话名称出错, conversation_info: %(conversation_info)s, 错误信息: %(error)s",
                              {"conversation_info": conversation_info, "error": e})

        if len(name) > 75:
            name = name[:75] + "..."

        return name

    @classmethod
    def generate_suggested_questions(cls, histories: str) -> list[str]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUGGESTED_QUESTIONS_TEMPLATE),
            ("human", "{histories}")
        ])
        # 构建llm设置温度降低幻觉概率
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        structured_llm = llm.with_structured_output(SuggestedQuestions)

        chain = prompt | structured_llm

        suggested_questions = chain.invoke({"histories": histories})
        questions = []
        try:
            if suggested_questions and hasattr(suggested_questions, "questions"):
                questions = suggested_questions.questions
        except Exception as e:
            logging.exception("生成建议问题出错, suggested_questions: %(suggested_questions)s, 错误信息: %(e)s",
                              {"suggested_questions": suggested_questions, "error": e})

        if len(questions) > 3:
            questions = questions[:3]

        return questions

    def save_agent_thoughts(self,
                            flask_app: Flask,
                            account_id: UUID,
                            app_id: UUID,
                            app_config: dict[str, Any],
                            conversation_id: UUID,
                            message_id: UUID,
                            agent_thoughts: list[AgentThought],
                            ):
        with flask_app.app_context():
            position = 0
            latency = 0
            conversation = self.get(Conversation, conversation_id)
            message = self.get(Message, message_id)

            for agent_thought in agent_thoughts:
                if agent_thought.event in [
                    QueueEvent.LONG_TERM_MEMORY_RECALL,
                    QueueEvent.AGENT_THOUGHT,
                    QueueEvent.AGENT_MESSAGE,
                    QueueEvent.AGENT_ACTION,
                    QueueEvent.DATASET_RETRIEVAL,
                ]:
                    position += 1
                    latency += agent_thought.latency
                    self.create(
                        MessageAgentThought,
                        app_id=app_id,
                        conversation_id=conversation.id,
                        message_id=message.id,
                        invoke_from=InvokeFrom.DEBUGGER,
                        created_by=account_id,
                        position=position,
                        event=agent_thought.event,
                        thought=agent_thought.thought,
                        observation=agent_thought.observation,
                        tool=agent_thought.tool,
                        tool_input=agent_thought.tool_input,
                        message=agent_thought.message,
                        message_token_count=agent_thought.message_token_count,
                        message_unit_price=agent_thought.message_unit_price,
                        message_price_unit=agent_thought.message_price_unit,
                        answer=agent_thought.answer,
                        answer_token_count=agent_thought.answer_token_count,
                        answer_unit_price=agent_thought.answer_unit_price,
                        answer_price_unit=agent_thought.answer_price_unit,
                        total_token_count=agent_thought.total_token_count,
                        total_price=agent_thought.total_price,
                        latency=agent_thought.latency,
                    )

                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    self.update(
                        message,
                        message=agent_thought.message,
                        message_token_count=agent_thought.message_token_count,
                        message_unit_price=agent_thought.message_unit_price,
                        message_price_unit=agent_thought.message_price_unit,
                        answer=agent_thought.answer,
                        answer_token_count=agent_thought.answer_token_count,
                        answer_unit_price=agent_thought.answer_unit_price,
                        answer_price_unit=agent_thought.answer_price_unit,
                        total_token_count=agent_thought.total_token_count,
                        total_price=agent_thought.total_price,
                        latency=latency
                    )
                    if app_config["long_term_memory"]["enable"]:
                        new_summary = self.summary(
                            message.query,
                            agent_thought.answer,
                            conversation.summary
                        )

                        self.update(
                            conversation,
                            summary=new_summary,
                        )

                    if conversation.is_new:
                        new_conversation_name = self.generate_conversation_name(message.query)
                        self.update(
                            conversation,
                            name=new_conversation_name,
                        )

                if agent_thought.event in [QueueEvent.TIMEOUT, QueueEvent.STOP, QueueEvent.ERROR]:
                    self.update(
                        message,
                        status=agent_thought.event,
                        error=agent_thought.observation
                    )
                    break
