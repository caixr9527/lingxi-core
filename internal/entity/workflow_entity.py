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
@Time   : 2025/1/13 21:26
@Author : caixiaorong01@outlook.com
@File   : workflow_entity.py.py
"""
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态类型枚举"""
    DRAFT = "draft"
    PUBLISHED = "published"


class WorkflowResultStatus(str, Enum):
    """工作流运行结果状态"""
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# 工作流默认配置信息，默认添加一个空的工作流
DEFAULT_WORKFLOW_CONFIG = {
    "graph": {},
    "draft_graph": {
        "nodes": [],
        "edges": []
    },
}
