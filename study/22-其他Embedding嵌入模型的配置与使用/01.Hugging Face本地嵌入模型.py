#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/9 20:52
@Author : rxccai@gmail.com
@File   : 01.Hugging Face本地嵌入模型.py
"""
from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L12-v2",
    cache_folder="./embeddings/"
)

query_vector = embedding.embed_query("你好，我是蔡徐坤")
print(query_vector)
print(len(query_vector))
