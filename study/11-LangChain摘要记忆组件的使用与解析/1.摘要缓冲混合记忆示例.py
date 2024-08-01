#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/7/28 22:32
@Author : rxccai@gmail.com
@File   : 1.缓冲窗口记忆示例.py
"""
from operator import itemgetter

import dotenv
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是OpenAI开发的聊天机器人，请根据对呀的上下文回复用户问题"),
    MessagesPlaceholder("history"),
    ("human", "{query}")
])
memory = ConversationSummaryBufferMemory(
    max_token_limit=300,
    return_message=True,
    input_key="query",
    llm=ChatOpenAI(model="moonshot-v1-8k")
)

llm = ChatOpenAI(model="moonshot-v1-8k")

chain = RunnablePassthrough.assign(
    history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
) | prompt | llm | StrOutputParser()

while True:
    query = input("Human: ")
    if query == "q":
        exit(0)
    chain_input = {"query": query, "language": "中文"}
    response = chain.stream(chain_input)
    print("AI: ", flush=True, end="")
    output = ""
    for chunk in response:
        output += chunk
        print(chunk, flush=True, end="")
    memory.save_context(chain_input, {"output": output})
    print("")
    print("history: ", memory.load_memory_variables({}))
