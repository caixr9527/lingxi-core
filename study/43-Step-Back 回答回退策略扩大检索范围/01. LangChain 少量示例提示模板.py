#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/31 19:46
@Author : rxccai@gmail.com
@File   : 01. LangChain 少量示例提示模板.py
"""
import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

# 1.构建示例模板与示例
examples = [
    {"question": "帮我计算下2+2等于多少？", "answer": "4"},
    {"question": "帮我计算下2+3等于多少？", "answer": "5"},
    {"question": "帮我计算下20*15等于多少？", "answer": "300"},
]
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{question}"),
    ("ai", "{answer}"),
])

# 2.构建少量示例提示模板
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)
print("少量示例模板:", few_shot_prompt.format())

# 3.构建最终提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个可以计算复杂数学问题的聊天机器人"),
    few_shot_prompt,
    ("human", "{question}"),
])

# 4.创建大语言模型与链
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
chain = prompt | llm | StrOutputParser()

# 5.调用链获取结果
print(chain.invoke("帮我计算下14*15等于多少"))
