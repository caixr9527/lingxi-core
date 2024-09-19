#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/19 22:31
@Author : rxccai@gmail.com
@File   : tool_entity.py
"""
from pydantic import BaseModel


class ToolEntity(BaseModel):
    """工具实体类"""
    name: str
    label: str
    description: str
    params: list = []
