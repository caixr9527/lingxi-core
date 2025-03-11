#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/3/11 21:41
@Author : rxccai@gmail.com
@File   : platform_entity.py
"""
from enum import Enum


class WechatConfigStatus(str, Enum):
    """微信配置状态"""
    CONFIGURED = "configured"  # 已配置
    UNCONFIGURED = "unconfigured"  # 未配置
