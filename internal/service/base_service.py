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
@Time   : 2024/10/8 21:00
@Author : caixiaorong01@outlook.com
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
