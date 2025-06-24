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
@Time   : 2024/9/20 22:23
@Author : caixiaorong01@outlook.com
@File   : current_time.py
"""
from datetime import datetime
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel

from internal.lib.helper import add_attribute


class CurrentTimeSchema(BaseModel):
    pass


class CurrentTimeTool(BaseTool):
    name: str = "current_time"
    description: str = "一个用于获取当前时间的工具"
    args_schema: Type[BaseModel] = CurrentTimeSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")


@add_attribute("args_schema", CurrentTimeSchema)
def current_time(**kwargs) -> BaseTool:
    return CurrentTimeTool()
