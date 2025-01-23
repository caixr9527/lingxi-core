#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/23 21:35
@Author : rxccai@gmail.com
@File   : chat.py.py
"""
from langchain_community.chat_models.baidu_qianfan_endpoint import QianfanChatEndpoint

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(QianfanChatEndpoint, BaseLanguageModel):
    """百度千帆聊天模型"""
    pass
