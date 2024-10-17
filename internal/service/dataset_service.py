#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/17 20:49
@Author : rxccai@gmail.com
@File   : dataset_service.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidateException, NotFoundException
from internal.model import Dataset
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetsWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class DatasetService(BaseService):
    db: SQLAlchemy

    def create_dataset(self, req: CreateDatasetReq) -> Dataset:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        dateset = self.db.session.query(Dataset).filter_by(
            account_id=account_id,
            name=req.name.data
        ).one_or_none()
        if dateset:
            raise ValidateException(f"该知识库{req.name.data}已存在")
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        return self.create(
            Dataset,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data
        )

    def get_dataset(self, dataset_id: UUID) -> Dataset:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("该知识库不存在")

        return dataset

    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq) -> Dataset:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("该知识库不存在")

        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account_id,
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

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq) -> tuple[list[Dataset], Paginator]:
        # todo
        account_id = "e7300838-b215-4f97-b420-2333a699e22e"
        paginator = Paginator(db=self.db, req=req)
        filters = [Dataset.account_id == account_id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at"))
        )

        return datasets, paginator
