#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright [2025] [caixiaorong]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
@Time   : 2025/5/8 12:41
@Author : caixiaorong01@outlook.com
@File   : bocha_web_search.py
"""
import os
from typing import Any, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class BOChaWebSearchArgsSchema(BaseModel):
    query: str = Field(description="用户的搜索词")


class BOChaWebSearchTool(BaseTool):
    name: str = "bocha_web_search"
    description: str = "当需要搜索互联网上的内容时，可以使用该工具"
    args_schema: Type[BaseModel] = BOChaWebSearchArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        try:
            api_key = os.getenv("BOCHA_API_KEY")
            if not api_key:
                return f"博查开放平台API为配置"

            query = kwargs.get("query", "")
            freshness = kwargs.get("freshness", "noLimit")
            summary = kwargs.get("summary", True)
            count = kwargs.get("count", 10)
            page = kwargs.get("page", 1)

            url = 'https://api.bochaai.com/v1/web-search'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                "query": query,
                "freshness": freshness,
                "summary": summary,
                "count": count,
                page: page
            }
            response = requests.post(url, headers=headers, json=data)
            formatted_results = ""
            if response.status_code == 200:
                json_response = response.json()
                try:
                    if json_response["code"] != 200 or not json_response["data"]:
                        return f"搜索API请求失败，原因是: {json_response["msg"] or '未知错误'}"

                    webpages = json_response["data"]["webPages"]["value"]
                    if not webpages:
                        return "未找到相关结果。"
                    for idx, page in enumerate(webpages, start=1):
                        formatted_results += (
                            f"引用: {idx}\n"
                            f"标题: {page['name']}\n"
                            f"URL: {page['url']}\n"
                            f"摘要: {page['summary']}\n"
                            f"网站名称: {page['siteName']}\n"
                            f"网站图标: {page['siteIcon']}\n"
                            f"发布时间: {page['dateLastCrawled']}\n\n"
                        )
                    return formatted_results.strip()
                except Exception as e:
                    return f"搜索API请求失败，原因是：搜索结果解析失败 {str(e)}"
            else:
                return f"查询结果异常: {response.status_code}"
        except Exception as e:
            return f"获取 {kwargs.get("query", "")} 信息失败"


@add_attribute("args_schema", BOChaWebSearchArgsSchema)
def bocha_web_search(**kwargs) -> BaseTool:
    return BOChaWebSearchTool()
