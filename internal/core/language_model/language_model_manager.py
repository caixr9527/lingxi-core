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
@Time   : 2025/1/23 20:22
@Author : caixiaorong01@outlook.com
@File   : language_model_manager.py.py
"""
import os.path
from typing import Any, Optional, Type

import yaml
from injector import inject, singleton
from langchain_core.pydantic_v1 import BaseModel, Field, root_validator

from internal.exception import NotFoundException
from .entities.model_entity import ModelType, BaseLanguageModel
from .entities.provider_entity import Provider, ProviderEntity


@inject
@singleton
class LanguageModelManager(BaseModel):
    """语言模型管理器"""
    provider_map: dict[str, Provider] = Field(default_factory=dict)  # 服务提供者映射

    @root_validator(pre=False)
    def validate_language_model_manager(cls, values: dict[str, Any]) -> dict[str, Any]:
        """使用pydantic提供的预设规则校验提供者映射，完成语言模型管理器的初始化"""
        # 获取当前类所在的路径
        current_path = os.path.abspath(__file__)
        providers_path = os.path.join(os.path.dirname(current_path), "providers")
        providers_yaml_path = os.path.join(providers_path, "providers.yaml")

        # 读取providers.yaml数据配置获取提供者列表
        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        # 循环读取服务提供者数据并配置模型信息
        values["provider_map"] = {}
        for index, provider_yaml_data in enumerate(providers_yaml_data):
            # 获取提供者实体数据结构，并构建服务提供者实体
            provider_entity = ProviderEntity(**provider_yaml_data)
            values["provider_map"][provider_entity.name] = Provider(
                name=provider_entity.name,
                position=index + 1,
                provider_entity=provider_entity,
            )
        return values

    def get_provider(self, provider_name: str) -> Optional[Provider]:
        """根据传递的提供者名字获取提供者"""
        provider = self.provider_map.get(provider_name, None)
        if provider is None:
            raise NotFoundException("该模型服务提供商不存在，请核实后重试")
        return provider

    def get_providers(self) -> list[Provider]:
        """获取所有提供者列表信息"""
        return list(self.provider_map.values())

    def get_model_class_by_provider_and_type(
            self,
            provider_name: str,
            model_type: ModelType,
    ) -> Optional[Type[BaseLanguageModel]]:
        """根据传递的提供者名字+模型类型，获取模型类"""
        provider = self.get_provider(provider_name)

        return provider.get_model_class(model_type)

    def get_model_class_by_provider_and_model(
            self,
            provider_name: str,
            model_name: str,
    ) -> Optional[Type[BaseLanguageModel]]:
        """根据传递的提供者名字+模型名字获取模型类"""
        provider = self.get_provider(provider_name)

        model_entity = provider.get_model_entity(model_name)

        return provider.get_model_class(model_entity.model_type)
