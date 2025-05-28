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
@Time    : 2025/01/02 22:10
@Author  : caixiaorong01@outlook.com
@File    : builtin_app_entity.py
"""
from typing import Any

from pydantic import BaseModel, Field

from internal.entity.app_entity import DEFAULT_APP_CONFIG


class BuiltinAppEntity(BaseModel):
    """内置工具实体类"""
    id: str = Field(default="")
    category: str = Field(default="")
    name: str = Field(default="")
    icon: str = Field(default="")
    description: str = Field(default="")
    language_model_config: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("model_config"))
    dialog_round: int = Field(default=DEFAULT_APP_CONFIG.get("dialog_round"))
    preset_prompt: str = Field(default=DEFAULT_APP_CONFIG.get("preset_prompt"))
    tools: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_config: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("retrieval_config"))
    long_term_memory: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("long_term_memory"))
    opening_statement: str = Field(default=DEFAULT_APP_CONFIG.get("opening_statement"))
    opening_questions: list[str] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("opening_questions"))
    speech_to_text: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("speech_to_text"))
    text_to_speech: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("text_to_speech"))
    suggested_after_answer: dict[str, Any] = Field(
        default_factory=lambda: DEFAULT_APP_CONFIG.get("suggested_after_answer"),
    )
    multimodal: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("multimodal"))
    review_config: dict[str, Any] = Field(default_factory=lambda: DEFAULT_APP_CONFIG.get("review_config"))
    created_at: int = Field(default=0)
