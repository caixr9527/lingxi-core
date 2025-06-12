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
@Time   : 2025/5/8 14:41
@Author : caixiaorong01@outlook.com
@File   : web_content_extract.py
"""
from typing import Type, Any

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class WebContentExtractArgsSchema(BaseModel):
    url: str = Field(description="网页url链接,例如：https://www.baidu.com/")


class WebContentExtractTool(BaseTool):
    name = "web_content_extract"
    description = "当用户的输入内容包含有网页URL链接且需要根据网页URL链接提取内容时，可以使用该工具"
    args_schema: Type[BaseModel] = WebContentExtractArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        try:
            url = kwargs.get("url", "")
            loader = WebBaseLoader(web_paths=[url])
            result = ""
            for doc in loader.load():
                result += doc.page_content + "\n"

            return result
        except Exception as e:
            return f"获取 {kwargs.get("url", "")} 网页内容失败"


@add_attribute("args_schema", WebContentExtractArgsSchema)
def web_content_extract(**kwargs) -> BaseTool:
    return WebContentExtractTool()
