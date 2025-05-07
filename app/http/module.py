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
@Time   : 2024/6/30 17:50
@Author : caixiaorong01@outlook.com
@File   : module.py
"""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_weaviate import FlaskWeaviate
from injector import Injector
from injector import Module, Binder
from redis import Redis

from internal.extension.database_extension import db
from internal.extension.login_extension import login_manager
from internal.extension.migrate_extension import migrate
from internal.extension.redis_extension import redis_client
from internal.extension.weaviate_extension import weaviate
from pkg.sqlalchemy import SQLAlchemy


class ExtensionModule(Module):
    """扩展模块的依赖注入"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(FlaskWeaviate, to=weaviate)
        binder.bind(Migrate, to=migrate)
        binder.bind(Redis, to=redis_client)
        binder.bind(LoginManager, to=login_manager)


injector = Injector([ExtensionModule])
