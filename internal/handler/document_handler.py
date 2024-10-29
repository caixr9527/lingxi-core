#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/21 23:16
@Author : rxccai@gmail.com
@File   : document_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from flask import request
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

    def create_document(self, dataset_id: UUID):
        req = CreateDocumentsReq()
        if not req.validate():
            return validate_error_json(req.errors)
        documents, batch = self.document_service.create_documents(dataset_id, **req.data)
        resp = CreateDocumentResp()
        return success_json(resp.dump((documents, batch)))

    def get_document(self, dataset_id: UUID, document_id: UUID):
        document = self.document_service.get_document(dataset_id, document_id)
        resp = GetDocumentResp()
        return success_json(resp.dump(document))

    def update_document_name(self, dataset_id: UUID, document_id: UUID):
        req = UpdateDocumentNameReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document(dataset_id, document_id, name=req.name.data)
        return success_message("更新文档名称成功")

    def update_document_enabled(self, dataset_id: UUID, document_id: UUID):
        req = UpdateDocumentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)
        self.document_service.update_document_enabled(dataset_id, document_id, enabled=req.enabled.data)
        return success_message("更新文档状态成功")

    def get_document_with_page(self, dataset_id: UUID):
        req = GetDocumentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        documents, paginator = self.document_service.get_document_with_page(dataset_id, req)
        resp = GetDocumentsWithPageResp(many=True)
        return success_json(PageModel(list=resp.dump(documents), paginator=paginator))

    def get_documents_status(self, dataset_id: UUID, batch: str):
        documents_status = self.document_service.get_documents_status(dataset_id, batch)
        return success_json(documents_status)
