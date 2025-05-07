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
@Time   : 2024/6/29 23:07
@Author : caixiaorong01@outlook.com
@File   : exception.py
"""
from dataclasses import field
from typing import Any

from pkg.response import HttpCode


class CustomException(Exception):
    """基础自定义异常信息"""
    code: HttpCode = HttpCode.FAIL
    message: str = ""
    data: Any = field(default_factory=dict)

    def __init__(self, message: str = "", data: Any = None):
        super().__init__()
        self.message = message
        self.data = data


class FailException(CustomException):
    """通用失败异常"""
    pass


class NotFoundException(CustomException):
    """未找到异常"""
    code = HttpCode.NOT_FOUND


class UnauthorizedException(CustomException):
    """未认证异常"""
    code = HttpCode.UNAUTHORIZED


class ForbiddenException(CustomException):
    """未授权异常"""
    code = HttpCode.FORBIDDEN


class ValidateException(CustomException):
    """验证异常"""
    code = HttpCode.VALIDATE_ERROR
