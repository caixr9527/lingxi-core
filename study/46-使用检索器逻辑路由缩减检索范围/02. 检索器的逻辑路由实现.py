#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/1 11:11
@Author : rxccai@gmail.com
@File   : 02. 检索器的逻辑路由实现.py
"""
from typing import Literal

import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()


class RouteQuery(BaseModel):
    """将用户查询映射到最相关的数据源"""
    datasource: Literal["python_docs", "js_docs", "golang_docs"] = Field(
        description="根据给定用户问题，选择哪个数据源最相关以回答他们的问题"
    )


def choose_route(result: RouteQuery):
    if "python_docs" in result.datasource.lower():
        return "chain for python_docs"
    elif "js_docs" in result.datasource.lower():
        return "chain for js_docs"
    else:
        return "golang_docs"


# 1.构建大语言模型并进行结构化输出
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
structured_llm = llm.with_structured_output(RouteQuery)

# 2.创建路由逻辑链
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个擅长将用户问题路由到适当的数据源的专家。\n请根据问题涉及的编程语言，将其路由到相关数据源"),
    ("human", "{question}")
])
router = {"question": RunnablePassthrough()} | prompt | structured_llm | choose_route

# 3.执行相应的提问，检查映射的路由
question = """为什么下面的代码不工作了，请帮我检查下：

from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(["human", "speak in {language}"])
prompt.invoke("中文")"""

# 4.选择不同的数据库
print(router.invoke(question))
