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
@Time   : 2025/2/5 21:25
@Author : caixiaorong01@outlook.com
@File   : faiss_service.py.py
"""
import os

from injector import inject
from langchain_community.vectorstores import FAISS
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import BaseTool, tool

from internal.core.agent.entities.agent_entity import DATASET_RETRIEVAL_TOOL_NAME
from internal.lib.helper import combine_documents
from .embeddings_service import EmbeddingsService


@inject
class FaissService:
    """Faiss向量数据库服务"""
    faiss: FAISS
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService):
        """构造函数，完成Faiss向量数据库的初始化"""
        # 赋值embeddings_service
        self.embeddings_service = embeddings_service

        # 获取internal路径并计算本地向量数据库的实际路径
        internal_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        faiss_vector_store_path = os.path.join(internal_path, "core", "vector_store")

        # 初始化faiss向量数据库
        self.faiss = FAISS.load_local(
            folder_path=faiss_vector_store_path,
            embeddings=self.embeddings_service.embeddings,
            allow_dangerous_deserialization=True,
        )

    def convert_faiss_to_tool(self) -> BaseTool:
        """将Faiss向量数据库检索器转换成LangChain工具"""
        # 将Faiss向量数据库转换成检索器
        retrieval = self.faiss.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20},
        )

        # 构建检索链，并将检索的结果合并成字符串
        search_chain = retrieval | combine_documents

        class DatasetRetrievalInput(BaseModel):
            """知识库检索工具输入结构"""
            query: str = Field(description="知识库检索query语句，类型为字符串")

        @tool(DATASET_RETRIEVAL_TOOL_NAME, args_schema=DatasetRetrievalInput)
        def dataset_retrieval(query: str) -> str:
            """如果需要检索扩展的知识库内容，当你觉得用户的提问超过你的知识范围时，可以尝试调用该工具，输入为搜索query语句，返回数据为检索内容字符串"""
            return search_chain.invoke(query)

        return dataset_retrieval
