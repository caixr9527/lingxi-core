#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/30 17:37
@Author : rxccai@gmail.com
@File   : default_config.py
"""
# 应用默认配置项
DEFAULT_CONFIG = {
    "WTF_CSRF_ENABLED": "True",
    # SQLAlchemy数据库配置
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True"
}
