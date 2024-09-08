#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/8 10:17
@Author : rxccai@gmail.com
@File   : 01.捕获工具错误.py
"""
import dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


@tool
def complex_tool(int_arg: int, float_arg: float, dict_arg: dict) -> int:
    """使用复杂工具进行复杂计算操作"""
    return int_arg * float_arg


# 1.创建大语言模型并绑定工具
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
llm_with_tools = llm.bind_tools([complex_tool])

# 2.创建链并执行工具
chain = llm_with_tools | (lambda msg: msg.tool_calls[0]["args"]) | complex_tool

# 3.调用链
print(chain.invoke("使用复杂工具，对应参数为5和2.1"))
