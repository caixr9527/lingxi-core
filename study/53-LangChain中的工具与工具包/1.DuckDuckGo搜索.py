#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/5 23:03
@Author : rxccai@gmail.com
@File   : 1.DuckDuckGo搜索.py
"""
from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()

print("工具名字: ", search.name)
print("工具描述: ", search.description)
print("工具参数:", search.args)
print("是否直接返回: ", search.return_direct)
print(search.run("LangChain目前最新版本是什么?"))
