#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/7/6 14:48
@Author : rxccai@gmail.com
@File   : 1.Prompt组件基础用法.py
"""
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template("请讲一个关于{subject}的冷笑话")
print()
