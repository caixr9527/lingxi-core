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
@Time   : 2024/11/4 23:10
@Author : caixiaorong01@outlook.com
@File   : full_text_retriever.py
"""
from collections import Counter
from typing import List
from uuid import UUID

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from internal.model import KeywordTable, Segment
from internal.service import JiebaService
from pkg.sqlalchemy import SQLAlchemy


class FullTextRetriever(BaseRetriever):
    """全文检索器"""

    db: SQLAlchemy
    dataset_ids: list[UUID]
    jieba_service: JiebaService
    search_kwargs: dict = Field(default_factory=dict)

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[LCDocument]:
        # 查询query转化成的关键词
        keywords = self.jieba_service.extract_keywords(query, 10)
        # 查询指定知识库的关键词表
        keyword_tables = [keyword_table for keyword_table, in
                          self.db.session.query(KeywordTable).with_entities(KeywordTable.keyword_table).filter(
                              KeywordTable.dataset_id.in_(self.dataset_ids)
                          ).all()]
        # 便利所有的知识库关键词表，找到匹配query关键词的id列表
        all_ids = []
        for keyword_table in keyword_tables:
            for keyword, segment_ids in keyword_table.items():
                if keyword in keywords:
                    all_ids.extend(segment_ids)
        # 统计segment_id出现的频率
        id_counter = Counter(all_ids)
        # 获取前k条数据
        k = self.search_kwargs.get('k', 4)
        top_k_ids = id_counter.most_common(k)
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([id for id, _ in top_k_ids])
        ).all()
        segment_dict = {
            str(segment.id): segment for segment in segments
        }
        # 根据频率排序
        sorted_segments = [segment_dict[str(id)] for id, freq in top_k_ids if id in segment_dict]
        # 构建langchain文档列表
        lc_documents = [LCDocument(
            page_content=segment.content,
            metadata={
                "account_id": str(segment.account_id),
                "dataset_id": str(segment.dataset_id),
                "document_id": str(segment.document_id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": True,
                "segment_enabled": True,
                "score": 0,
            }
        ) for segment in sorted_segments]
        return lc_documents
