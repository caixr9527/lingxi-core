#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/15 20:24
@Author : rxccai@gmail.com
@File   : 01. 更新删除与归纳函数.py
"""
from typing import Any

import dotenv
from langchain_core.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph

dotenv.load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


def chatbot(state: MessagesState, config: RunnableConfig) -> Any:
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}


def delete_human_message(state: MessagesState, config: RunnableConfig) -> Any:
    """删除人类消息节点"""
    human_message = state["messages"][0]
    return {"messages": [RemoveMessage(id=human_message.id)]}


# 1.创建图构建器
graph_builder = StateGraph(MessagesState)

# 2.添加节点
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("delete_human_message", delete_human_message)

# 3.添加边
graph_builder.set_entry_point("chatbot")
graph_builder.add_edge("chatbot", "delete_human_message")
graph_builder.set_finish_point("delete_human_message")

# 4.编译图
graph = graph_builder.compile()

# 5.调用图应用程序
print(graph.invoke({"messages": [("human", "你好，你是")]}))
