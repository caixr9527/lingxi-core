#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/10 20:33
@Author : rxccai@gmail.com
@File   : conversation_service.py
"""
import logging
from dataclasses import dataclass

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.conversation_entity import SUMMARIZER_TEMPLATE, CONVERSATION_NAME_TEMPLATE, ConversationInfo
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


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
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

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
