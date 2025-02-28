#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/28 20:41
@Author : rxccai@gmail.com
@File   : app.py
"""

import os

if os.environ.get("FLASK_DEBUG") == "0" or os.environ.get("FLASK_ENV") == "production":
    from gevent import monkey

    monkey.patch_all()
    import grpc.experimental.gevent

    grpc.experimental.gevent.init_gevent()

import dotenv
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_weaviate import FlaskWeaviate

from config import Config
from internal.middleware import Middleware
from internal.router import Router
from internal.server.http import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import injector

# 将env加载到环境变量中
dotenv.load_dotenv()

conf = Config()

app = Http(__name__,
           conf=conf,
           db=injector.get(SQLAlchemy),
           weaviate=injector.get(FlaskWeaviate),
           migrate=injector.get(Migrate),
           login_manager=injector.get(LoginManager),
           middleware=injector.get(Middleware),
           router=injector.get(Router))

celery = app.extensions["celery"]
if __name__ == "__main__":
    app.run(debug=True)
