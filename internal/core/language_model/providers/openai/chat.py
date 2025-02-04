#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/21 21:49
@Author : rxccai@gmail.com
@File   : chat.py
"""
from langchain_openai import ChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOpenAI, BaseLanguageModel):
    """OpenAI聊天模型基类"""
    pass
