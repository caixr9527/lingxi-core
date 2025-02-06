#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/1/23 22:25
@Author : rxccai@gmail.com
@File   : language_model_service.py.py
"""
import mimetypes
import os
from dataclasses import dataclass
from typing import Any

from flask import current_app
from injector import inject
from langchain_openai import ChatOpenAI

from internal.core.language_model import LanguageModelManager
from internal.core.language_model.entities.model_entity import BaseLanguageModel
from internal.exception import NotFoundException
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..lib.helper import convert_model_to_dict


@inject
@dataclass
class LanguageModelService(BaseService):
    """语言模型服务"""
    db: SQLAlchemy
    language_model_manager: LanguageModelManager

    def get_language_models(self) -> list[dict[str, Any]]:
        """获取LLMOps项目中的所有模型列表信息"""
        # 调用语言模型管理器获取提供商列表
        providers = self.language_model_manager.get_providers()

        # 构建语言模型列表，循环读取数据
        language_models = []
        for provider in providers:
            # 获取提供商实体和模型实体列表
            provider_entity = provider.provider_entity
            model_entities = provider.get_model_entities()

            # 构建响应字典结构
            language_model = {
                "name": provider_entity.name,
                "position": provider.position,
                "label": provider_entity.label,
                "icon": provider_entity.icon,
                "description": provider_entity.description,
                "background": provider_entity.background,
                "support_model_types": provider_entity.supported_model_types,
                "models": convert_model_to_dict(model_entities),
            }
            language_models.append(language_model)

        return language_models

    def get_language_model(self, provider_name: str, model_name: str) -> dict[str, Any]:
        """根据传递的提供者名字+模型名字获取模型详细信息"""
        # 获取提供者+模型实体信息
        provider = self.language_model_manager.get_provider(provider_name)
        if not provider:
            raise NotFoundException("该服务提供者不存在")

        # 获取模型实体
        model_entity = provider.get_model_entity(model_name)
        if not model_entity:
            raise NotFoundException("该模型不存在")

        return convert_model_to_dict(model_entity)

    def get_language_model_icon(self, provider_name: str) -> tuple[bytes, str]:
        """根据传递的提供者名字获取提供商对应的图标信息"""
        # 获取提供者信息
        provider = self.language_model_manager.get_provider(provider_name)
        if not provider:
            raise NotFoundException("该服务提供者不存在")

        # 获取项目的根路径信息
        root_path = os.path.dirname(os.path.dirname(current_app.root_path))

        # 拼接得到提供者所在的文件夹
        provider_path = os.path.join(
            root_path,
            "internal", "core", "language_model", "providers", provider_name,
        )

        # 拼接得到icon对应的路径
        icon_path = os.path.join(provider_path, "_asset", provider.provider_entity.icon)

        # 检测icon是否存在
        if not os.path.exists(icon_path):
            raise NotFoundException(f"该模型提供者_asset下未提供图标")

        # 读取icon的类型
        mimetype, _ = mimetypes.guess_type(icon_path)
        mimetype = mimetype or "application/octet-stream"

        # 读取icon的字节数据
        with open(icon_path, "rb") as f:
            byte_data = f.read()
            return byte_data, mimetype

    def load_language_model(self, model_config: dict[str, Any]) -> BaseLanguageModel:
        """根据配置加载大模型"""
        try:
            # 从model_config中提取出provider、model、parameters
            provider_name = model_config.get("provider", "")
            model_name = model_config.get("model", "")
            parameters = model_config.get("parameters", {})

            # 从模型管理器获取提供者、模型实体、模型类
            provider = self.language_model_manager.get_provider(provider_name)
            model_entity = provider.get_model_entity(model_name)
            model_class = provider.get_model_class(model_entity.model_type)

            # 实例化模型后并返回
            return model_class(
                **model_entity.attributes,
                **parameters,
                features=model_entity.features,
                metadata=model_entity.metadata,
            )
        except Exception as _:
            return self.load_default_language_model()

    @classmethod
    def load_default_language_model(cls) -> BaseLanguageModel:
        """加载默认的大语言模型，在模型管理器中获取不到模型或者出错时使用默认模型进行兜底"""
        return ChatOpenAI(model="gpt-4o-mini", temperature=1, max_tokens=8192)
