#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/30 17:37
@Author : rxccai@gmail.com
@File   : default_config.py
"""
# 应用默认配置项
DEFAULT_CONFIG = {
    "WTF_CSRF_ENABLED": "True",
    # SQLAlchemy数据库配置
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",

    # Redis配置
    "REDIS_HOST": "127.0.0.1",
    "REDIS_PORT": 6379,
    "REDIS_USERNAME": "",
    "REDIS_PASSWORD": "",
    "REDIS_DB": "0",
    "REDIS_USE_SSL": "False",

    # weaviate向量数据库配置
    "WEAVIATE_HTTP_HOST": "127.0.0.1",
    "WEAVIATE_HTTP_PORT": 8080,
    "WEAVIATE_GRPC_HOST": "127.0.0.1",
    "WEAVIATE_GRPC_PORT": 50051,

    # celery默认配置
    "CELERY_BROKER_DB": 1,
    "CELERY_RESULT_BACKEND_DB": 1,
    "CELERY_TASK_IGNORE_RESULT": "False",
    "CELERY_RESULT_EXPIRES": 3600,
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP": "True",

    # 辅助Agent应用id标识
    "ASSISTANT_AGENT_ID": "6774fcef-b594-8008-b30c-a05b8190afe6",

}
