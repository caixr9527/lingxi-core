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
@Time   : 2024/10/17 20:20
@Author : caixiaorong01@outlook.com
@File   : dataset_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.core.file_extractor import FileExtractor
from internal.model import UploadFile
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    GetDatasetResp,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    GetDatasetsWithPageResp,
    HitReq,
    GetDatasetQueriesResp
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

    @login_required
    def embeddings_query(self):
        upload_file = self.db.session.query(UploadFile).get("8ed477e0-603f-449a-9617-223abd8cd940")
        content = self.file_extractor.load(upload_file, True)
        return success_json({"content": content})
        # query = request.args.get("query")
        # keywords = self.jieba_service.extract_keywords(query)
        # return success_json({"keywords": keywords})

    @login_required
    def hit(self, dataset_id: UUID):
        req = HitReq()
        if not req.validate():
            return validate_error_json(req.errors)
        hit_result = self.dataset_service.hit(dataset_id, req, account=current_user)
        return success_json(hit_result)

    @login_required
    def get_dataset_queries(self, dataset_id: UUID):

        dataset_queries = self.dataset_service.get_dataset_queries(dataset_id, account=current_user)
        resp = GetDatasetQueriesResp(many=True)
        return success_json(resp.dump(dataset_queries))

    @login_required
    def create_dataset(self):
        req = CreateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.create_dataset(req, account=current_user)

        return success_message("创建知识库成功")

    @login_required
    def get_dataset(self, dataset_id: UUID):
        dataset = self.dataset_service.get_dataset(dataset_id, account=current_user)
        resp = GetDatasetResp()
        return success_json(resp.dump(dataset))

    @login_required
    def update_dataset(self, dataset_id: UUID):
        req = UpdateDatasetReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.dataset_service.update_dataset(dataset_id, req, account=current_user)

        return success_message("更新知识库成功")

    @login_required
    def get_datasets_with_page(self):
        req = GetDatasetsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        datasets, paginator = self.dataset_service.get_datasets_with_page(req, account=current_user)

        resp = GetDatasetsWithPageResp(many=True)

        return success_json(PageModel(list=resp.dump(datasets), paginator=paginator))

    @login_required
    def delete_dataset(self, dataset_id: UUID):
        """根据传递的知识库id删除知识库"""
        self.dataset_service.delete_dataset(dataset_id, account=current_user)
        return success_message("删除知识库成功")
