#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:39
@Author : rxccai@gmail.com
@File   : http.py
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config
from internal.exception import CustomException
from internal.router import Router
from pkg.response import Response, json, HttpCode


class Http(Flask):
    """Http服务引擎"""

    def __init__(self, *args, conf: Config, db: SQLAlchemy, router: Router, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化配置
        self.config.from_object(conf)
        # 注册绑定异常错误处理
        self.register_error_handler(Exception, self._register_error_handler)
        # 注册应用路由
        router.register_router(self)
        # 初始化flask扩展
        db.init_app(self)

    def _register_error_handler(self, error: Exception):
        # 判断是否自定义异常
        if isinstance(error, CustomException):
            return json(Response(
                code=error.code,
                message=error.message,
                data=error.data if error.data is not None else {}
            ))
        if self.debug or os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            # 非自定义异常
            return json(Response(code=HttpCode.FAIL,
                                 message=str(error),
                                 data={}))
