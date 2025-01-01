#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/10 20:33
@Author : rxccai@gmail.com
@File   : conversation_service.py
"""
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from flask import Flask
from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.conversation_entity import (
    InvokeFrom,
)
from internal.entity.conversation_entity import (
    SUMMARIZER_TEMPLATE,
    CONVERSATION_NAME_TEMPLATE,
    ConversationInfo,
    SUGGESTED_QUESTIONS_TEMPLATE,
    SuggestedQuestions
)
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.agent.entities.queue_entity import AgentThought
from ..core.agent.entities.queue_entity import QueueEvent
from ..model import Conversation
from ..model import Message, MessageAgentThought


@inject
@dataclass
class ConversationService(BaseService):
    db: SQLAlchemy

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
            logging.exception(f"提取会话名称出错, conversation_info: {conversation_info}, 错误信息: {str(e)}")

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
            logging.exception(f"生成建议问题出错, suggested_questions: {suggested_questions}, 错误信息: {str(e)}")

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
                        answer=agent_thought.answer,
                        latency=agent_thought.latency,
                    )

                if agent_thought.event == QueueEvent.AGENT_MESSAGE:
                    self.update(
                        message,
                        message=agent_thought.message,
                        answer=agent_thought.answer,
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
