#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/26 09:59
@Author : rxccai@gmail.com
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
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(dataset_id=dataset_id)
        with self.redis_client.lock(str(cache_key), timeout=LOCK_EXPIRE_TIME):
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = {
                field: set(value) for field, value in keyword_table_record.keyword_table.items()
            }

            # 根据segment_id查询片段关键词
            segments = self.db.session.query(Segment).with_entities(Segment.id, Segment.keywords).filter(
                Segment.id.in_(segment_ids),
            ).all()

            for id, keywords in segments:
                for keyword in keywords:
                    if keyword not in keyword_table:
                        keyword_table[keyword] = set()
                    keyword_table[keyword].add(str(id))

            self.update(
                keyword_table_record,
                keyword_table={field: list(value) for field, value in keyword_table.items()}
            )
