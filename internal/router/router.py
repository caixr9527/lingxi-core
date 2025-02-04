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
    AIHandler,
    ApiKeyHandler,
    OpenAPIHandler,
    BuiltinAppHandler,
    WorkflowHandler,
    LanguageModelHandler
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
    ai_handler: AIHandler
    api_key_handler: ApiKeyHandler
    open_api_handler: OpenAPIHandler
    builtin_app_handler: BuiltinAppHandler
    workflow_handler: WorkflowHandler
    language_model_handler: LanguageModelHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1.创建蓝图
        bp = Blueprint("llmops", __name__, url_prefix="")
        openapi_bp = Blueprint("openapi", __name__, url_prefix="")
        # 2.将url与对应的控制器绑定
        bp.add_url_rule("/ping", view_func=self.app_handler.ping)
        bp.add_url_rule("/apps", view_func=self.app_handler.get_apps_with_page)
        bp.add_url_rule("/apps", methods=["POST"], view_func=self.app_handler.create_app)
        bp.add_url_rule("/apps/<uuid:app_id>", view_func=self.app_handler.get_app)
        bp.add_url_rule("/apps/<uuid:app_id>", methods=["POST"], view_func=self.app_handler.update_app)
        bp.add_url_rule("/apps/<uuid:app_id>/delete", methods=["POST"], view_func=self.app_handler.delete_app)
        bp.add_url_rule("/apps/<uuid:app_id>/copy", methods=["POST"], view_func=self.app_handler.copy_app)
        bp.add_url_rule("/apps/<uuid:app_id>/draft-app-config", view_func=self.app_handler.get_draft_app_config)
        bp.add_url_rule("/apps/<uuid:app_id>/draft-app-config", methods=["POST"],
                        view_func=self.app_handler.update_draft_app_config)
        bp.add_url_rule("/apps/<uuid:app_id>/publish", methods=["POST"],
                        view_func=self.app_handler.publish)
        bp.add_url_rule("/apps/<uuid:app_id>/cancel-publish", methods=["POST"],
                        view_func=self.app_handler.cancel_publish)
        bp.add_url_rule("/apps/<uuid:app_id>/publish-histories",
                        view_func=self.app_handler.get_publish_histories_with_page)
        bp.add_url_rule("/apps/<uuid:app_id>/fallback-history", methods=["POST"],
                        view_func=self.app_handler.fallback_history_to_draft)
        bp.add_url_rule("/apps/<uuid:app_id>/summary",
                        view_func=self.app_handler.get_debug_conversation_summary)
        bp.add_url_rule("/apps/<uuid:app_id>/summary", methods=["POST"],
                        view_func=self.app_handler.update_debug_conversation_summary)
        bp.add_url_rule("/apps/<uuid:app_id>/conversations/delete-debug-conversation", methods=["POST"],
                        view_func=self.app_handler.delete_debug_conversation)
        bp.add_url_rule("/apps/<uuid:app_id>/conversations", methods=["POST"],
                        view_func=self.app_handler.debug_chat)
        bp.add_url_rule("/apps/<uuid:app_id>/conversations/tasks/<uuid:task_id>/stop", methods=["POST"],
                        view_func=self.app_handler.stop_debug)
        bp.add_url_rule("/apps/<uuid:app_id>/conversations/messages",
                        view_func=self.app_handler.get_debug_conversation_messages_with_page)

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

        # ai辅助模块
        bp.add_url_rule("/ai/optimize-prompt", methods=["POST"], view_func=self.ai_handler.optimize_prompt)
        bp.add_url_rule("/ai/suggested-questions", methods=["POST"],
                        view_func=self.ai_handler.generate_suggested_questions)

        # API秘钥模块
        bp.add_url_rule("/openapi/api-keys", view_func=self.api_key_handler.get_api_keys_with_page)
        bp.add_url_rule(
            "/openapi/api-keys",
            methods=["POST"],
            view_func=self.api_key_handler.create_api_key,
        )
        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>",
            methods=["POST"],
            view_func=self.api_key_handler.update_api_key,
        )
        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>/is-active",
            methods=["POST"],
            view_func=self.api_key_handler.update_api_key_is_active,
        )
        bp.add_url_rule(
            "/openapi/api-keys/<uuid:api_key_id>/delete",
            methods=["POST"],
            view_func=self.api_key_handler.delete_api_key,
        )
        openapi_bp.add_url_rule("/openapi/chat", methods=["POST"],
                                view_func=self.open_api_handler.chat, )

        # 内置应用模块
        bp.add_url_rule("/builtin-apps/categories", view_func=self.builtin_app_handler.get_builtin_app_categories)
        bp.add_url_rule("/builtin-apps", view_func=self.builtin_app_handler.get_builtin_apps)
        bp.add_url_rule(
            "/builtin-apps/add-builtin-app-to-space",
            methods=["POST"],
            view_func=self.builtin_app_handler.add_builtin_app_to_space,
        )

        # 工作流模块
        bp.add_url_rule("/workflows", view_func=self.workflow_handler.get_workflows_with_page)
        bp.add_url_rule("/workflows", methods=["POST"], view_func=self.workflow_handler.create_workflow)
        bp.add_url_rule("/workflows/<uuid:workflow_id>", view_func=self.workflow_handler.get_workflow)
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>",
            methods=["POST"],
            view_func=self.workflow_handler.update_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/delete",
            methods=["POST"],
            view_func=self.workflow_handler.delete_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/draft-graph",
            methods=["POST"],
            view_func=self.workflow_handler.update_draft_graph,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/draft-graph",
            view_func=self.workflow_handler.get_draft_graph,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/debug",
            methods=["POST"],
            view_func=self.workflow_handler.debug_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/publish",
            methods=["POST"],
            view_func=self.workflow_handler.publish_workflow,
        )
        bp.add_url_rule(
            "/workflows/<uuid:workflow_id>/cancel-publish",
            methods=["POST"],
            view_func=self.workflow_handler.cancel_publish_workflow,
        )

        # 语言模型模块
        bp.add_url_rule("/language-models", view_func=self.language_model_handler.get_language_models)
        bp.add_url_rule(
            "/language-models/<string:provider_name>/icon",
            view_func=self.language_model_handler.get_language_model_icon,
        )
        bp.add_url_rule(
            "/language-models/<string:provider_name>/<string:model_name>",
            view_func=self.language_model_handler.get_language_model,
        )
        # 4.应用上注册蓝图
        app.register_blueprint(bp)
        app.register_blueprint(openapi_bp)
