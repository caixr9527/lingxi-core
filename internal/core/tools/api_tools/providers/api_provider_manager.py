#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/9 20:30
@Author : rxccai@gmail.com
@File   : api_provider_manager.py
"""
from dataclasses import dataclass
from typing import Type, Optional, Callable

import requests
from injector import inject
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model, Field

from internal.core.tools.api_tools.entites import ToolEntity, ParameterTypeMap, ParameterIn


@inject
@dataclass
class ApiProviderManager(BaseModel):

    @classmethod
    def _create_tool_func_from_tool_entity(cls, tool_entity: ToolEntity) -> Callable:
        def tool_func(**kwargs) -> str:
            parameters = {
                ParameterIn.PATH: {},
                ParameterIn.HEADER: {},
                ParameterIn.QUERY: {},
                ParameterIn.COOKIE: {},
                ParameterIn.REQUEST_BODY: {},
            }
            parameter_map = {parameter.get("name"): parameter for parameter in tool_entity.parameters}
            header_map = {header.get("key"): header.get("value") for header in tool_entity.headers}
            for key, value in kwargs.items():
                parameter = parameter_map.get(key)
                if parameter is None:
                    continue
                parameters[parameter.get("in", ParameterIn.QUERY)][key] = value
            return requests.request(
                method=tool_entity.method,
                url=tool_entity.url.format(**parameters[ParameterIn.PATH]),
                params=parameters[ParameterIn.QUERY],
                json=parameters[ParameterIn.REQUEST_BODY],
                headers={**header_map, **parameters[ParameterIn.HEADER]},
                cookies=parameters[ParameterIn.COOKIE],
            ).text

        return tool_func

    @classmethod
    def _create_model_from_parameters(cls, parameters: list[dict]) -> Type[BaseModel]:
        """根据传递的parameters参数创建BaseModel子类"""

        fields = {}
        for parameter in parameters:
            field_name = parameter.get("name")
            field_type = ParameterTypeMap.get(parameter.get("type"), str)
            filed_required = parameter.get("required", True)
            field_description = parameter.get("description", "")
            fields[field_name] = (
                field_type if filed_required else Optional[field_type],
                Field(description=field_description),
            )

        return create_model("DynamicModel", **fields)

    def get_tool(self, tool_entity: ToolEntity) -> BaseTool:
        return StructuredTool.from_function(
            func=self._create_tool_func_from_tool_entity(tool_entity),
            name=f"{tool_entity.id}_{tool_entity.name}",
            description=tool_entity.description,
            args_schema=self._create_model_from_parameters(tool_entity.parameters),
        )
