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
@Time   : 2024/9/19 22:50
@Author : caixiaorong01@outlook.com
@File   : helper.py
"""
import base64
import importlib
import os
import random
import string
from datetime import datetime
from enum import Enum
from hashlib import sha3_256
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from langchain_core.documents import Document
from langchain_core.pydantic_v1 import BaseModel

IMAGE_EXT = ["jpg", "jpeg", "png", "svg", "gif", "webp", "bmp", "ico"]
FILE_EXT = ["xlsx", "xls", "pdf", "md", "markdown", "htm", "html", "csv", "ppt", "pptx", "xml",
            "txt"]


def dynamic_import(module_name: str, symbol_name: str) -> Any:
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def add_attribute(attr_name: str, attr_value: Any):
    def decorator(func):
        setattr(func, attr_name, attr_value)
        return func

    return decorator


def generate_text_hash(text: str) -> str:
    text = str(text) + "None"
    return sha3_256(text.encode()).hexdigest()


def datetime_to_timestamp(dt: datetime) -> int:
    if dt is None:
        return 0
    return int(dt.timestamp())


def combine_documents(documents: list[Document]) -> str:
    """将对应的文档列表使用换行符合并"""
    doc = "\n\n".join([document.page_content for document in documents])
    return doc


def remove_fields(data_dict: dict, fields: list[str]) -> None:
    """根据传递的字段名移除字典中指定的字段"""
    for field in fields:
        data_dict.pop(field, None)


def convert_model_to_dict(obj: Any, *args, **kwargs):
    """辅助函数，将Pydantic V1版本中的UUID/Enum等数据转换成可序列化存储的数据。"""
    # 1.如果是Pydantic的BaseModel类型，递归处理其字段
    if isinstance(obj, BaseModel):
        obj_dict = obj.dict(*args, **kwargs)
        # 2.递归处理嵌套字段
        for key, value in obj_dict.items():
            obj_dict[key] = convert_model_to_dict(value, *args, **kwargs)
        return obj_dict

    # 3.如果是 UUID 类型，转换为字符串
    elif isinstance(obj, UUID):
        return str(obj)

    # 4.如果是 Enum 类型，转换为其值
    elif isinstance(obj, Enum):
        return obj.value

    # 5.如果是列表类型，递归处理列表中的每个元素
    elif isinstance(obj, list):
        return [convert_model_to_dict(item, *args, **kwargs) for item in obj]

    # 6.如果是字典类型，递归处理字典中的每个字段
    elif isinstance(obj, dict):
        return {key: convert_model_to_dict(value, *args, **kwargs) for key, value in obj.items()}

    # 7.对其他类型的字段，保持原样
    return obj


def get_value_type(value: Any) -> Any:
    """根据传递的值获取变量的类型，并将str和bool转换成string和boolean"""
    # 计算变量的类型并转换成字符串
    value_type = type(value).__name__

    # 判断是否为str或者是bool
    if value_type == "str":
        return "string"
    elif value_type == "bool":
        return "boolean"

    return value_type


def generate_random_string(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits
    random_str = ''.join(random.choices(chars, k=length))
    return random_str


def decode_password(password: str) -> str:
    with open("private.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=os.getenv('PRIVATE_KEY_PASSWORD').encode(),
            backend=default_backend()
        )
    encrypted_bytes = base64.b64decode(password)
    decrypted_bytes = private_key.decrypt(
        encrypted_bytes,
        padding.PKCS1v15()
    )
    password = decrypted_bytes.decode('utf-8')
    return password


def get_file_extension(url) -> str:
    # 解析URL的路径部分
    path = urlparse(url).path
    # 提取文件名
    filename = os.path.basename(path)
    # 若无文件名或文件名无扩展名，返回空字符串
    if not filename or '.' not in filename:
        return ''
    # 分割扩展名并去除点号
    return os.path.splitext(filename)[1].lstrip('.')
