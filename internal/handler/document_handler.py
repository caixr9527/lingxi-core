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
@Time   : 2024/10/21 23:16
@Author : caixiaorong01@outlook.com
@File   : document_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
from flask_login import login_required, current_user
from injector import inject

from internal.schema.document_schema import (
    CreateDocumentsReq,
    CreateDocumentResp,
    GetDocumentResp,
    UpdateDocumentNameReq,
    GetDocumentsWithPageReq,
    GetDocumentsWithPageResp,
    UpdateDocumentEnabledReq
)
from internal.service import DocumentService
from pkg.paginator import PageModel
from pkg.response import validate_error_json, success_json, success_message


@inject
@dataclass
class DocumentHandler:
    document_service: DocumentService

    @login_required
    def create_document(self, dataset_id: UUID):
        req = CreateDocumentsReq()
        if not req.validate():
            return validate_error_json(req.errors)
        documents, batch = self.document_service.create_documents(dataset_id, **req.data, account=current_user)
        resp = CreateDocumentResp()
        return success_json(resp.dump((documents, batch)))

    @login_required
    def get_document(self, dataset_id: UUID, document_id: UUID):
        document = self.document_service.get_document(dataset_id, document_id, account=current_user)
        resp = GetDocumentResp()
        return success_json(resp.dump(document))

    @login_required
    def update_document_name(self, dataset_id: UUID, document_id: UUID):
        req = UpdateDocumentNameReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document(dataset_id, document_id, account=current_user, name=req.name.data)
        return success_message("更新文档名称成功")

    @login_required
    def update_document_enabled(self, dataset_id: UUID, document_id: UUID):
        req = UpdateDocumentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document_enabled(dataset_id, document_id,
                                                      enabled=req.enabled.data,
                                                      account=current_user)
        return success_message("更新文档状态成功")

    @login_required
    def delete_document(self, dataset_id: UUID, document_id: UUID):
        self.document_service.delete_document(dataset_id, document_id, account=current_user)
        return success_message("删除文档成功")

    @login_required
    def get_document_with_page(self, dataset_id: UUID):
        req = GetDocumentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        documents, paginator = self.document_service.get_document_with_page(dataset_id, req, account=current_user)
        resp = GetDocumentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(documents), paginator=paginator))

    @login_required
    def get_documents_status(self, dataset_id: UUID, batch: str):
        documents_status = self.document_service.get_documents_status(dataset_id, batch, account=current_user)
        return success_json(documents_status)
