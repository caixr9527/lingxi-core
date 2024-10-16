#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/16 22:12
@Author : rxccai@gmail.com
@File   : celery_extension.py
"""
from celery import Task, Celery
from flask import Flask


def init_app(app: Flask):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    app.extensions["celery"] = celery_app
