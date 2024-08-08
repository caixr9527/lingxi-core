#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/8 23:04
@Author : rxccai@gmail.com
@File   : 01.OpenAI嵌入模型示例.py
"""
import dotenv
from langchain_openai import OpenAIEmbeddings

dotenv.load_dotenv()
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

query_vector = embeddings.embed_query("hello world")
print(query_vector)
print(len(query_vector))
