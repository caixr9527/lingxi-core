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
@Time   : 2024/9/20 22:32
@Author : caixiaorong01@outlook.com
@File   : duckduckgo_search.py
"""
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool

from internal.lib.helper import add_attribute


class DDGInput(BaseModel):
    query: str = Field(description="需要搜索的查询语句")


@add_attribute("args_schema", DDGInput)
def duckduckgo_search(**kwargs) -> BaseTool:
    return DuckDuckGoSearchRun(
        description="一个注重隐私的搜索工具，当你需要瘦瘦时事时可以使用该工具",
        args_schema=DDGInput
    )
