#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:41
@Author : rxccai@gmail.com
@File   : app.py
"""
import dotenv
from flask_migrate import Migrate
from injector import Injector

from config import Config
from internal.router import Router
from internal.server.http import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import ExtensionModule

# 将env加载到环境变量中
dotenv.load_dotenv()

conf = Config()

injector = Injector([ExtensionModule])

app = Http(__name__,
           conf=conf,
           db=injector.get(SQLAlchemy),
           migrate=injector.get(Migrate),
           router=injector.get(Router))

celery = app.extensions["celery"]
if __name__ == "__main__":
    app.run(debug=True)
