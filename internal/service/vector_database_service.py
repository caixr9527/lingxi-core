#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/21 22:12
@Author : rxccai@gmail.com
@File   : vector_database_service.py
"""
import os

import weaviate
from injector import inject
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate import WeaviateClient


@inject
class VectorDatabaseService:
    """向量数据库服务"""
    client: WeaviateClient
    vector_store: WeaviateVectorStore

    def __init__(self):
        """构造函数，完成向量数据库服务客户端和LangChain向量数据库示例创建"""
        # 1. 创建/连接weaviate向量数据库
        self.client = weaviate.connect_to_local(
            host=os.getenv("WEAVIATE_HOST"),
            port=int(os.getenv("WEAVIATE_PORT"))
        )
        # todo 这里使用text-embedding-3-small
        embedding = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L12-v2",
        )
        # 2. 创建LangChain向量数据库
        self.vector_store = WeaviateVectorStore(
            client=self.client,
            index_name="Dataset",
            text_key="text",
            # embedding=OpenAIEmbeddings(model="text-embedding-3-small")
            embedding=embedding
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @classmethod
    def combine_documents(cls, documents: list[Document]) -> str:
        """将对应的文档列表使用换行符合并"""
        doc = "\n\n".join([document.page_content for document in documents])
        return doc
