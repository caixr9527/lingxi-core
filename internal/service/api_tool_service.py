#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/24 23:35
@Author : rxccai@gmail.com
@File   : api_tool_service.py
"""
import json
from dataclasses import dataclass

from injector import inject

from internal.core.tools.api_tools.entites import OpenAPISchema
from internal.exception import ValidateException


@inject
@dataclass
class ApiToolService:
    """自定义api插件服务"""

    @classmethod
    def parse_openapi_schema(cls, openapi_schema_str: str) -> OpenAPISchema:
        try:
            data = json.loads(openapi_schema_str.strip())
            if not isinstance(data, dict):
                raise
        except Exception as e:
            raise ValidateException("格式错误")
        return OpenAPISchema(**data)
