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
@Time   : 2025/1/13 21:27
@Author : caixiaorong01@outlook.com
@File   : workflow_service.py
"""
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Generator
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.core.workflow import Workflow as WorkflowTool
from internal.core.workflow.entities.edge_entity import BaseEdgeData
from internal.core.workflow.entities.node_entity import NodeType, BaseNodeData
from internal.core.workflow.entities.workflow_entity import WorkflowConfig
from internal.core.workflow.nodes import (
    CodeNodeData,
    DatasetRetrievalNodeData,
    EndNodeData,
    HttpRequestNodeData,
    LLMNodeData,
    StartNodeData,
    TemplateTransformNodeData,
    ToolNodeData,
    QuestionClassifierNodeData,
    IterationNodeData,
    ConditionSelectNodeData,
)
from internal.entity.workflow_entity import WorkflowStatus, DEFAULT_WORKFLOW_CONFIG, WorkflowResultStatus
from internal.exception import ValidateException, NotFoundException, ForbiddenException, FailException
from internal.lib.helper import convert_model_to_dict
from internal.model import Account, Workflow, Dataset, ApiTool, WorkflowResult
from internal.schema.workflow_schema import CreateWorkflowReq, GetWorkflowsWithPageReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService


@inject
@dataclass
class WorkflowService(BaseService):
    """工作流服务"""
    db: SQLAlchemy
    builtin_provider_manager: BuiltinProviderManager

    def create_workflow(self, req: CreateWorkflowReq, account: Account) -> Workflow:
        """根据传递的请求信息创建工作流"""
        # 根据传递的工作流工具名称查询工作流信息
        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == req.tool_call_name.data.strip(),
            Workflow.account_id == account.id,
        ).one_or_none()
        if check_workflow:
            raise ValidateException(f"在当前账号下已创建[{req.tool_call_name.data}]工作流，不支持重名")

        # 调用数据库服务创建工作流
        return self.create(Workflow, **{
            **req.data,
            **DEFAULT_WORKFLOW_CONFIG,
            "account_id": account.id,
            "is_debug_passed": False,
            "status": WorkflowStatus.DRAFT,
            "tool_call_name": req.tool_call_name.data.strip(),
        })

    def get_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """根据传递的工作流id，获取指定的工作流基础信息"""
        # 查询数据库获取工作流基础信息
        workflow = self.get(Workflow, workflow_id)

        # 判断工作流是否存在
        if not workflow:
            raise NotFoundException("该工作流不存在，请核实后重试")

        # 判断当前账号是否有权限访问该应用
        if workflow.account_id != account.id:
            raise ForbiddenException("当前账号无权限访问该应用，请核实后尝试")

        return workflow

    def delete_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """根据传递的工作流id+账号信息，删除指定的工作流"""
        # 获取工作流基础信息并校验权限
        workflow = self.get_workflow(workflow_id, account)

        # 删除工作流
        self.delete(workflow)

        return workflow

    def update_workflow(self, workflow_id: UUID, account: Account, **kwargs) -> Workflow:
        """根据传递的工作流id+请求更新工作流基础信息"""
        # 获取工作流基础信息并校验权限
        workflow = self.get_workflow(workflow_id, account)

        # 根据传递的工具调用名字查询是否存在重名工作流
        check_workflow = self.db.session.query(Workflow).filter(
            Workflow.tool_call_name == kwargs.get("tool_call_name", "").strip(),
            Workflow.account_id == account.id,
            Workflow.id != workflow.id,
        ).one_or_none()
        if check_workflow:
            raise ValidateException(f"在当前账号下已创建[{kwargs.get('tool_call_name', '')}]工作流，不支持重名")

        # 更新工作流基础信息
        self.update(workflow, **kwargs)

        return workflow

    def get_workflows_with_page(
            self, req: GetWorkflowsWithPageReq, account: Account
    ) -> tuple[list[Workflow], Paginator]:
        """根据传递的信息获取工作流分页列表数据"""
        # 构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [Workflow.account_id == account.id]
        if req.search_word.data:
            filters.append(Workflow.name.ilike(f"%{req.search_word.data}%"))
        if req.status.data:
            filters.append(Workflow.status == req.status.data)

        # 分页查询数据
        workflows = paginator.paginate(
            self.db.session.query(Workflow).filter(*filters).order_by(desc("created_at"))
        )

        return workflows, paginator

    def update_draft_graph(self, workflow_id: UUID, draft_graph: dict[str, Any], account: Account) -> Workflow:
        """根据传递的工作流id+草稿图配置+账号更新工作流的草稿图"""
        # 根据传递的id获取工作流并校验权限
        workflow = self.get_workflow(workflow_id, account)

        # 校验传递的草稿图配置，因为有可能边有可能还未建立，所以需要校验关联的数据
        validate_draft_graph = self._validate_graph(workflow_id, draft_graph, account)

        # 更新工作流草稿图配置，每次修改都将is_debug_passed的值重置为False，该处可以优化对比字典里除position的其他属性
        self.update(workflow, **{
            "draft_graph": validate_draft_graph,
            "is_debug_passed": False,
        })

        return workflow

    def get_draft_graph(self, workflow_id: UUID, account: Account) -> dict[str, Any]:
        """根据传递的工作流id+账号信息，获取指定工作流的草稿配置信息"""
        workflow = self.get_workflow(workflow_id, account)

        # 提取草稿图结构信息并校验(不更新校验后的数据到数据库)
        draft_graph = workflow.draft_graph
        validate_draft_graph = self._validate_graph(workflow_id, draft_graph, account)

        # 循环遍历节点信息，为工具节点/知识库节点附加元数据
        for node in validate_draft_graph["nodes"]:
            if node.get("node_type") == NodeType.TOOL:
                # 判断工具的类型执行不同的操作
                if node.get("tool_type") == "builtin_tool":
                    # 节点类型为工具，则附加工具的名称、图标、参数等额外信息
                    provider = self.builtin_provider_manager.get_provider(node.get("provider_id"))
                    if not provider:
                        continue

                    # 获取提供者下的工具实体，并检测是否存在
                    tool_entity = provider.get_tool_entity(node.get("tool_id"))
                    if not tool_entity:
                        continue

                    # 判断工具的params和草稿中的params是否一致，如果不一致则全部重置为默认值（或者考虑删除这个工具的引用）
                    param_keys = set([param.name for param in tool_entity.params])
                    params = node.get("params")
                    if set(params.keys()) - param_keys:
                        params = {
                            param.name: param.default
                            for param in tool_entity.params
                            if param.default is not None
                        }

                    # 数据校验成功附加展示信息
                    provider_entity = provider.provider_entity
                    node["meta"] = {
                        "type": "builtin_tool",
                        "provider": {
                            "id": provider_entity.name,
                            "name": provider_entity.name,
                            "label": provider_entity.label,
                            "icon": f"builtin-tools/{provider_entity.name}/icon",
                            "description": provider_entity.description,
                        },
                        "tool": {
                            "id": tool_entity.name,
                            "name": tool_entity.name,
                            "label": tool_entity.label,
                            "description": tool_entity.description,
                            "params": params,
                        }
                    }
                elif node.get("tool_type") == "api_tool":
                    # 查询数据库获取对应的工具记录，并检测是否存在
                    tool_record = self.db.session.query(ApiTool).filter(
                        ApiTool.provider_id == node.get("provider_id"),
                        ApiTool.name == node.get("tool_id"),
                        ApiTool.account_id == account.id,
                    ).one_or_none()
                    if not tool_record:
                        continue

                    # 组装api工具展示信息
                    provider = tool_record.provider
                    node["meta"] = {
                        "type": "api_tool",
                        "provider": {
                            "id": str(provider.id),
                            "name": provider.name,
                            "label": provider.name,
                            "icon": provider.icon,
                            "description": provider.description,
                        },
                        "tool": {
                            "id": str(tool_record.id),
                            "name": tool_record.name,
                            "label": tool_record.name,
                            "description": tool_record.description,
                            "params": {},
                        },
                    }
                else:
                    node["meta"] = {
                        "type": "api_tool",
                        "provider": {
                            "id": "",
                            "name": "",
                            "label": "",
                            "icon": "",
                            "description": "",
                        },
                        "tool": {
                            "id": "",
                            "name": "",
                            "label": "",
                            "description": "",
                            "params": {},
                        },
                    }
            elif node.get("node_type") == NodeType.DATASET_RETRIEVAL:
                # 节点类型为知识库检索，需要附加知识库的名称、图标等信息
                datasets = self.db.session.query(Dataset).filter(
                    Dataset.id.in_(node.get("dataset_ids", [])),
                    Dataset.account_id == account.id,
                ).all()
                datasets = datasets[:5]
                node["dataset_ids"] = [str(dataset.id) for dataset in datasets]
                node["meta"] = {
                    "datasets": [{
                        "id": dataset.id,
                        "name": dataset.name,
                        "icon": dataset.icon,
                        "description": dataset.description,
                    } for dataset in datasets]
                }
                # 检查迭代节点工作流配置
            elif node.get("node_type") == NodeType.ITERATION:
                workflows = self.db.session.query(Workflow).filter(
                    Workflow.id.in_(node.get("workflow_ids", [])),
                    Workflow.account_id == account.id,
                    Workflow.status == WorkflowStatus.PUBLISHED,
                ).all()
                workflows = workflows[:1]
                node["workflow_ids"] = [str(workflow.id) for workflow in workflows]
                node["meta"] = {
                    "workflows": [{
                        "id": workflow.id,
                        "name": workflow.name,
                        "icon": workflow.icon,
                        "description": workflow.description,
                    } for workflow in workflows]
                }
        return validate_draft_graph

    def debug_workflow(self, workflow_id: UUID, inputs: dict[str, Any], account: Account) -> Generator:
        """调试指定的工作流API接口，该接口为流式事件输出"""
        # 根据传递的id获取工作流并校验权限
        workflow = self.get_workflow(workflow_id, account)

        # 创建工作流工具
        workflow_tool = WorkflowTool(workflow_config=WorkflowConfig(
            account_id=account.id,
            name=workflow.tool_call_name,
            description=workflow.description,
            nodes=workflow.draft_graph.get("nodes", []),
            edges=workflow.draft_graph.get("edges", []),
        ))

        def handle_stream() -> Generator:
            # 定义变量存储所有节点运行结果
            node_results = []

            # 添加数据库工作流运行结果记录
            workflow_result = self.create(WorkflowResult, **{
                "app_id": None,
                "account_id": account.id,
                "workflow_id": workflow.id,
                "graph": workflow.draft_graph,
                "state": [],
                "latency": 0,
                "status": WorkflowResultStatus.RUNNING,
            })

            # 调用stream服务获取工具信息
            start_at = time.perf_counter()
            try:
                for chunk in workflow_tool.stream(inputs):
                    # chunk的格式为:{"node_name": WorkflowState}，所以需要取出节点响应结构的第1个key
                    first_key = next(iter(chunk))
                    # 因为存在虚拟节点，所以需要判断是否执行当前循环
                    if len(chunk[first_key]["node_results"]) == 0:
                        continue

                    # 取出各个节点的运行结果
                    node_result = chunk[first_key]["node_results"][0]
                    node_result_dict = convert_model_to_dict(node_result)
                    node_results.append(node_result_dict)

                    # 组装响应数据并流式事件输出
                    data = {
                        "id": str(uuid.uuid4()),
                        **node_result_dict,
                    }
                    yield f"event: workflow\ndata: {json.dumps(data)}\n\n"

                # 流式输出完毕后，将结果存储到数据库中
                self.update(workflow_result, **{
                    "status": WorkflowResultStatus.SUCCEEDED,
                    "state": node_results,
                    "latency": (time.perf_counter() - start_at),
                })
                self.update(workflow, **{
                    "is_debug_passed": True,
                })
            except Exception as e:
                logging.exception("执行工作流发生错误, 错误信息: %(error)s", {"error": e})
                self.update(workflow_result, **{
                    "status": WorkflowResultStatus.FAILED,
                    "state": node_results,
                    "latency": (time.perf_counter() - start_at)
                })

        return handle_stream()

    def publish_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """根据传递的工作流id，发布指定的工作流"""
        workflow = self.get_workflow(workflow_id, account)

        # 校验工作流是否调试通过
        if workflow.is_debug_passed is False:
            raise FailException("该工作流未调试通过，请调试通过后发布")

        # 使用WorkflowConfig二次校验，如果校验失败则不发布
        try:
            WorkflowConfig(
                account_id=account.id,
                name=workflow.tool_call_name,
                description=workflow.description,
                nodes=workflow.draft_graph.get("nodes", []),
                edges=workflow.draft_graph.get("edges", []),
            )
        except Exception:
            self.update(workflow, **{
                "is_debug_passed": False,
            })
            raise ValidateException("工作流配置校验失败，请核实后重试")

        # 更新工作流的发布状态
        self.update(workflow, **{
            "graph": workflow.draft_graph,
            "status": WorkflowStatus.PUBLISHED,
            "is_debug_passed": False,
        })

        return workflow

    def cancel_publish_workflow(self, workflow_id: UUID, account: Account) -> Workflow:
        """取消发布指定的工作流"""
        workflow = self.get_workflow(workflow_id, account)

        # 校验工作流是否为已发布的状态
        if workflow.status != WorkflowStatus.PUBLISHED:
            raise FailException("该工作流未发布无法取消发布")

        # 更新发布状态并删除运行图草稿配置
        self.update(workflow, **{
            "graph": {},
            "status": WorkflowStatus.DRAFT,
            "is_debug_passed": False,
        })

        return workflow

    def _validate_graph(self, workflow_id: UUID, graph: dict[str, Any], account: Account) -> dict[str, Any]:
        """校验传递的graph信息，涵盖nodes和edges对应的数据，该函数使用相对宽松的校验方式，并且因为是草稿，不需要校验节点与边的关系"""
        # 提取nodes和edges数据
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # 构建节点类型与节点数据类映射
        node_data_classes = {
            NodeType.START: StartNodeData,
            NodeType.END: EndNodeData,
            NodeType.LLM: LLMNodeData,
            NodeType.TEMPLATE_TRANSFORM: TemplateTransformNodeData,
            NodeType.DATASET_RETRIEVAL: DatasetRetrievalNodeData,
            NodeType.CODE: CodeNodeData,
            NodeType.TOOL: ToolNodeData,
            NodeType.HTTP_REQUEST: HttpRequestNodeData,
            NodeType.QUESTION_CLASSIFIER: QuestionClassifierNodeData,
            NodeType.ITERATION: IterationNodeData,
            NodeType.CONDITION_SELECTOR: ConditionSelectNodeData,
        }

        # 循环校验nodes中各个节点对应的数据
        node_data_dict: dict[UUID, BaseNodeData] = {}
        start_nodes = 0
        end_nodes = 0
        for node in nodes:
            try:
                # 校验传递的node数据是不是字典，如果不是则跳过当前数据
                if not isinstance(node, dict):
                    raise ValidateException("工作流节点数据类型出错，请核实后重试")

                # 提取节点的node_type类型，并判断类型是否正确
                node_type = node.get("node_type", "")
                node_data_cls = node_data_classes.get(node_type, None)
                if node_data_cls is None:
                    raise ValidateException("工作流节点类型出错，请核实后重试")

                # 实例化节点数据类型，如果出错则跳过当前数据
                node_data = node_data_cls(**node)

                # 判断节点id是否唯一，如果不唯一，则将当前节点清除
                if node_data.id in node_data_dict:
                    raise ValidateException("工作流节点id必须唯一，请核实后重试")

                # 判断节点title是否唯一，如果不唯一，则将当前节点清除
                if any(item.title.strip() == node_data.title.strip() for item in node_data_dict.values()):
                    raise ValidateException("工作流节点title必须唯一，请核实后重试")

                # 对特殊节点进行判断，涵盖开始/结束/知识库检索/工具
                if node_data.node_type == NodeType.START:
                    if start_nodes >= 1:
                        raise ValidateException("工作流中只允许有1个开始节点")
                    start_nodes += 1
                elif node_data.node_type == NodeType.END:
                    if end_nodes >= 1:
                        raise ValidateException("工作流中只允许有1个结束节点")
                    end_nodes += 1
                elif node_data.node_type == NodeType.DATASET_RETRIEVAL:
                    # 剔除关联知识库列表中不属于当前账户的数据
                    datasets = self.db.session.query(Dataset).filter(
                        Dataset.id.in_(node_data.dataset_ids[:5]),
                        Dataset.account_id == account.id,
                    ).all()
                    node_data.dataset_ids = [dataset.id for dataset in datasets]
                # 判断类型为迭代节点，剔除不属于当前账户并且未发布的工作流
                elif node_data.node_type == NodeType.ITERATION:
                    workflows = self.db.session.query(Workflow).filter(
                        Workflow.id.in_(node_data.workflow_ids[:1]),
                        Workflow.account_id == account.id,
                        Workflow.status == WorkflowStatus.PUBLISHED,
                    ).all()
                    # 剔除当前工作流，迭代节点不能内嵌本身（todo 这块还可以继续升级，双方不能内嵌）
                    node_data.workflow_ids = [workflow.id for workflow in workflows if workflow.id != workflow_id]
                # 将数据添加到node_data_dict中
                node_data_dict[node_data.id] = node_data
            except Exception as e:
                logging.exception(str(e))
                continue

        # 循环校验edges中各个节点对应的数据
        edge_data_dict: dict[UUID, BaseEdgeData] = {}
        for edge in edges:
            try:
                # 边类型为非字典则抛出错误，否则转换成BaseEdgeData
                if not isinstance(edge, dict):
                    raise ValidateException("工作流边数据类型出错，请核实后重试")
                edge_data = BaseEdgeData(**edge)

                # 校验边edges的id是否唯一
                if edge_data.id in edge_data_dict:
                    raise ValidateException("工作流边数据id必须唯一，请核实后重试")

                # 校验边中的source/target/source_type/target_type必须和nodes对得上
                if (
                        edge_data.source not in node_data_dict
                        or edge_data.source_type != node_data_dict[edge_data.source].node_type
                        or edge_data.target not in node_data_dict
                        or edge_data.target_type != node_data_dict[edge_data.target].node_type
                ):
                    raise ValidateException("工作流边起点/终点对应的节点不存在或类型错误，请核实后重试")

                # 校验边Edges里的边必须唯一(source+target必须唯一)
                if any(
                        (item.source == edge_data.source
                         and item.target == edge_data.target
                         and item.source_handle_id == edge_data.source_handle_id)
                        for item in edge_data_dict.values()
                ):
                    raise ValidateException("工作流边数据不能重复添加")

                # 基础数据校验通过，将数据添加到edge_data_dict中
                edge_data_dict[edge_data.id] = edge_data
            except Exception:
                continue

        return {
            "nodes": [convert_model_to_dict(node_data) for node_data in node_data_dict.values()],
            "edges": [convert_model_to_dict(edge_data) for edge_data in edge_data_dict.values()],
        }
