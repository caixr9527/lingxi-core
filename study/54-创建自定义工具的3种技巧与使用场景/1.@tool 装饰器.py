#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/6 21:49
@Author : rxccai@gmail.com
@File   : 1.@tool 装饰器.py
"""
from langchain_core.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """将传递的两个数字相乘"""
    return a * b


# 打印下该工具的相关信息
print("名称: ", multiply.name)
print("描述: ", multiply.description)
print("参数: ", multiply.args)
print("直接返回: ", multiply.return_direct)

# 调用工具
print(multiply.invoke({"a": 2, "b": 8}))
