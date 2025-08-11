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
@Time   : 2024/6/29 21:47
@Author : caixiaorong01@outlook.com
@File   : response.py
"""
from dataclasses import field, dataclass
from typing import Any, Union, Generator

from flask import jsonify, stream_with_context, Response as FlaskResponse

from pkg.response.http_code import HttpCode


@dataclass
class Response:
    """基础HTTP接口响应格式"""
    code: HttpCode = HttpCode.SUCCESS
    message: str = ""
    data: Any = field(default_factory=dict)


def json(data: Response = None):
    return jsonify(data), 200


def success_json(data: Any = None):
    """成功响应"""
    return json(Response(code=HttpCode.SUCCESS, message="", data=data))


def fail_json(data: Any = None):
    """失败响应"""
    return json(Response(code=HttpCode.FAIL, message="", data=data))


def validate_error_json(errors: dict = None):
    """数据验证错误响应"""
    first_key = next(iter(errors))
    if first_key is not None:
        msg = errors.get(first_key)[0]
    else:
        msg = ""
    return json(Response(code=HttpCode.VALIDATE_ERROR, message=msg, data=errors))


def message(code: HttpCode = None, msg: str = ""):
    """基础消息响应"""
    return json(Response(code=code, message=msg, data={}))


def success_message(msg: str = ""):
    """成功消息响应"""
    return message(code=HttpCode.SUCCESS, msg=msg)


def fail_message(msg: str = ""):
    """失败消息响应"""
    return message(code=HttpCode.FAIL, msg=msg)


def not_found_message(msg: str = ""):
    """未找到消息响应"""
    return message(code=HttpCode.NOT_FOUND, msg=msg)


def unauthorized_message(msg: str = ""):
    """未认证消息响应"""
    return message(code=HttpCode.UNAUTHORIZED, msg=msg)


def forbidden_message(msg: str = ""):
    """未授权消息响应"""
    return message(code=HttpCode.FORBIDDEN, msg=msg)


def compact_generate_response(response: Union[Response, Generator]) -> FlaskResponse:
    """统一合并处理块输出以及流式事件输出"""
    # 检测下是否为块输出(Response)
    if isinstance(response, Response):
        return json(response)
    else:
        # response格式为生成器，代表本次响应需要执行流式事件输出
        def generate() -> Generator:
            """构建generate函数，流式从response中获取数据"""
            yield from response

        # 返回携带上下文的流式事件输出
        return FlaskResponse(
            stream_with_context(generate()),
            status=200,
            mimetype="text/event-stream",
        )
