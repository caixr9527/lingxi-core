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
@Time   : 2025/3/22 10:44
@Author : caixiaorong01@outlook.com
@File   : langchain_core_utils__merge.py.py
"""
from typing import List, Optional

from langchain_core.utils._merge import merge_dicts


def merge_lists(left: Optional[List], *others: Optional[List]) -> Optional[List]:
    """
    重写langchain团队的merge_lists方法，解决在流式输出`工具调用消息时`返回的index为None时。
    一个`工具调用消息`会被拆分成多个，导致接口响应错误的问题。
    该功能直连openai官方没问题，所有中转接口可能因为使用的是Azure提供的服务，没及时更新导致有问题。
    直连响应块内容:
        content='' additional_kwargs={'tool_calls': [{'index': 0, 'id': 'call_eFerXQJL9isVRRXHkqPJ13bL', 'function': {'arguments': '', 'name': 'weather'}, 'type': 'function'}]} id='run-0873bc8d-2f87-47a8-943c-20e4a56aa9f8' tool_calls=[{'name': 'weather', 'args': {}, 'id': 'call_eFerXQJL9isVRRXHkqPJ13bL', 'type': 'tool_call'}] tool_call_chunks=[{'name': 'weather', 'args': '', 'id': 'call_eFerXQJL9isVRRXHkqPJ13bL', 'index': 0, 'type': 'tool_call_chunk'}]
    中转响应块内容:
        content='' additional_kwargs={'tool_calls': [{'index': None, 'id': 'call_eFerXQJL9isVRRXHkqPJ13bL', 'function': {'arguments': '', 'name': 'weather'}, 'type': 'function'}]} id='run-0873bc8d-2f87-47a8-943c-20e4a56aa9f8' tool_calls=[{'name': 'weather', 'args': {}, 'id': 'call_eFerXQJL9isVRRXHkqPJ13bL', 'type': 'tool_call'}] tool_call_chunks=[{'name': 'weather', 'args': '', 'id': 'call_eFerXQJL9isVRRXHkqPJ13bL', 'index': 0, 'type': 'tool_call_chunk'}]
    一个index是数值，一个是None
    """
    merged = left.copy() if left is not None else None
    for other in others:
        if other is None:
            continue
        elif merged is None:
            merged = other.copy()
        else:
            for e in other:
                # fix:为e["index"]新增一个类型判断，当类型为整型或者None时，直接合并
                if isinstance(e, dict) and "index" in e and (isinstance(e["index"], int) or e["index"] is None):
                    to_merge = [
                        i
                        for i, e_left in enumerate(merged)
                        if e_left["index"] == e["index"]
                    ]
                    if to_merge:
                        # handling for 'type'.
                        if "type" in e:
                            e = {k: v for k, v in e.items() if k != "type"}
                        merged[to_merge[0]] = merge_dicts(merged[to_merge[0]], e)
                    else:
                        merged.append(e)
                else:
                    merged.append(e)
    return merged
