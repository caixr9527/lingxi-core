#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/30 22:43
@Author : rxccai@gmail.com
@File   : app_service.py
"""
import uuid
from dataclasses import dataclass

from flask_sqlalchemy import SQLAlchemy
from injector import inject

from internal.model import App


@inject
@dataclass
class AppService:
    """应用服务器逻辑"""
    db: SQLAlchemy

    def create_app(self) -> App:
        # 1.创建实体类
        app = App()
        app.account_id = uuid.uuid4()
        app.name = "测试机器人"
        app.icon = ""
        app.description = "这是一个简单到聊天机器人"
        # 2.将实体类添加到session会话中
        self.db.session.add(app)
        # 3.提交session会话
        self.db.session.commit()
        return app

    def get_app(self, id: uuid.UUID) -> App:
        return self.db.session.query(App).get(id)

    def update_app(self, id: uuid.UUID) -> App:
        app = self.get_app(id)
        app.name = "红皇后聊天机器人"
        self.db.session.commit()
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        app = self.get_app(id)
        self.db.session.delete(app)
        self.db.session.commit()
        return app
