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
@Time   : 2024/6/28 20:39
@Author : rxccai@gmail.com
@File   : http.py
"""
import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_weaviate import FlaskWeaviate

from config import Config
from internal.exception import CustomException
from internal.extension import logging_extension, redis_extension, celery_extension
from internal.middleware import Middleware
from internal.router import Router
from pkg.response import Response, json, HttpCode
from pkg.sqlalchemy import SQLAlchemy


class Http(Flask):
    """Http服务引擎"""

    def __init__(
            self,
            *args,
            conf: Config,
            db: SQLAlchemy,
            weaviate: FlaskWeaviate,
            migrate: Migrate,
            login_manager: LoginManager,
            middleware: Middleware,
            router: Router,
            **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化配置
        self.config.from_object(conf)
        # 注册绑定异常错误处理
        self.register_error_handler(Exception, self._register_error_handler)
        # 初始化flask扩展
        db.init_app(self)
        weaviate.init_app(self)
        migrate.init_app(self, db, directory="internal/migration")
        redis_extension.init_app(self)
        celery_extension.init_app(self)
        logging_extension.init_app(self)
        login_manager.init_app(self)
        # 跨域
        CORS(self, resources={
            r"/*": {
                "origins": "*",
                "supports_credentials": True,
                # "methods": ["GET", "POST"],
                # "allow_headers": ["Content-Type"],
            }
        })

        # 注册应用中间价
        login_manager.request_loader(middleware.request_loader)

        # 注册应用路由
        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        # 日志记录异常信息
        logging.error("An error occurred: %(error)s", {"error": error}, exc_info=True)
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
