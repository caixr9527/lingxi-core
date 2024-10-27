#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/21 23:16
@Author : rxccai@gmail.com
@File   : document_handler.py
"""
from dataclasses import dataclass
from uuid import UUID

from injector import inject

from internal.schema.document_schema import CreateDocumentsReq, CreateDocumentResp
from internal.service import DocumentService
from pkg.response import validate_error_json, success_json


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

    def get_documents_status(self, dataset_id: UUID, batch: str):
        documents_status = self.document_service.get_documents_status(dataset_id, batch)
        return success_json(documents_status)
