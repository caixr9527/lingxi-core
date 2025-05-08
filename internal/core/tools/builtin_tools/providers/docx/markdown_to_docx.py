#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/5/8 21:05
@Author : caixiaorong01@outlook.com
@File   : markdown_to_docx.py
"""
import logging
import os
import tempfile
import uuid
from typing import Type, Any

import pypandoc
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class MarkdownToDOCXArgsSchema(BaseModel):
    markdown: str = Field(description="要生成Word内容的markdown文档字符串。")


class MarkdownToDOCXTool(BaseTool):
    name = "markdown_to_docx"
    description = "这是一个可以将markdown文本转换成Word文档的工具，传递的参数是markdown对应的文本字符串，返回的数据是PPT的下载地址。"
    args_schema: Type[BaseModel] = MarkdownToDOCXArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                filename = str(uuid.uuid4()) + ".docx"
                filepath = os.path.join(temp_dir, filename)
                pypandoc.convert_text(
                    kwargs.get("markdown"),
                    'docx',
                    format='markdown',
                    outputfile=filepath
                )

                from internal.service import CosService
                from app.http.module import injector
                cos_service = injector.get(CosService)
                client = cos_service.get_client()
                bucket = cos_service.get_bucket()
                key = f"builtin-tools/markdown-to-docx/{filename}"
                client.upload_file(
                    Bucket=bucket,
                    Key=key,
                    LocalFilePath=filepath,
                    EnableMD5=False,
                    progress_callback=None,
                )

                # 返回对应的地址
                return cos_service.get_file_url(key)
        except Exception as e:
            logging.error("markdown_to_docx出错: %(error)s", {"error": e}, exc_info=True)
            return f"生成Word文档失败，错误原因: {str(e)}"


@add_attribute("args_schema", MarkdownToDOCXArgsSchema)
def markdown_to_docx(**kwargs) -> BaseTool:
    return MarkdownToDOCXTool()
