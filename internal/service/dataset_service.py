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
@Time   : 2024/10/17 20:49
@Author : caixiaorong01@outlook.com
@File   : dataset_service.py
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidateException, NotFoundException, FailException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Dataset, Segment, DatasetQuery, AppDatasetJoin, Account
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    HitReq
)
from internal.task.dataset_task import delete_dataset
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .retrieval_service import RetrievalService


@inject
@dataclass
class DatasetService(BaseService):
    db: SQLAlchemy
    retrieval_service: RetrievalService

    def create_dataset(self, req: CreateDatasetReq, account: Account) -> Dataset:
        dateset = self.db.session.query(Dataset).filter_by(
            account_id=account.id,
            name=req.name.data
        ).one_or_none()
        if dateset:
            raise ValidateException(f"该知识库{req.name.data}已存在")
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        return self.create(
            Dataset,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data
        )

    def get_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        return dataset

    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq, account: Account) -> Dataset:
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account.id,
            Dataset.name == req.name.data,
            Dataset.id != dataset_id,
        ).one_or_none()
        if check_dataset:
            raise ValidateException(f"该知识库名称{req.name.data}已存在")

        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        self.update(
            dataset,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data
        )
        return dataset

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq, account: Account) -> tuple[list[Dataset], Paginator]:
        paginator = Paginator(db=self.db, req=req)
        filters = [Dataset.account_id == account.id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at"))
        )

        return datasets, paginator

    def hit(self, dataset_id: UUID, req: HitReq, account: Account) -> list[dict]:
        # 检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        # 调用检索服务执行检索
        lc_documents = self.retrieval_service.search_in_datasets(
            dataset_ids=[dataset_id],
            account_id=account.id,
            **req.data,
        )
        lc_document_dict = {str(lc_document.metadata["segment_id"]): lc_document for lc_document in lc_documents}

        # 根据检索到的数据查询对应的片段信息
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([str(lc_document.metadata["segment_id"]) for lc_document in lc_documents])
        ).all()
        segment_dict = {str(segment.id): segment for segment in segments}

        # 排序片段数据
        sorted_segments = [
            segment_dict[str(lc_document.metadata["segment_id"])]
            for lc_document in lc_documents
            if str(lc_document.metadata["segment_id"]) in segment_dict
        ]
        # 组装响应数据
        hit_result = []
        for segment in sorted_segments:
            document = segment.document
            if document is None:
                continue
            upload_file = document.upload_file
            hit_result.append({
                "id": segment.id,
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "extension": upload_file.extension,
                    "mime_type": upload_file.mime_type,
                },
                "dataset_id": segment.dataset_id,
                "score": lc_document_dict[str(segment.id)].metadata["score"],
                "position": segment.position,
                "content": segment.content,
                "keywords": segment.keywords,
                "character_count": segment.character_count,
                "token_count": segment.token_count,
                "hit_count": segment.hit_count,
                "enabled": segment.enabled,
                "disabled_at": datetime_to_timestamp(segment.disabled_at),
                "status": segment.status,
                "error": segment.error,
                "updated_at": datetime_to_timestamp(segment.updated_at),
                "created_at": datetime_to_timestamp(segment.created_at),
            })

        return hit_result

    def get_dataset_queries(self, dataset_id: UUID, account: Account) -> list[DatasetQuery]:
        """根据传递的知识库id获取最近的10条查询记录"""

        # 1.获取知识库并校验权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        # 2.调用知识库查询模型查找最近的10条记录
        dataset_queries = self.db.session.query(DatasetQuery).filter(
            DatasetQuery.dataset_id == dataset_id,
        ).order_by(desc("created_at")).limit(10).all()

        return dataset_queries

    def delete_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """根据传递的知识库id删除知识库信息，涵盖知识库底下的所有文档、片段、关键词，以及向量数据库里存储的数据"""

        # 1.获取知识库并校验权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("该知识库不存在")

        try:
            # 2.删除知识库基础记录以及知识库和应用关联的记录
            self.delete(dataset)
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(
                    AppDatasetJoin.dataset_id == dataset_id,
                ).delete()

            # 3.调用异步任务执行后续的操作
            delete_dataset.delay(dataset_id)
        except Exception as e:
            logging.exception(f"删除知识库失败, dataset_id: {dataset_id}, 错误信息: {str(e)}")
            raise FailException("删除知识库失败，请稍后重试")
