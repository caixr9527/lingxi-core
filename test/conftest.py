#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/6/30 16:09
@Author : rxccai@gmail.com
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
    with app.test_client() as client:
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
