#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/8 21:00
@Author : rxccai@gmail.com
@File   : base_service.py
"""
from typing import Any, Optional

from internal.exception import FailException
from pkg.sqlalchemy import SQLAlchemy


class BaseService:
    db: SQLAlchemy

    def create(self, model: Any, **kwargs) -> Any:
        with self.db.auto_commit():
            model_instance = model(**kwargs)
            self.db.session.add(model_instance)
        return model_instance

    def delete(self, model_instance: Any) -> Any:
        with self.db.auto_commit():
            self.db.session.delete(model_instance)

        return model_instance

    def update(self, model_instance: Any, **kwargs) -> Any:
        with self.db.auto_commit():
            for field, value in kwargs.items():
                if hasattr(model_instance, field):
                    setattr(model_instance, field, value)
                else:
                    raise FailException("更新数据失败")

        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[Any]:
        return self.db.session.query(model).get(primary_key)
