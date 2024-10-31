#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/29 22:53
@Author : rxccai@gmail.com
@File   : cache_entity.py
"""
LOCK_EXPIRE_TIME = 600

# 更新文档启用状态锁
LOCK_DOCUMENT_UPDATE_ENABLED = "lock:document:update:enabled_{document_id}"
# 更新关键词表缓存锁
LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE = "lock:keyword_table:update:keyword_table_{dataset_id}"
