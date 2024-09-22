#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/9/22 20:51
@Author  : rxccai@gmail.com
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
