#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/24 23:41
@Author : rxccai@gmail.com
@File   : openapi_schema.py
"""
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from internal.exception import ValidateException


class ParameterType(str, Enum):
    STR: str = "str"
    INT: str = "int"
    FLOAT: str = "float"
    BOOL: str = "bool"


class ParameterIn(str, Enum):
    PATH: str = "path"
    QUERY: str = "query"
    HEADER: str = "header"
    COOKIE: str = "cookie"
    REQUEST_BODY: str = "request_body"


class OpenAPISchema(BaseModel):
    """OpenAPI规范的数据结构"""
    server: str = Field(default="", validate_default=True, description="工具提供者的服务基础地址")
    description: str = Field(default="", validate_default=True, description="工具提供者的描述信息")
    paths: dict[str, dict] = Field(default_factory=dict, validate_default=True, description="工具提供者的路径参数字典")

    @field_validator("server", mode="before")
    def validate_server(cls, server: str) -> str:
        """校验server数据"""
        if server is None or server == "":
            raise ValidateException("server不能为空")
        return server

    @field_validator("description", mode="before")
    def validate_description(cls, description: str) -> str:
        if description is None or description == "":
            raise ValidateException("description不能为空")
        return description

    @field_validator("paths", mode="before")
    def validate_paths(cls, paths: dict[str, dict]) -> dict[str, dict]:
        # paths不能为空且类型必须为字典
        if not paths or not isinstance(paths, dict):
            raise ValidateException("paths不能为空，且类型必须为字典")
        # 提取path里的每个元素，并获取对应值
        methods = ["get", "post"]
        interfaces = []
        extra_paths = {}
        for path, path_item in paths.items():
            for method in methods:
                if method in path_item:
                    interfaces.append({
                        "path": path,
                        "method": method,
                        "operation": path_item[method],
                    })

        # 校验信息
        operation_ids = []
        for interface in interfaces:
            if not isinstance(interface["operation"].get("description"), str):
                raise ValidateException("description不能为空且需为字符串")
            if not isinstance(interface["operation"].get("operationId"), str):
                raise ValidateException("operationId不能为空且需为字符串")
            if not isinstance(interface["operation"].get("parameters", []), list):
                raise ValidateException("parameters必须是列表或者为空")

            if interface["operation"]["operationId"] in operation_ids:
                raise ValidateException(f"operationId: {interface["operation"]["operationId"]} 必须唯一")

            operation_ids.append(interface["operation"]["operationId"])

            for parameter in interface["operation"].get("parameters", []):
                if not isinstance(parameter.get("name"), str):
                    raise ValidateException("parameter.name参数必须为字符串且不为空")
                if not isinstance(parameter.get("description"), str):
                    raise ValidateException("parameter.description参数必须为字符串且不为空")
                if not isinstance(parameter.get("required"), bool):
                    raise ValidateException("parameter.required参数必须为布尔值且不为空")
                if (
                        not isinstance(parameter.get("in"), str)
                        or parameter.get("in") not in ParameterIn.__members__.values()
                ):
                    raise ValidateException(f"parameter.in参数必须为{'/'.join([item.value for item in ParameterIn])}")
                if (
                        not isinstance(parameter.get("type"), str)
                        or parameter.get("type") not in ParameterType.__members__.values()
                ):
                    raise ValidateException(
                        f"parameter.type参数必须为{'/'.join([item.value for item in ParameterType])}")

            extra_paths[interface["path"]] = {
                interface["method"]: {
                    "description": interface["operation"]["description"],
                    "operationId": interface["operation"]["operationId"],
                    "parameters": [{
                        "name": parameter.get("name"),
                        "in": parameter.get("in"),
                        "description": parameter.get("description"),
                        "required": parameter.get("required"),
                        "type": parameter.get("type")
                    } for parameter in interface["operation"].get("parameters", [])]
                }
            }

        return extra_paths
