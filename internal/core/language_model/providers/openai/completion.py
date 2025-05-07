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
@Time   : 2025/1/21 21:49
@Author : caixiaorong01@outlook.com
@File   : completion.py.py
"""
from langchain_openai import OpenAI

from internal.core.language_model.entities.model_entity import BaseLanguageModel


class Completion(OpenAI, BaseLanguageModel):
    """OpenAI聊天模型基类"""
    pass
