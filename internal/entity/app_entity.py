#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/11/25 22:04
@Author  : rxccai@gmail.com
@File    : app_entity.py
"""
from enum import Enum


class AppStatus(str, Enum):
    """应用状态枚举类"""
    DRAFT = "draft"
    PUBLISHED = "published"


class AppConfigType(str, Enum):
    """应用配置类型枚举类"""
    DRAFT = "draft"
    PUBLISHED = "published"


# 应用默认配置信息
DEFAULT_APP_CONFIG = {
    "model_config": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "parameters": {
            "temperature": 0.5,
            "top_p": 0.85,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.2,
            "max_tokens": 8192,
        },
    },
    "dialog_round": 3,
    "preset_prompt": "",
    "tools": [],
    "workflows": [],
    "datasets": [],
    "retrieval_config": {
        "retrieval_strategy": "semantic",
        "k": 10,
        "score": 0.5,
    },
    "long_term_memory": {
        "enable": False,
    },
    "opening_statement": "",
    "opening_questions": [],
    "speech_to_text": {
        "enable": False,
    },
    "text_to_speech": {
        "enable": False,
        "voice": "echo",
        "auto_play": False,
    },
    "suggested_after_answer": {
        "enable": True,
    },
    "review_config": {
        "enable": False,
        "keywords": [],
        "inputs_config": {
            "enable": False,
            "preset_response": "",
        },
        "outputs_config": {
            "enable": False,
        },
    },
}
