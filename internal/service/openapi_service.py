#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/12/29 15:01
@Author : rxccai@gmail.com
@File    : openapi_service.py
"""
from dataclasses import dataclass

from injector import inject

from internal.model import Account
from internal.schema.openapi_schema import OpenAPIChatReq
from pkg.sqlalchemy import SQLAlchemy
from .app_service import AppService
from .base_service import BaseService
from .conversation_service import ConversationService
from .retrieval_service import RetrievalService


@inject
@dataclass
class OpenAPIService(BaseService):
    """开放API服务"""
    db: SQLAlchemy
    app_service: AppService
    retrieval_service: RetrievalService
    conversation_service: ConversationService

    def chat(self, req: OpenAPIChatReq, account: Account):
        pass
