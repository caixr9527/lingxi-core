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
@Time   : 2025/4/16 20:42
@Author : caixiaorong01@outlook.com
@File   : iteration_node.py.py
"""
import json
import logging
import time
from typing import Optional, Any

from langchain_core.runnables import RunnableConfig

from internal.core.workflow.entities.node_entity import NodeResult, NodeStatus
from internal.core.workflow.entities.workflow_entity import WorkflowState, WorkflowConfig
from internal.core.workflow.nodes import BaseNode
from internal.core.workflow.utils.helper import extract_variables_from_state
from internal.entity.workflow_entity import WorkflowStatus
from internal.model import Workflow
from .iteration_entity import IterationNodeData


class IterationNode(BaseNode):
    """迭代节点"""
    node_data: IterationNodeData
    workflow: Any = None

    def __init__(self, *args: Any, **kwargs: Any):
        """构造函数，完成数据的初始化"""
        try:
            # 调用父类构造函数完成数据初始化
            super().__init__(*args, **kwargs)

            # 判断是否传递的工作流id
            if len(self.node_data.workflow_ids) != 1:
                self.workflow = None
            else:
                # 导入依赖注入及相关服务
                from app.http.module import injector
                from pkg.sqlalchemy import SQLAlchemy

                db = injector.get(SQLAlchemy)
                workflow_record = db.session.query(Workflow).get(self.node_data.workflow_ids[0])

                # 判断工作流是否存在并且已发布
                if not workflow_record or workflow_record.status != WorkflowStatus.PUBLISHED:
                    self.workflow = None
                else:
                    # 已发布且存在，则构建工作流并存储
                    from internal.core.workflow import Workflow as WorkflowTool
                    self.workflow = WorkflowTool(
                        workflow_config=WorkflowConfig(
                            account_id=workflow_record.account_id,
                            name="iteration_workflow",
                            description=self.node_data.description,
                            nodes=workflow_record.graph.get("nodes", []),
                            edges=workflow_record.graph.get("edges", [])
                        ),
                    )
        except Exception as error:
            # 出现异常则将工作流重置为空，使用相对宽松的校验范式
            logging.error("迭代节点子工作流构建失败: %(error)s", {"error": error}, exc_info=True)
            self.workflow = None

    def invoke(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """迭代节点调用函数，循环遍历将工作流的结果进行输出"""
        # 提取节点输入变量字典映射
        start_at = time.perf_counter()
        inputs_dict = extract_variables_from_state(self.node_data.inputs, state)
        inputs = inputs_dict.get("inputs", [])

        # 异常检测，涵盖工作流不存在、工作流输入参数不唯一、数据为非列表、长度为0等
        if (
                self.workflow is None
                or len(self.workflow.args) != 1
                or not isinstance(inputs, list)
                or len(inputs) == 0
        ):
            return {
                "node_results": [
                    NodeResult(
                        node_data=self.node_data,
                        status=NodeStatus.FAILED,
                        inputs=inputs_dict,
                        outputs={"outputs": []},
                        latency=(time.perf_counter() - start_at),
                    )
                ]
            }

        # 获取工作流的输入字段结构
        param_key = list(self.workflow.args.keys())[0]

        # 工作流+数据均存在，则循环遍历输入数据调用迭代工作流获取结果
        outputs = []
        for item in inputs:
            # 构建输入字典信息
            data = {param_key: item}

            # 调用工作流获取结果，这里可以修改为并行执行提升效率，得到的结构转换成字符串
            iteration_result = self.workflow.invoke(data)
            outputs.append(json.dumps(iteration_result, ensure_ascii=False))

        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCEEDED,
                    inputs=inputs_dict,
                    outputs={"outputs": outputs},
                    latency=(time.perf_counter() - start_at),
                )
            ]
        }
