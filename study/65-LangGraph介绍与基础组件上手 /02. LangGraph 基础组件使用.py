#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/15 14:25
@Author : rxccai@gmail.com
@File   : 02. LangGraph 基础组件使用.py
"""
from typing import TypedDict, Annotated

import dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

dotenv.load_dotenv()


class GraphState(TypedDict):
    """图状态数据结构，类型为字典"""
    messages: Annotated[list, add_messages]  # 设置消息列表，并添加归纳函数
    node_name: str


llm = ChatOpenAI(model="gpt-4o-mini")


def chatbot(state: GraphState) -> GraphState:
    """聊天机器人函数"""
    # 1.获取状态里存储的消息列表数据并传递给LLM
    ai_message = llm.invoke(state["messages"])
    # 2.返回更新/生成的状态
    return {"messages": [ai_message], "node_name": "chatbot"}


# 1.创建状态图，并使用GraphState作为状态数据
graph_builder = StateGraph(GraphState)

# 2.添加节点
graph_builder.add_node("llm", chatbot)

# 3.添加边
graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)

# 4.编译图为Runnable可运行组件
graph = graph_builder.compile()

# 5.调用图架构应用
print(graph.invoke({"messages": [("human", "你好，你是？")], "node_name": "graph"}))
