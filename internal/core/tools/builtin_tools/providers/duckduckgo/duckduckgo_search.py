#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/20 22:32
@Author : rxccai@gmail.com
@File   : duckduckgo_search.py
"""
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool


class DDGInput(BaseModel):
    query: str = Field(description="需要搜索的查询语句")


def duckduckgo_search(**kwargs) -> BaseTool:
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索工具，当你需要瘦瘦时事时可以使用该工具",
        args_schema=DDGInput
    )
