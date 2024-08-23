#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/22 21:25
@Author : rxccai@gmail.com
@File   : 1.Document与TextLoader.py
"""
from langchain_community.document_loaders import TextLoader

loader = TextLoader("./电商数据.txt", "utf-8")
documents = loader.load()
print(documents)
print(len(documents))
print(documents[0].metadata)
