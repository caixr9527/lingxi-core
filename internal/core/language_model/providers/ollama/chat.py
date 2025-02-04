#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/2/4 22:26
@Author : rxccai@gmail.com
@File   : chat.py.py
"""
from langchain_ollama import ChatOllama

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(ChatOllama, BaseLanguageModel):
    """Ollama聊天模型"""
    pass
