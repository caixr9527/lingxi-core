#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/5 11:12
@Author : rxccai@gmail.com
@File   : variable_entity.py
"""
import re
from enum import Enum
from typing import Union, Any
from uuid import UUID

from langchain_core.pydantic_v1 import BaseModel, Field, validator

from internal.exception import ValidateException


class VariableType(str, Enum):
    """变量的类型枚举"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"


# 变量类型与声明的映射
VARIABLE_TYPE_MAP = {
    VariableType.STRING: str,
    VariableType.INT: int,
    VariableType.FLOAT: float,
    VariableType.BOOLEAN: bool,
}

# 变量类型默认值映射
VARIABLE_TYPE_DEFAULT_VALUE_MAP = {
    VariableType.STRING: "",
    VariableType.INT: 0,
    VariableType.FLOAT: 0,
    VariableType.BOOLEAN: False,
}

# 变量名字正则匹配规则
VARIABLE_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'

# 描述最大长度
VARIABLE_DESCRIPTION_MAX_LENGTH = 1024


class VariableValueType(str, Enum):
    """变量内置值类型枚举"""
    REF = "ref"  # 引用类型
    LITERAL = "literal"  # 字面数据/直接输入
    GENERATED = "generated"  # 生成的值，一般用在开始节点或者output中


class VariableEntity(BaseModel):
    class Value(BaseModel):
        """变量的实体值信息"""

        class Content(BaseModel):
            """变量内容实体信息，如果类型为引用，则使用content记录引用节点id+引用节点的变量名"""
            ref_node_id: UUID
            ref_var_name: str

        type: VariableValueType = VariableValueType.LITERAL
        content: Union[Content, str, int, float, bool] = ""

    name: str = ""  # 变量的名字
    description: str = ""  # 变量的描述信息
    required: bool = True  # 变量是否必填
    type: VariableType = VariableType.STRING  # 变量的类型
    value: Value = Field(default_factory=lambda: {"type": VariableValueType.LITERAL, "content": ""})  # 变量对应的值
    meta: dict[str, Any] = Field(default_factory=dict)  # 变量元数据，存储一些额外的信息

    @validator("name")
    def validate_name(cls, value: str) -> str:
        """自定义校验函数，用于校验变量名字"""
        if not re.match(VARIABLE_NAME_PATTERN, value):
            raise ValidateException("变量名字仅支持字母、数字和下划线，且以字母/下划线为开头")
        return value

    @validator("description")
    def validate_description(cls, value: str) -> str:
        """自定义校验函数，用于校验描述信息，截取前1024个字符"""
        return value[:VARIABLE_DESCRIPTION_MAX_LENGTH]
