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
@Time   : 2025/1/9 21:33
@Author : rxccai@gmail.com
@File   : tool_node.py.py
"""
import json
import time
from typing import Optional, Any

from langchain_core.pydantic_v1 import PrivateAttr
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from internal.core.tools.api_tools.entites import ToolEntity
from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.exception import FailException, NotFoundException
from internal.model import ApiTool
from .tool_entity import ToolNodeData


class ToolNode(BaseNode):
    """扩展插件节点"""
    node_data: ToolNodeData
    _tool: BaseTool = PrivateAttr(None)

    def __init__(self, *args: Any, **kwargs: Any):
        """构造函数，完成对内置工具的初始化"""
        # 调用父类构造函数完成数据初始化
        super().__init__(*args, **kwargs)

        # 导入依赖注入及工具提供者
        from app.http.module import injector

        # 判断是内置插件还是API插件，执行不同的操作
        if self.node_data.tool_type == "builtin_tool":
            from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
            builtin_provider_manager = injector.get(BuiltinProviderManager)

            # 调用内置提供者获取内置插件
            _tool = builtin_provider_manager.get_tool(self.node_data.provider_id, self.node_data.tool_id)
            if not _tool:
                raise NotFoundException("该内置插件扩展不存在，请核实后重试")

            self._tool = _tool(**self.node_data.params)
        else:
            # API插件，调用数据库查询记录并创建API插件
            from pkg.sqlalchemy import SQLAlchemy
            db = injector.get(SQLAlchemy)

            # 根据传递的提供者名字+工具名字查询工具
            api_tool = db.session.query(ApiTool).filter(
                ApiTool.provider_id == self.node_data.provider_id,
                ApiTool.name == self.node_data.tool_id
            ).one_or_none()
            if not api_tool:
                raise NotFoundException("该API扩展插件不存在，请核实重试")

            # 导入API插件提供者
            from internal.core.tools.api_tools.providers import ApiProviderManager
            api_provider_manager = injector.get(ApiProviderManager)

            # 创建API工具提供者并赋值
            self._tool = api_provider_manager.get_tool(ToolEntity(
                id=str(api_tool.id),
                name=api_tool.name,
                url=api_tool.url,
                method=api_tool.method,
                description=api_tool.description,
                headers=api_tool.provider.headers,
                parameters=api_tool.parameters,
            ))

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """扩展插件执行节点，根据传递的信息调用预设的插件，涵盖内置插件及API插件"""
        # 提取节点中的输入数据
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)

        # 调用插件并获取结果
        try:
            result = self._tool.invoke(inputs_dict)
        except Exception as e:
            raise FailException("扩展插件执行失败，请稍后尝试")

        # 检测result是否为字符串，如果不是则转换
        if not isinstance(result, str):
            result = json.dumps(result)

        # 提取并构建输出数据结构
        outputs = {}
        if self.node_data.outputs:
            outputs[self.node_data.outputs[0].name] = result
        else:
            outputs["text"] = result

        # 构建响应状态并返回
        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs=outputs,
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
