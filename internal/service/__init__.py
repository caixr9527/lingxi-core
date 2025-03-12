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
@Time   : 2024/6/27 22:02
@Author : rxccai@gmail.com
@File   : __init__.py.py
"""
from .account_service import AccountService
from .ai_service import AIService
from .analysis_service import AnalysisService
from .api_key_service import ApiKeyService
from .api_tool_service import ApiToolService
from .app_service import AppService
from .assistant_agent_service import AssistantAgentService
from .audio_service import AudioService
from .base_service import BaseService
from .builtin_app_service import BuiltinAppService
from .builtin_tool_service import BuiltinToolService
from .conversation_service import ConversationService
from .cos_service import CosService
from .dataset_service import DatasetService
from .document_service import DocumentService
from .embeddings_service import EmbeddingsService
from .faiss_service import FaissService
from .indexing_service import IndexingService
from .jieba_service import JiebaService
from .jwt_service import JwtService
from .keyword_table_service import KeywordTableService
from .language_model_service import LanguageModelService
from .oauth_service import OAuthService
from .openapi_service import OpenAPIService
from .platform_service import PlatformService
from .process_rule_service import ProcessRuleService
from .retrieval_service import RetrievalService
from .segment_service import SegmentService
from .upload_file_service import UploadFileService
from .vector_database_service import VectorDatabaseService
from .web_app_service import WebAppService
from .wechat_service import WechatService
from .workflow_service import WorkflowService

__all__ = [
    "AppService",
    "VectorDatabaseService",
    "BuiltinToolService",
    "ApiToolService",
    "BaseService",
    "UploadFileService",
    "CosService",
    "DatasetService",
    "EmbeddingsService",
    "JiebaService",
    "DocumentService",
    "IndexingService",
    "ProcessRuleService",
    "KeywordTableService",
    "SegmentService",
    "RetrievalService",
    "ConversationService",
    "JwtService",
    "AccountService",
    "OAuthService",
    "AIService",
    "ApiKeyService",
    "OpenAPIService",
    "BuiltinAppService",
    "WorkflowService",
    "LanguageModelService",
    "AssistantAgentService",
    "FaissService",
    "AnalysisService",
    "WebAppService",
    "AudioService",
    "PlatformService",
    "WechatService"
]
