#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/8/21 22:12
@Author : rxccai@gmail.com
@File   : vector_database_service.py
"""
from dataclasses import dataclass

from flask_weaviate import FlaskWeaviate
from injector import inject
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_weaviate import WeaviateVectorStore
from weaviate.collections import Collection

from .embeddings_service import EmbeddingsService

COLLECTION_NAME = "Dataset"


@inject
@dataclass
class VectorDatabaseService:
    """向量数据库服务"""
    embeddings_service: EmbeddingsService
    weaviate: FlaskWeaviate

    @property
    def vector_store(self) -> WeaviateVectorStore:
        return WeaviateVectorStore(
            client=self.weaviate.client,
            index_name=COLLECTION_NAME,
            text_key="text",
            embedding=self.embeddings_service.embeddings
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @property
    def collection(self) -> Collection:
        return self.weaviate.client.collections.get(COLLECTION_NAME)
