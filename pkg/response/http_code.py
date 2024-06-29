#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/29 21:45
@Author : rxccai@gmail.com
@File   : http_code.py
"""
from enum import Enum


class HttpCode(str, Enum):
    """HTTP基础业务状态码"""
    SUCCESS = "success"
    FAIL = "fail"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    VALIDATE_ERROR = "validate_error"
