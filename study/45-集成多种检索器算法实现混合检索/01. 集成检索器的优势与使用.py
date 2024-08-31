#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/31 21:14
@Author : rxccai@gmail.com
@File   : 01. 集成检索器的优势与使用.py
"""
import dotenv
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

dotenv.load_dotenv()

# 1.创建文档列表
documents = [
    Document(page_content="笨笨是一只很喜欢睡觉的猫咪", metadata={"page": 1}),
    Document(page_content="我喜欢在夜晚听音乐，这让我感到放松。", metadata={"page": 2}),
    Document(page_content="猫咪在窗台上打盹，看起来非常可爱。", metadata={"page": 3}),
    Document(page_content="学习新技能是每个人都应该追求的目标。", metadata={"page": 4}),
    Document(page_content="我最喜欢的食物是意大利面，尤其是番茄酱的那种。", metadata={"page": 5}),
    Document(page_content="昨晚我做了一个奇怪的梦，梦见自己在太空飞行。", metadata={"page": 6}),
    Document(page_content="我的手机突然关机了，让我有些焦虑。", metadata={"page": 7}),
    Document(page_content="阅读是我每天都会做的事情，我觉得很充实。", metadata={"page": 8}),
    Document(page_content="他们一起计划了一次周末的野餐，希望天气能好。", metadata={"page": 9}),
    Document(page_content="我的狗喜欢追逐球，看起来非常开心。", metadata={"page": 10}),
]

# 2.构建BM25关键词检索器
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 4

# 3.创建FAISS向量数据库检索
faiss_db = FAISS.from_documents(documents, embedding=OpenAIEmbeddings(model="text-embedding-3-small"))
faiss_retriever = faiss_db.as_retriever(search_kwargs={"k": 4})

# 4.初始化集成检索器
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
    weights=[0.5, 0.5],
)

# 5.执行检索
docs = ensemble_retriever.invoke("除了猫，你养了什么宠物呢？")
print(docs)
print(len(docs))
