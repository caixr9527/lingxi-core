#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/21 22:41
@Author : rxccai@gmail.com
@File   : 26-Weaviate向量数据库的配置与使用.py
"""
import dotenv
import weaviate
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.query import Filter

dotenv.load_dotenv()

# 3.新增数据
texts = [
    "笨笨是一只很喜欢睡觉的猫咪",
    "我喜欢在夜晚听音乐，这让我感到放松。",
    "猫咪在窗台上打盹，看起来非常可爱。",
    "学习新技能是每个人都应该追求的目标。",
    "我最喜欢的食物是意大利面，尤其是番茄酱的那种。",
    "昨晚我做了一个奇怪的梦，梦见自己在太空飞行。",
    "我的手机突然关机了，让我有些焦虑。",
    "阅读是我每天都会做的事情，我觉得很充实。",
    "他们一起计划了一次周末的野餐，希望天气能好。",
    "我的狗喜欢追逐球，看起来非常开心。",
]

metadatas = [
    {"page": 1},
    {"page": 2},
    {"page": 3},
    {"page": 4},
    {"page": 5},
    {"page": 6, "account_id": 1},
    {"page": 7},
    {"page": 8},
    {"page": 9},
    {"page": 10},
]

# 1.连接weaviate向量数据库
client = weaviate.connect_to_local("127.0.0.1", "8080")

# 2.实例化WeaviateVectorStore
# embedding = OpenAIEmbeddings(model="text-embedding-3-small")
embedding = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L12-v2",
)
db = WeaviateVectorStore(client=client, index_name="Dataset", text_key="text", embedding=embedding)

ids = db.add_texts(texts, metadatas)
print(ids)
# 4.检索数据
# print(db.similarity_search_with_score("笨笨"))

filters = Filter.by_property("page").greater_or_equal(5)
print(db.similarity_search_with_score("笨笨", filters=filters))
retriever = db.as_retriever()
print(retriever.invoke("笨笨"))
