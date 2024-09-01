#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/1 10:58
@Author : rxccai@gmail.com
@File   : 01. 大模型的函数回调与规范化输出.py
"""
from typing import Literal

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI


class RouteQuery(BaseModel):
    """将用户查询映射到最相关的数据源"""
    datasource: Literal["python_docs", "js_docs", "golang_docs"] = Field(
        description="根据给定用户问题，选择哪个数据源最相关以回答他们的问题"
    )


llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
structured_llm = llm.with_structured_output(RouteQuery)
