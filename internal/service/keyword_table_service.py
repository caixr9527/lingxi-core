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
@Time   : 2024/10/26 09:59
@Author : caixiaorong01@outlook.com
@File   : keyword_table_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from redis import Redis

from internal.entity.cache_entity import (
    LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE,
    LOCK_EXPIRE_TIME
)
from internal.model import KeywordTable, Segment
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class KeywordTableService(BaseService):
    db: SQLAlchemy
    redis_client: Redis

    def get_keyword_table_from_dataset_id(self, dataset_id: UUID) -> KeywordTable:
        keyword_table = self.db.session.query(KeywordTable).filter(
            KeywordTable.dataset_id == dataset_id
        ).one_or_none()
        if keyword_table is None:
            keyword_table = self.create(KeywordTable, dataset_id=dataset_id, keyword_table={})

        return keyword_table

    def delete_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[UUID]) -> None:
        # 删除知识库表的多余数据
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(str(cache_key), timeout=LOCK_EXPIRE_TIME):
            # 获取关键词表
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = keyword_table_record.keyword_table.copy()

            segment_ids_to_delete = set([str(segment_id) for segment_id in segment_ids])
            keywords_to_delete = set()

            for keyword, ids in keyword_table.items():
                ids_set = set(ids)
                if segment_ids_to_delete.intersection(ids_set):
                    keyword_table[keyword] = list(ids_set.difference(segment_ids_to_delete))
                    if not keyword_table[keyword]:
                        keywords_to_delete.add(keyword)
            # 检测空关键词并删除
            for keyword in keywords_to_delete:
                del keyword_table[keyword]

            # 将数据更新到关键词表
            self.update(keyword_table_record, keyword_table=keyword_table)

    def add_keyword_table_from_ids(self, dataset_id: UUID, segment_ids: list[UUID]) -> None:
        # 1.新增知识库关键词表里多余的数据，该操作需要上锁，避免在并发的情况下拿到错误的数据
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            # 2.获取指定知识库的关键词比哦啊
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = {
                field: set(value) for field, value in keyword_table_record.keyword_table.items()
            }

            # 3.根据segment_ids查找片段的关键词信息
            segments = self.db.session.query(Segment).with_entities(Segment.id, Segment.keywords).filter(
                Segment.id.in_(segment_ids),
            ).all()

            # 4.循环将新关键词添加到关键词表中
            for id, keywords in segments:
                for keyword in keywords:
                    if keyword not in keyword_table:
                        keyword_table[keyword] = set()
                    keyword_table[keyword].add(str(id))

            # 5.更新关键词表
            self.update(
                keyword_table_record,
                keyword_table={field: list(value) for field, value in keyword_table.items()}
            )
