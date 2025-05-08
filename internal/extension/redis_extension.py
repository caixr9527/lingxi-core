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
@Time   : 2024/10/16 21:12
@Author : caixiaorong01@outlook.com
@File   : redis_extension.py
"""
import redis
from flask import Flask
from redis.connection import Connection, SSLConnection

redis_client = redis.Redis()


def init_app(app: Flask):
    connection_class = Connection
    if app.config.get("REDIS_USE_SSL", False):
        connection_class = SSLConnection

    redis_client.connection_pool = redis.ConnectionPool(**{
        "host": app.config.get("REDIS_HOST", "127.0.0.1"),
        "port": app.config.get("REDIS_PORT", 6379),
        "username": app.config.get("REDIS_USERNAME", None),
        "password": app.config.get("REDIS_PASSWORD", None),
        "db": app.config.get("REDIS_DB", 0),
        "encoding": "utf-8",
        "encoding_errors": "strict",
        "decode_responses": False
    }, connection_class=connection_class)

    app.extensions["redis"] = redis_client
