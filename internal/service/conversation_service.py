#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/11/10 20:33
@Author : rxccai@gmail.com
@File   : conversation_service.py
"""
from dataclasses import dataclass

from injector import inject
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from internal.entity.conversation_entity import SUMMARIZER_TEMPLATE
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
