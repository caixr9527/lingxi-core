#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:30
@Author : rxccai@gmail.com
@File   : router.py
"""
from dataclasses import dataclass

from flask import Flask, Blueprint
from injector import inject

from internal.handler import (
    AppHandler,
    BuiltinToolHandler,
    ApiToolHandler,
    UploadFileHandler,
    DatasetHandler,
    DocumentHandler,
    SegmentHandler,
    OAuthHandler,
    AccountHandler,
    AuthHandler,
)


@inject
@dataclass
class Router:
    """路由"""
    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler
    upload_file_handler: UploadFileHandler
    dataset_handler: DatasetHandler
    document_handler: DocumentHandler
    segment_handler: SegmentHandler
    oauth_handler: OAuthHandler
    account_handler: AccountHandler
    auth_handler: AuthHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1.创建蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")
        # 2.将url与对应的控制器绑定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule("/apps", methods=["POST"], view_func=self.app_handler.create_app)
        bp.add_url_rule("/apps/<uuid:app_id>", view_func=self.app_handler.get_app)
        bp.add_url_rule("/apps/<uuid:app_id>/draft-app-config", view_func=self.app_handler.get_draft_app_config)
        bp.add_url_rule("/apps/<uuid:app_id>/draft-app-config", methods=["POST"],
                        view_func=self.app_handler.update_draft_app_config)

        # 3.内置插件广场模块
        bp.add_url_rule("/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools)
        bp.add_url_rule("/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
                        view_func=self.builtin_tool_handler.get_provider_tool)

        bp.add_url_rule("/builtin-tools/<string:provider_name>/icon",
                        view_func=self.builtin_tool_handler.get_provider_icon)
        bp.add_url_rule("/builtin-tools/categories", view_func=self.builtin_tool_handler.get_categories)

        # 自定义api插件模块
        bp.add_url_rule(
            "/api-tools",
            view_func=self.api_tool_handler.get_api_tool_providers_with_page
        )
        bp.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["POST"],
            view_func=self.api_tool_handler.validate_openapi_schema
        )
        bp.add_url_rule(
            "/api-tools",
            methods=["POST"],
            view_func=self.api_tool_handler.create_api_tool_provider,
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            view_func=self.api_tool_handler.get_api_tool_provider
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>",
            methods=["POST"],
            view_func=self.api_tool_handler.update_api_tool_provider
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/tools/<string:tool_name>",
            view_func=self.api_tool_handler.get_api_tool
        )
        bp.add_url_rule(
            "/api-tools/<uuid:provider_id>/delete",
            methods=["POST"],
            view_func=self.api_tool_handler.delete_api_tool_provider
        )

        # 上传文件模块
        bp.add_url_rule("/upload-files/file", methods=["POST"], view_func=self.upload_file_handler.upload_file)
        bp.add_url_rule("/upload-files/image", methods=["POST"], view_func=self.upload_file_handler.upload_image)

        # 知识库模块
        bp.add_url_rule("/datasets", view_func=self.dataset_handler.get_datasets_with_page)
        bp.add_url_rule("/datasets", methods=["POST"], view_func=self.dataset_handler.create_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", view_func=self.dataset_handler.get_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>", methods=["POST"], view_func=self.dataset_handler.update_dataset)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/queries", view_func=self.dataset_handler.get_dataset_queries)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/delete", methods=["POST"],
                        view_func=self.dataset_handler.delete_dataset)
        bp.add_url_rule("/datasets/embeddings", view_func=self.dataset_handler.embeddings_query)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents", view_func=self.document_handler.get_document_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents",
                        methods=["POST"],
                        view_func=self.document_handler.create_document)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>",
                        view_func=self.document_handler.get_document)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/name",
                        methods=["POST"],
                        view_func=self.document_handler.update_document_name)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/enabled",
                        methods=["POST"],
                        view_func=self.document_handler.update_document_enabled)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/delete",
                        methods=["POST"],
                        view_func=self.document_handler.delete_document)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/batch/<string:batch>",
                        view_func=self.document_handler.get_documents_status)

        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
                        view_func=self.segment_handler.get_segment_with_page)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments",
                        methods=["POST"],
                        view_func=self.segment_handler.create_segment)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
                        view_func=self.segment_handler.get_segment)
        bp.add_url_rule("/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/enabled",
                        methods=["POST"],
                        view_func=self.segment_handler.update_segment_enabled)
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>",
            methods=["POST"],
            view_func=self.segment_handler.update_segment,
        )
        bp.add_url_rule(
            "/datasets/<uuid:dataset_id>/documents/<uuid:document_id>/segments/<uuid:segment_id>/delete",
            methods=["POST"],
            view_func=self.segment_handler.delete_segment,
        )
        bp.add_url_rule("/datasets/<uuid:dataset_id>/hit", methods=["POST"], view_func=self.dataset_handler.hit)

        # 授权认证模块路由
        bp.add_url_rule("/oauth/<string:provider_name>", view_func=self.oauth_handler.provider)
        bp.add_url_rule(
            "/oauth/authorize/<string:provider_name>",
            methods=["POST"],
            view_func=self.oauth_handler.authorize)

        bp.add_url_rule("/auth/password-login",
                        methods=["POST"],
                        view_func=self.auth_handler.password_login)
        bp.add_url_rule("/auth/logout",
                        methods=["POST"],
                        view_func=self.auth_handler.logout)

        # 账号模块
        bp.add_url_rule("/account", view_func=self.account_handler.get_current_user)
        bp.add_url_rule("/account/password", methods=["POST"], view_func=self.account_handler.update_password)
        bp.add_url_rule("/account/name", methods=["POST"], view_func=self.account_handler.update_name)
        bp.add_url_rule("/account/avatar", methods=["POST"], view_func=self.account_handler.update_avatar)

        # 4.应用上注册蓝图
        app.register_blueprint(bp)
