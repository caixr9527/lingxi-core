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
