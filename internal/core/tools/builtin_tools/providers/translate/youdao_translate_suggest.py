#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/6/28 16:14
@Author : caixiaorong01@outlook.com
@File   : youdao_translate_suggest.py
"""
from typing import Type, Any

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class YouDaoSuggestArgsSchema(BaseModel):
    q: str = Field(description="要检索查询的单词，例如love/computer")


class YouDaoSuggestTool(BaseTool):
    name: str = "youdao_suggest"
    description: str = "根据传递的单词查询其字典信息"
    args_schema: Type[BaseModel] = YouDaoSuggestArgsSchema
    url: str

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        try:
            q = kwargs.get("q", "")
            if q == "":
                return "输入不能为空"
            headers = {
                'Content-Type': 'application/json'
            }
            if self.url.strip() == "":
                return "接口地址配置错误"
            query = f"{self.url}?q={q}&doctype=json"
            response = requests.get(query, headers=headers)
            if response.status_code != 200:
                return f"{q} 请求结果异常: {response.status_code}"
            json_response = response.json()
            if json_response["result"]["code"] != 200 or not json_response["data"]:
                return f"请求失败，原因是: {json_response["result"]["msg"]}"

            return json_response["data"]["entries"]
        except Exception as e:
            return f"获取{kwargs.get("q", "")} 信息失败"


@add_attribute("args_schema", YouDaoSuggestArgsSchema)
def youdao_translate_suggest(**kwargs) -> BaseTool:
    return YouDaoSuggestTool(**kwargs)
