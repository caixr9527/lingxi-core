#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/10/21 23:20
@Author : rxccai@gmail.com
@File   : document_schema.py
"""
import uuid

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, AnyOf, ValidationError

from internal.entity.dataset_entity import ProcessType, DEFAULT_PROCESS_RULE
from internal.model import Document
from .schema import ListField, DictField


class CreateDocumentsReq(FlaskForm):
    upload_file_ids = ListField("upload_file_ids")
    process_type = StringField("process_type", validators=[
        DataRequired("文档处理类型不能为空"),
        AnyOf(values=[ProcessType.AUTOMATIC, ProcessType.CUSTOM], message="处理类型格式错误")
    ])
    rule = DictField("rule")

    def validate_upload_file_ids(self, field: ListField) -> None:
        if not isinstance(field.data, list):
            raise ValidationError("文件id列表格式必须是数组")
        if len(field.data) == 0 or len(field.data) > 10:
            raise ValidationError("新增文档数范围在0-10")
        for upload_file_id in field.data:
            try:
                uuid.UUID(upload_file_id)
            except Exception as e:
                raise ValidationError("文件id的格式必须数UUID")

        field.data = list(dict.fromkeys(field.data))

    def validate_rule(self, field: DictField) -> None:
        if self.process_type.data == ProcessType.AUTOMATIC:
            field.data = DEFAULT_PROCESS_RULE["rule"]
        else:
            if not isinstance(field.data, dict) or len(field.data) == 0:
                raise ValidationError("自定义处理模式下，rule不能为空")
            if "pre_process_rules" not in field.data or not isinstance(field.data["pre_process_rules"], list):
                raise ValidationError("pre_process_rules必须为列表")
            unique_pre_process_rule_dict = {}
            for pre_process_rule in field.data["pre_process_rules"]:
                if "id" not in pre_process_rule or pre_process_rule["id"] not in ["remove_extra_space",
                                                                                  "remove_url_and_email"]:
                    raise ValidationError("预处理ID格式错误")
                if "enabled" not in pre_process_rule or not isinstance(pre_process_rule["enabled"], bool):
                    raise ValidationError("预处理enabled格式错误")
                unique_pre_process_rule_dict[pre_process_rule["id"]] = {
                    "id": pre_process_rule["id"],
                    "enabled": pre_process_rule["enabled"],
                }
            if len(unique_pre_process_rule_dict) != 2:
                raise ValidationError("预处理规则格式错误,请重试")
            field.data["pre_process_rules"] = list(unique_pre_process_rule_dict.values())
            if "segment" not in field.data or not isinstance(field.data["segment"], dict):
                raise ValidationError("segment不能为空且为字典")
            if "separators" not in field.data["segment"] or not isinstance(field.data["segment"]["separators"], list):
                raise ValidationError("separators不能为空且为列表")
            for separator in field.data["segment"]["separators"]:
                if not isinstance(separator, str):
                    raise ValidationError("分隔符列表元素格式错误")
            if len(field.data["segment"]["separators"]) == 0:
                raise ValidationError("separators不能为空")
            if "chunk_size" not in field.data["segment"] or not isinstance(field.data["segment"]["chunk_size"], int):
                raise ValidationError("chunk_size不能为空且为整型")
            if field.data["segment"]["chunk_size"] < 100 or field.data["segment"]["chunk_size"] > 1000:
                raise ValidationError("chunk_size范围为100-1000")

            if ("chunk_overlap" not in field.data["segment"] or
                    not isinstance(field.data["segment"]["chunk_overlap"], int)):
                raise ValidationError("chunk_overlap不能为空且为整型")
            if not (0 <= field.data["segment"]["chunk_overlap"] or field.data["segment"]["chunk_size"] * 0.5):
                raise ValidationError(f"快重叠大小在0-{int(field.data['segment']['chunk_size'] * 0.5)}")
            field.data = {
                "pre_process_rules": field.data["pre_process_rules"],
                "segment": {
                    "separators": field.data["segment"]["separators"],
                    "chunk_size": field.data["segment"]["chunk_size"],
                    "chunk_overlap": field.data["segment"]["chunk_overlap"],
                }
            }


class CreateDocumentResp(Schema):
    documents = fields.List(fields.Dict, dump_default=[])
    batch = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: tuple[list[Document], str], **kwargs):
        return {
            "documents": [{
                "id": document.id,
                "name": document.name,
                "status": document.status,
                "created_at": int(document.created_at.timestamp())
            } for document in data[0]],
            "batch": data[1],
        }
