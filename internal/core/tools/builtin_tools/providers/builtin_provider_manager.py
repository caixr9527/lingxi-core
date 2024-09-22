#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/19 22:02
@Author : rxccai@gmail.com
@File   : builtin_provider_manager.py
"""
import os.path
from typing import Any

import yaml
from injector import inject, singleton
from pydantic import BaseModel, Field

from internal.core.tools.builtin_tools.entities import ProviderEntity, Provider


@inject
@singleton
class BuiltinProviderManager(BaseModel):
    """工厂类"""
    provider_map: dict[str, Provider] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._get_provider_tool_map()

    def get_provider(self, provider_name: str) -> Provider:
        """根据名称获取Provider"""
        return self.provider_map.get(provider_name)

    def get_providers(self) -> list[Provider]:
        return list(self.provider_map.values())

    def get_provider_entities(self) -> list[ProviderEntity]:
        return [provider.provider_entity for provider in self.provider_map.values()]

    def get_tool(self, provider_name: str, tool_name: str) -> Any:
        """根据服务提供商名字+工具名字，来获取特定的工具实体"""
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        return provider.get_tool(tool_name)

    def _get_provider_tool_map(self):
        if self.provider_map:
            return

        current_path = os.path.abspath(__file__)
        providers_path = os.path.dirname(current_path)
        providers_yaml_path = os.path.join(providers_path, "providers.yaml")

        with open(providers_yaml_path, encoding="utf-8") as f:
            providers_yaml_data = yaml.safe_load(f)

        for idx, provider_data in enumerate(providers_yaml_data):
            provider_entity = ProviderEntity(**provider_data)
            self.provider_map[provider_entity.name] = Provider(
                name=provider_entity.name,
                position=idx + 1,
                provider_entity=provider_entity
            )
