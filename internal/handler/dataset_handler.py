#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/17 20:20
@Author : rxccai@gmail.com
@File   : dataset_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.model import UploadFile
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    GetDatasetResp,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    GetDatasetsWithPageResp
)
from internal.service import DatasetService, EmbeddingsService, JiebaService, VectorDatabaseService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_message, success_json
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class DatasetHandler:
    dataset_service: DatasetService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    file_extractor: FileExtractor
    vector_database_service: VectorDatabaseService
    db: SQLAlchemy

    def embeddings_query(self):
        upload_file = self.db.session.query(UploadFile).get("8ed477e0-603f-449a-9617-223abd8cd940")
        content = self.file_extractor.load(upload_file, True)
        return success_json({"content": content})
        # query = request.args.get("query")
        # keywords = self.jieba_service.extract_keywords(query)
        # return success_json({"keywords": keywords})

    def hit(self, dataset_id: UUID):
        from weaviate.classes.query import Filter
        query = "长恨歌"
        retriever = self.vector_database_service.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 10,
                "filters": Filter.all_of([
                    Filter.by_property("document_id").equal("38d5df91-4cdc-4407-931b-283eebb836f8"),
                    # Filter.by_property("document_enabled").equal(True),
                    # Filter.by_property("segment_enabled").equal(True),
                    # Filter.any_of([
                    #     Filter.by_property("dataset_id").equal("e6fc9059-2570-4315-994e-e566d4398926"),
                    #     Filter.by_property("dataset_id").equal("e6fc9059-2570-4315-994e-e566d4398927"),
                    #     Filter.by_property("document_id").equal("8547c5c6-e27b-45ad-8f89-0c1a4f871031"),
                    #
                    # ])
                ])
            }
        )
        documents = retriever.invoke(query)
        return success_json({
            "documents": [
                {
                    "page_content": document.page_content,
                    "metadata": document.metadata
                } for document in documents
            ]
        })

    def create_dataset(self):
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.create_dataset(req)

        return success_message("创建知识库成功")

    def get_dataset(self, dataset_id: UUID):
        dataset = self.dataset_service.get_dataset(dataset_id)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))

    def update_dataset(self, dataset_id: UUID):
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.update_dataset(dataset_id, req)

        return success_message("更新知识库成功")

    def get_datasets_with_page(self):
        req = GetDatasetsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        datasets, paginator = self.dataset_service.get_datasets_with_page(req)

        resp = GetDatasetsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))
