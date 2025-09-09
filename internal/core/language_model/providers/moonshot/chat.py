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
@Time   : 2025/1/23 21:27
@Author : caixiaorong01@outlook.com
@File   : chat.py.py
"""
import os
from typing import Tuple

import tiktoken
from langchain_openai.chat_models.base import BaseChatOpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Chat(BaseChatOpenAI, BaseLanguageModel):
    """月之暗面聊天模型"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            openai_api_base=kwargs.get("base_url") if kwargs.get("base_url") else os.getenv("MOONSHOT_API_KEY"),
            openai_api_key=kwargs.get("api_key") if kwargs.get("api_key") else os.getenv("MOONSHOT_API_BASE_URL"),
            **kwargs
        )

    def _get_encoding_model(self) -> Tuple[str, tiktoken.Encoding]:
        # 将月之暗面的词表模型设置为gpt-3.5-turbo
        model = "gpt-3.5-turbo"
        return model, tiktoken.encoding_for_model(model)
