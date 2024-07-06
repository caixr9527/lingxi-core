#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/30 17:50
@Author : rxccai@gmail.com
@File   : module.py
"""
from flask_migrate import Migrate
from injector import Module, Binder

from internal.extension.database_extension import db
from internal.extension.migrate_extension import migrate
from pkg.sqlalchemy import SQLAlchemy


class ExtensionModule(Module):
    """扩展模块的依赖注入"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
