#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/7 22:19
@Author : rxccai@gmail.com
@File   : 01. 结构化输出.py
"""
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class QAExtra(BaseModel):
    """一个问答键值对工具，传递对应的假设性问题+答案"""
    question: str = Field(description="假设性问题")
    answer: str = Field(description="假设性问题对应的答案")


llm = ChatOpenAI(model="gpt-3.5-turbo-16k")
structured_llm = llm.with_structured_output(QAExtra)

prompt = ChatPromptTemplate.from_messages([
    ("system", "请从用户传递的query中提取出假设性的问题+答案。"),
    ("human", "{query}")
])

chain = {"query": RunnablePassthrough()} | prompt | structured_llm

print(chain.invoke("我叫慕小课，我喜欢打篮球，游泳"))
