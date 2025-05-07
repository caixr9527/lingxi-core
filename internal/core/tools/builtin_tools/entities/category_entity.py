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
@Time    : 2024/9/22 20:51
@Author  : caixiaorong01@outlook.com
@File    : category_entity.py
"""
from pydantic import BaseModel, field_validator

from internal.exception import FailException


class CategoryEntity(BaseModel):
    """分类实体"""
    category: str  # 分类唯一标识
    name: str  # 分类名称
    icon: str  # 分类图标名称

    @field_validator("icon")
    def check_icon_extension(cls, value: str):
        """校验icon的扩展名是不是.svg，如果不是则抛出错误"""
        if not value.endswith(".svg"):
            raise FailException("该分类的icon图标并不是.svg格式")
        return value
