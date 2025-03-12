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
@Time   : 2024/10/21 22:20
@Author : rxccai@gmail.com
@File   : file_extractor.py
"""
import os.path
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import requests
from injector import inject
from langchain_community.document_loaders import (
    UnstructuredExcelLoader,
    UnstructuredPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredCSVLoader,
    UnstructuredPowerPointLoader,
    UnstructuredXMLLoader,
    UnstructuredFileLoader,
    TextLoader,
)
from langchain_core.documents import Document as LCDocument

from internal.model import UploadFile
from internal.service import CosService


@inject
@dataclass
class FileExtractor:
    """文件提取提，用于将远程文件、upload_file记录加载成LangChain对应的文档或字符串"""
    cos_service: CosService

    def load(
            self,
            upload_file: UploadFile,
            return_text: bool = False,
            is_unstructured: bool = True,
    ) -> Union[list[LCDocument], str]:
        """加载传入的upload_file记录，返回LangChain文档列表或者字符串"""
        # 1.创建一个临时的文件夹
        with tempfile.TemporaryDirectory() as temp_dir:
            # 2.构建一个临时文件路径
            file_path = os.path.join(temp_dir, os.path.basename(upload_file.key))

            # 3.将对象存储中的文件下载到本地
            self.cos_service.download_file(upload_file.key, file_path)

            # 4.从指定的路径中去加载文件
            return self.load_from_file(file_path, return_text, is_unstructured)

    @classmethod
    def load_from_url(cls, url: str, return_text: bool = False) -> Union[list[LCDocument], str]:
        """从传入的URL中去加载数据，返回LangChain文档列表或者字符串"""
        # 1.下载远程URL的文件到本地
        response = requests.get(url)

        # 2.将文件下载到本地的临时文件夹
        with tempfile.TemporaryDirectory() as temp_dir:
            # 3.获取文件的扩展名，并构建临时存储路径，将远程文件存储到本地
            file_path = os.path.join(temp_dir, os.path.basename(url))
            with open(file_path, "wb") as file:
                file.write(response.content)

            return cls.load_from_file(file_path, return_text)

    @classmethod
    def load_from_file(
            cls,
            file_path: str,
            return_text: bool = False,
            is_unstructured: bool = True,
    ) -> Union[list[LCDocument], str]:
        """从本地文件中加载数据，返回LangChain文档列表或者字符串"""
        # 1.获取文件的扩展名
        delimiter = "\n\n"
        file_extension = Path(file_path).suffix.lower()

        # 2.根据不同的文件扩展名去加载不同的加载器
        if file_extension in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(file_path)
        elif file_extension == ".pdf":
            loader = UnstructuredPDFLoader(file_path)
        elif file_extension in [".md", ".markdown"]:
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_extension in [".htm", ".html"]:
            loader = UnstructuredHTMLLoader(file_path)
        elif file_extension == ".csv":
            loader = UnstructuredCSVLoader(file_path)
        elif file_extension in [".ppt", "pptx"]:
            loader = UnstructuredPowerPointLoader(file_path)
        elif file_extension == ".xml":
            loader = UnstructuredXMLLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path) if is_unstructured else TextLoader(file_path)

        # 3.返回加载的文档列表或者文本
        return delimiter.join([document.page_content for document in loader.load()]) if return_text else loader.load()
