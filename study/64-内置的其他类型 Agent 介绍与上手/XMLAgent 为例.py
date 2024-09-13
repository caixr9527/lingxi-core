#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/13 23:18
@Author : rxccai@gmail.com
@File   : XMLAgent 为例.py
"""
from langchain.agents import create_xml_agent, AgentExecutor, tools
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 创建XMLAgent提示模板
prompt = ChatPromptTemplate.from_messages([
    ("human", """You are a helpful assistant. Help the user answer any questions.

You have access to the following tools:

{tools}

In order to use a tool, you can use <tool></tool> and <tool_input></tool_input> tags. You will then get back a response in the form <observation></observation>
For example, if you have a tool called 'search' that could run a google search, in order to search for the weather in SF you would respond:

<tool>search</tool><tool_input>weather in SF</tool_input>
<observation>64 degrees</observation>

When you are done, respond with a final answer between <final_answer></final_answer>. For example:

<final_answer>The weather in SF is 64 degrees</final_answer>

Begin!

Previous Conversation:
{chat_history}

Question: {input}
{agent_scratchpad}"""),
])

# 创建大语言模型
llm = ChatOpenAI(model="gpt-4o-mini")

# 创建agent与agent执行者
agent = create_xml_agent(
    prompt=prompt,
    llm=llm,
    tools=tools,
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(agent_executor.invoke({"input": "马拉松的世界记录是多少？", "chat_history": ""}))
