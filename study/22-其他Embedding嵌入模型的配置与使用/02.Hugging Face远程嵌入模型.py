#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/9 20:52
@Author : rxccai@gmail.com
@File   : 01.Hugging Face本地嵌入模型.py
"""
import dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings

dotenv.load_dotenv()
embedding = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L12-v2",
)

query_vector = embedding.embed_query("你好，我是蔡徐坤")
print(query_vector)
print(len(query_vector))
