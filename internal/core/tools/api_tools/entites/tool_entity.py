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
