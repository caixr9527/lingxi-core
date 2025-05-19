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
@Time   : 2025/5/18 14:13
@Author : caixiaorong01@outlook.com
@File   : content_extract.py
"""
from typing import Type, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from internal.lib.helper import add_attribute, get_file_extension


class ContentExtractArgsSchema(BaseModel):
    url: str = Field(description="文档/文件/图片的链接地址")


class ContentExtractTool(BaseTool):
    name = "content_extract"
    description = "当需要提取各类文档/文件/图片内容时，可以使用该工具"
    args_schema: Type[BaseModel] = ContentExtractArgsSchema

    file_ext = ["xlsx", "xls", "pdf", "md", "markdown", "htm", "html", "csv", "ppt", "pptx", "xml",
                "txt"]
    img_ext = ["jpg", "jpeg", "png", "svg", "gif", "webp", "bmp", "ico"]
    prompt_template = """
    你是一位专业的图片文本内容提取大师，能够准确、高效地从图片中提取完整的文本内容信息。
    可以根据用户提供的图片，精准提取图片所包含的信息，仅输出图片中的文本内容，不添加多余的描述与修饰，图片文本内容是什么就输出什么。
    如果图片中无文本文字信息，则如实告诉用户图片文本内容为空，不对图片进行过多的修饰。
    """

    def _run(self, *args: Any, **kwargs: Any) -> str:
        try:
            url = kwargs.get("url", "")
            ext = get_file_extension(url).lower()

            if ext in self.file_ext:
                from internal.core.file_extractor import FileExtractor
                from app.http.module import injector
                file_extractor = injector.get(FileExtractor)
                return file_extractor.load_from_url(url, return_text=True)
            elif ext in self.img_ext:
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=self.prompt_template),
                    HumanMessage(content=[
                        {"type": "text", "text": "请准确的提取图片链接里面的内容"},
                        {"type": "image_url", "image_url": {"url": url}},
                    ])
                ])
                llm = ChatOpenAI(
                    model="gpt-4o",
                    temperature=0,
                    max_tokens=16384,
                )
                chain = prompt | llm | StrOutputParser()
                return chain.invoke({})
            else:
                return f"文档格式：{ext} 不支持内容提取"
        except Exception as e:
            return f"获取 {kwargs.get("url", "")} 内容失败"


@add_attribute("args_schema", ContentExtractArgsSchema)
def content_extract(**kwargs) -> BaseTool:
    return ContentExtractTool()
