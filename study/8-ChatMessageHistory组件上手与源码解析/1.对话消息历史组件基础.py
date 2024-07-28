#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/7/28 20:31
@Author : rxccai@gmail.com
@File   : 1.对话消息历史组件基础.py
"""

from langchain_core.chat_history import InMemoryChatMessageHistory

chat_history = InMemoryChatMessageHistory()

chat_history.add_user_message()
