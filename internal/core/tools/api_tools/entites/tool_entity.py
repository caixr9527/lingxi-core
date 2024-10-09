#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/9 20:35
@Author : rxccai@gmail.com
@File   : tool_entity.py
"""
from pydantic import BaseModel, Field


class ToolEntity(BaseModel):
    id: str = Field(default="", description="API工具提供者对应的id")
    name: str = Field(default="", description="API工具的名称")
    url: str = Field(default="", description="API工具发起请求的URL地址")
    method: str = Field(default="get", description="API工具发起请求的方法")
    description: str = Field(default="", description="API工具的描述信息")
    headers: list[dict] = Field(default_factory=list, description="API工具的请求头信息")
    parameters: list[dict] = Field(default_factory=list, description="API工具的参数列表信息")
