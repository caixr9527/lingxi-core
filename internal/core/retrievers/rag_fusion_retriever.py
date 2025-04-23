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
@Time   : 2025/4/23 15:41
@Author : rxccai@gmail.com
@File   : rag_fusion_retriever.py
"""
from typing import List
from uuid import UUID

from langchain.load import dumps, loads
from langchain.retrievers import MultiQueryRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.pydantic_v1 import Field
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.query import Filter


class RAGFusionRetriever(MultiQueryRetriever):
    """RAG多查询结果融合检索器"""
    k: int = 4
    vector_store: WeaviateVectorStore
    dataset_ids: list[UUID]
    search_kwargs: dict = Field(default_factory=dict)

    @property
    def rag_fusion_retriver(self) -> BaseRetriever:
        self.k = self.search_kwargs.pop("k", 4)
        retriever = self.vector_store.as_retriever(
            **{
                "search_type": "mmr",
                "search_kwargs": {
                    **self.search_kwargs,
                    "filter": Filter.all_of([
                        Filter.by_property("dataset_id").contains_any(
                            [str(dataset_id) for dataset_id in self.dataset_ids]),
                        Filter.by_property("document_enabled").equal(True),
                        Filter.by_property("segment_enabled").equal(True),
                    ])
                }
            }
        )
        return self.from_llm(
            retriever=retriever,
            llm=ChatOpenAI(model="gpt-4o", temperature=0),
        )

    def retrieve_documents(
            self, queries: List[str], run_manager: CallbackManagerForRetrieverRun
    ) -> List[List]:
        """重写检索文档，返回二层嵌套的列表"""
        documents = []
        for query in queries:
            docs = self.retriever.invoke(
                query, config={"callbacks": run_manager.get_child()}
            )
            documents.append(docs)
        return documents

    def unique_union(self, documents: List[List]) -> List[Document]:
        """使用RRF算法对文档列表进行排序&合并"""
        # 初始化一个字典，用于存储每一个唯一文档的得分
        fused_scores = {}

        # 遍历每个查询对应的文档列表
        for docs in documents:
            # 内层遍历文档列表得到每一个文档
            for rank, doc in enumerate(docs):
                # 将文档使用langchain提供的dump工具转换成字符串
                doc_str = dumps(doc)
                # 检测该字符串是否存在得分，如果不存在则赋值为0
                if doc_str not in fused_scores:
                    fused_scores[doc_str] = 0
                # 计算多结果得分，排名越小越靠前，k为控制权重的参数
                fused_scores[doc_str] += 1 / (rank + 60)

        # 提取得分并进行排序
        reranked_results = [
            (loads(doc), score)
            for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        ]

        return [item[0] for item in reranked_results[:self.k]]
