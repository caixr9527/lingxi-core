#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/11 23:12
@Author : rxccai@gmail.com
@File   : 01. 工具调用智能体.py
"""
import dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools import GoogleSerperRun
from langchain_community.tools.openai_dalle_image_generation import OpenAIDALLEImageGenerationTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")


class DallEArgsSchema(BaseModel):
    query: str = Field(description="输入应该是生成图像的文本提示(prompt)")


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
dalle = OpenAIDALLEImageGenerationTool(
    name="openai_dalle",
    api_wrapper=DallEAPIWrapper(model="dall-e-3"),
    args_schema=DallEArgsSchema,
)
tools = [google_serper, dalle]

# 2.定义工具调用agent提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 2.创建大语言模型
llm = ChatOpenAI(model="gpt-4o-mini")

# 3.创建agent与agent执行者
agent = create_tool_calling_agent(
    prompt=prompt,
    llm=llm,
    tools=tools,
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(agent_executor.invoke({"input": "请帮我绘制一张老爷爷爬山的图片"}))
