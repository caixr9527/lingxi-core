#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/23 21:27
@Author : rxccai@gmail.com
@File   : chat.py.py
"""
from typing import Tuple

import tiktoken
from langchain_community.chat_models.moonshot import MoonshotChat

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(MoonshotChat, BaseLanguageModel):
    """月之暗面聊天模型"""

    def _get_encoding_model(self) -> Tuple[str, tiktoken.Encoding]:
        # 将月之暗面的词表模型设置为gpt-3.5-turbo
        model = "gpt-3.5-turbo"
        return model, tiktoken.encoding_for_model(model)
