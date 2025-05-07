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
@Time   : 2024/10/29 22:53
@Author : caixiaorong01@outlook.com
@File   : cache_entity.py
"""
LOCK_EXPIRE_TIME = 600

# 更新文档启用状态锁
LOCK_DOCUMENT_UPDATE_ENABLED = "lock:document:update:enabled_{document_id}"
# 更新关键词表缓存锁
LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE = "lock:keyword_table:update:keyword_table_{dataset_id}"

LOCK_SEGMENT_UPDATE_ENABLED = "lock:segment:update:enabled_{segment_id}"
