#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/15 23:00
@Author : rxccai@gmail.com
@File   : logging_extension.py
"""
import logging
import os.path

from concurrent_log_handler import ConcurrentTimedRotatingFileHandler
from flask import Flask


def init_app(app: Flask):
    logging.getLogger().setLevel(
        logging.DEBUG if app.debug or os.getenv("FLASK_ENV") == "development" else logging.WARNING)
    log_folder = os.path.join(os.getcwd(), "storage", "log")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_file = os.path.join(log_folder, "app.log")
    handler = ConcurrentTimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s]: %(message)s"
    )
    handler.setLevel(logging.DEBUG if app.debug or os.getenv("FLASK_ENV") == "development" else logging.WARNING)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    if app.debug or os.getenv("FLASK_ENV") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
