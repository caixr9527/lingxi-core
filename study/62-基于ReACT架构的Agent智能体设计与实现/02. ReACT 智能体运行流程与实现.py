#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/9 23:12
@Author : rxccai@gmail.com
@File   : 02. ReACT 智能体运行流程与实现.py
"""
import dotenv
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import render_text_description_and_args
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")


# 1.定义工具与工具列表
google_serper = GoogleSerperRun(
    name="google_serper",
    description=(
        "一个低成本的谷歌搜索API。"
        "当你需要回答有关时事的问题时，可以调用该工具。"
        "该工具的输入是搜索查询语句。"
    ),
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)
tools = [google_serper]

# 2.定义智能体提示模板
prompt = hub.pull("hwchase17/react")

# 3.创建大语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo-16k")
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
    tools_renderer=render_text_description_and_args,
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(agent_executor.invoke({"input": "马拉松的最新世界记录是多少?"}))
