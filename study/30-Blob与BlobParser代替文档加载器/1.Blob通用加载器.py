#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/23 22:30
@Author : rxccai@gmail.com
@File   : 1.Blob通用加载器.py
"""
from langchain_community.document_loaders.generic import GenericLoader

loader = GenericLoader.from_filesystem(".", glob="*.txt", show_progress=True)

for idx, doc in enumerate(loader.lazy_load()):
    print(f"当前加载第{idx + 1}个文件，文件信息:{doc.metadata}")
