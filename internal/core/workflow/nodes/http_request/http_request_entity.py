#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/9 22:16
@Author : rxccai@gmail.com
@File   : http_request_entity.py.py
"""
from enum import Enum

from langchain_core.pydantic_v1 import Field, validator, HttpUrl

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableType, VariableValueType
from internal.exception import ValidateException


class HttpRequestMethod(str, Enum):
    """Http请求方法类型枚举"""
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    HEAD = "head"
    OPTIONS = "options"


class HttpRequestInputType(str, Enum):
    """Http请求输入变量类型"""
    PARAMS = "params"  # query参数
    HEADERS = "headers"  # header请求头
    BODY = "body"  # body参数


class HttpRequestNodeData(BaseNodeData):
    """HTTP请求节点数据"""
    url: HttpUrl = ""  # 请求URL地址
    method: HttpRequestMethod = HttpRequestMethod.GET  # API请求方法
    inputs: list[VariableEntity] = Field(default_factory=list)  # 输入变量列表
    outputs: list[VariableEntity] = Field(
        default_factory=lambda: [
            VariableEntity(
                name="status_code",
                type=VariableType.INT,
                value={"type": VariableValueType.GENERATED, "content": 0},
            ),
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED}),
        ],
    )

    @validator("outputs", pre=True)
    def validate_outputs(cls, outputs: list[VariableEntity]):
        return [
            VariableEntity(
                name="status_code",
                type=VariableType.INT,
                value={"type": VariableValueType.GENERATED, "content": 0},
            ),
            VariableEntity(name="text", value={"type": VariableValueType.GENERATED}),
        ]

    @validator("inputs")
    def validate_inputs(cls, inputs: list[VariableEntity]):
        """校验输入列表数据"""
        # 1.校验判断输入变量列表中的类型信息
        for input in inputs:
            if input.meta.get("type") not in HttpRequestInputType.__members__.values():
                raise ValidateException("Http请求参数结构出错")

        # 2.返回校验后的数据
        return inputs
