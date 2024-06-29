#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/29 21:08
@Author : rxccai@gmail.com
@File   : config.py
"""


class Config:
    def __init__(self):
        # 关闭CSRF保护
        self.WTF_CSRF_ENABLED = False
