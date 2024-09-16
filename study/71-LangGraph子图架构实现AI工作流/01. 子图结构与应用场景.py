#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/16 21:22
@Author : rxccai@gmail.com
@File   : 01. 子图结构与应用场景.py
"""
from typing import TypedDict, Any, Annotated

import dotenv
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

dotenv.load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")


google_serper = GoogleSerperRun(
    api_wrapper=GoogleSerperAPIWrapper(),
    args_schema=GoogleSerperArgsSchema,
)


def reduce_str(left: str | None, right: str | None) -> str:
    if right is not None and right != "":
        return right
    return left


class AgentState(TypedDict):
    query: Annotated[str, reduce_str]  # 原始问题
    live_content: Annotated[str, reduce_str]  # 直播文案
    xhs_content: Annotated[str, reduce_str]  # 小红书文案


class LiveAgentState(AgentState, MessagesState):
    """直播文案智能体状态"""
    pass


class XHSAgentState(AgentState):
    """小红书文案智能体状态"""
    pass


def chatbot_live(state: LiveAgentState, config: RunnableConfig) -> Any:
    """直播文案智能体聊天机器人节点"""
    # 1.创建提示模板+链应用
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "你是一个拥有10年经验的直播文案专家，请根据用户提供的产品整理一篇直播带货脚本文案，如果在你的知识库内找不到关于该产品的信息，可以使用搜索工具。"
        ),
        ("human", "{query}"),
        ("placeholder", "{chat_history}")
    ])
    chain = prompt | llm.bind_tools([google_serper])

    # 2.调用链并生成ai消息
    ai_message = chain.invoke({"query": state["query"], "chat_history": state["messages"]})

    return {
        "messages": [ai_message],
        "live_content": ai_message.content,
    }


# 1.创建子图1并添加节点、添加边
live_agent_graph = StateGraph(LiveAgentState)

live_agent_graph.add_node("chatbot_live", chatbot_live)
live_agent_graph.add_node("tools", ToolNode([google_serper]))

live_agent_graph.set_entry_point("chatbot_live")
live_agent_graph.add_conditional_edges("chatbot_live", tools_condition)
live_agent_graph.add_edge("tools", "chatbot_live")


def chatbot_xhs(state: XHSAgentState, config: RunnableConfig) -> Any:
    """小红书文案智能体聊天节点"""
    # 1.创建提示模板+链
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个小红书文案大师，请根据用户传递的商品名，生成一篇关于该商品的小红书笔记文案，注意风格活泼，多使用emoji表情。"),
        ("human", "{query}"),
    ])
    chain = prompt | llm | StrOutputParser()

    # 2.调用链并生成内容更新状态
    return {"xhs_content": chain.invoke({"query": state["query"]})}


# 2.创建子图2并添加节点、添加边
xhs_agent_graph = StateGraph(XHSAgentState)

xhs_agent_graph.add_node("chatbot_xhs", chatbot_xhs)

xhs_agent_graph.set_entry_point("chatbot_xhs")
xhs_agent_graph.set_finish_point("chatbot_xhs")


# 3.创建入口图并添加节点、边
def parallel_node(state: AgentState, config: RunnableConfig) -> Any:
    return state


agent_graph = StateGraph(AgentState)
agent_graph.add_node("parallel_node", parallel_node)
agent_graph.add_node("live_agent", live_agent_graph.compile())
agent_graph.add_node("xhs_agent", xhs_agent_graph.compile())

agent_graph.set_entry_point("parallel_node")
agent_graph.add_edge("parallel_node", "live_agent")
agent_graph.add_edge("parallel_node", "xhs_agent")

agent_graph.set_finish_point("live_agent")
agent_graph.set_finish_point("xhs_agent")

# 4.编译入口图
agent = agent_graph.compile()

# 5.执行入口图并打印结果
print(agent.invoke({"query": "潮汕牛肉丸"}))
