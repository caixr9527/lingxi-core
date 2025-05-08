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
@Time   : 2024/6/30 16:09
@Author : caixiaorong01@outlook.com
@File   : conftest.py
"""
import pytest
from sqlalchemy.orm import sessionmaker, scoped_session

from app.http.app import app as _app
from internal.extension.database_extension import db as _db


@pytest.fixture
def app():
    _app.config["TESTING"] = True
    return _app


@pytest.fixture
def client(app):
    """获取Flask应用的测试应用，并返回"""
    with app.test_client() as client:
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NmRiMzBkMS0zMTk5LTRlNzktYTBjZC1hYmYxMmZhNjg1OGYiLCJpc3MiOiJsbG1vcHMiLCJleHAiOjE3MzM1MDU2NTR9.HSKjINY58fzengY3BmxIDOnJyACnBnz9NmgVN3y02iI"
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
        yield client


@pytest.fixture
def db(app):
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        _db.session = session
        yield _db
        transaction.rollback()
        connection.close()
        session.remove()
