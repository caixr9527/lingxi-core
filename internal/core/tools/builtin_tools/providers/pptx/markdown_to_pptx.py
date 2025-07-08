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
@Time   : 2025/3/22 11:07
@Author : caixiaorong01@outlook.com
@File   : markdown_to_pptx.py.py
"""
import logging
import os
import tempfile
import urllib.request
import uuid
from typing import Type, Any, Optional

import mistune
from langchain_core.tools import BaseTool
from pptx import presentation, Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt, Length, Inches
from pydantic import BaseModel, Field

from internal.lib.helper import add_attribute


class PPTRenderer(mistune.HTMLRenderer):
    """借助HTML渲染器重写并定义PPT渲染器"""
    prs: presentation.Presentation
    font_name: str  # 字体名字
    image_folder: str  # 存储图片的文件夹
    content_left: Length  # 内容距离左侧的距离
    content_top: Length  # 内容距离顶部的距离
    content_width: Length  # 内容的宽度
    line_height: Length  # 内容行高

    def __init__(
            self,
            prs: presentation.Presentation,  # PPT演示文稿
            image_folder: str,  # 存储图片的文件夹
    ):
        """构造函数，完成PPT渲染器的初始化"""
        # 调用父类构造函数完成数据初步初始化
        super().__init__()

        # 完成PPT渲染器数据初始化
        self.prs = prs
        self.current_slide = None
        self.font_name = "微软雅黑"
        self.image_folder = image_folder
        self.content_left = Inches(1)  # 默认距离左侧1英寸
        self.content_top = Inches(1.5)  # 默认距离顶部1.5英寸
        self.content_width = Inches(8.5)  # 默认内容宽度为8.5英寸，4:3比例下
        self.line_height = Pt(24)  # 默认行高为24

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        """标题内容处理器"""
        # 判断标题的等级，如果为h1则代表为封面标题
        if level == 1:
            # 新建布局并添加封面页
            slide = self.prs.slides.add_slide(self.prs.slide_layouts[0])

            # 设置页面标题与副标题
            title = slide.shapes.title
            sub_title = slide.placeholders[1]
            title.text = text.strip()
            title.text_frame.paragraphs[0].font.name = self.font_name
            sub_title.text = "由不懂就问-AI平台生成"
            self.current_slide = None
        else:
            # 内容页创建带有标题的空布局页面并更新当前页
            slide_layout = self.prs.slide_layouts[5]
            self.current_slide = self.prs.slides.add_slide(slide_layout)

            # 设置页面标题内容与字体
            title_shape = self.current_slide.shapes.title
            title_shape.text = text.strip()
            title_shape.text_frame.paragraphs[0].font.name = self.font_name

            # 更新当前内容距离顶部的距离
            self.content_top = Inches(1.5)
        return ""

    def paragraph(self, text: str) -> str:
        """段落内容处理器"""
        # 提取段落的头尾空格
        text = text.strip()

        # 判断是否存在页面，存在才允许插入内容(空行直接跳过)
        if self.current_slide and len(text):
            # 检查是否插入新页面
            self.check_new_slide()

            # 估算文本的高度
            text_height = self.estimate_text_height(text, font_size=18)

            # 添加文本输入框
            text_box = self.current_slide.shapes.add_textbox(
                self.content_left,
                self.content_top,
                self.content_width,
                text_height,
            )

            # 提取输入框并强制换行
            tf = text_box.text_frame
            tf.word_wrap = True

            # 清除输入框中的默认换行
            if tf.paragraphs:
                tf.paragraphs[0]._element.getparent().remove(tf.paragraphs[0]._element)

            # 往输入框中添加段落并设置样式
            p = tf.add_paragraph()
            p.text = text
            p.font.name = self.font_name
            p.font.size = Pt(18)

            # 更新内容距离顶部高度
            self.content_top += text_height

        return ""

    def list(self, text: str, ordered: bool, **attrs: Any) -> str:
        """列表内容处理器"""
        # 判断幻灯片演示页存在时才添加元素
        if self.current_slide:
            # 判断是否新增页面
            self.check_new_slide()

            # 添加文本输入框(列表也是文本框)，并预先配置4英寸高度
            text_box = self.current_slide.shapes.add_textbox(
                self.content_left,
                self.content_top,
                self.content_width,
                Inches(4),
            )

            # 提取输入框内容并强制换行
            tf = text_box.text_frame
            tf.word_wrap = True
            tf.clear()

            # 分割提取列表信息
            items = text.strip().split("\n")
            total_height = 0

            # 循环遍历所有列表
            for item in items:
                # 检查是否插入新页
                self.check_new_slide()

                # 在文本框中添加段落
                p = tf.add_paragraph()
                p.text = item.strip().replace("<li>", "").replace("</li>", "")
                p.level = 0
                p.font.name = self.font_name
                p.font.size = Pt(18)

                # 重新估算行高并更新
                item_height = self.estimate_text_height(item, font_size=18)
                total_height += item_height
                self.content_top += item_height  # 累积高度

            # 如果文本框溢出，自动换页
            if total_height > Inches(4):
                self.check_new_slide()

        return ""

    def image(self, text: str, url: str, title: Optional[str] = None) -> str:
        """图片内容处理器"""
        try:
            # 判断是否存在页面，存在时才处理操作
            if self.current_slide:
                # 判断是否新增页面
                self.check_new_slide()

                # 将网络图片下载到本地
                if url.startswith("http"):
                    # 4.构建存储图片的位置
                    local_path = os.path.join(self.image_folder, os.path.basename(url))
                    urllib.request.urlretrieve(url, local_path)
                else:
                    local_path = url

                # 将图片添加到幻灯片并居中，图片宽固定为4英寸(可优化为PIL动态计算)
                pic = self.current_slide.shapes.add_picture(
                    local_path,
                    (self.prs.slide_width - Inches(4)) / 2,
                    self.content_top,
                    width=Inches(4),
                )

                # 更新内容距离顶部的高度
                self.content_top += pic.height + Inches(0.5)
        except Exception as error:
            logging.error("PPTRenderer图片处理失败, 错误信息: %(error)s", {"error": error}, exc_info=True)

        return ""

    def block_code(self, code: str, info: Optional[str] = None) -> str:
        """代码块内容处理器"""
        # 判断页面存在才插入数据
        if self.current_slide:
            # 检查是否新建页面
            self.check_new_slide()

            # 新增文本输入框
            text_box = self.current_slide.shapes.add_textbox(
                self.content_left,
                self.content_top,
                self.content_width,
                Inches(2)
            )

            # 配置文本输入框内容
            tf = text_box.text_frame
            p = tf.add_paragraph()
            p.text = code.strip()
            p.font.name = 'Consolas'
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(0x33, 0x66, 0x99)

            # 重新计算内容距离顶部的高度
            self.content_top += self.line_height * (code.count('\n') + 2)

        return ''

    def check_new_slide(self) -> None:
        """检查是否需要新建幻灯片"""
        # 判断当前内容高度是否大于等于6英寸(页面高度为6英寸)
        if self.content_top >= Inches(6):
            # 获取原先页面的标题
            title = ""
            if self.current_slide:
                title_shape = self.current_slide.shapes.title
                if title_shape and title_shape.text:
                    title = title_shape.text

            # 创建新幻灯片并更新内容高度
            self.current_slide = self.prs.slides.add_slide(self.prs.slide_layouts[5])
            self.content_top = Inches(1.5)

            # 判断是否有标题，如果有则填充并设置字体
            if title:
                new_title_shape = self.current_slide.shapes.title
                if new_title_shape:
                    new_title_shape.text = title
                    new_title_shape.text_frame.paragraphs[0].font.name = self.font_name

    @classmethod
    def estimate_text_height(cls, text: str, font_size: int = 20, avg_char_per_line: int = 30) -> float:
        """根据传递的文本内容、文字大小、行平均字数估算文本的高度"""
        # 估算数据行数
        lines = max(1, (len(text) // avg_char_per_line) + text.count("\n"))

        # 计算文本的行高(1.2倍行高)
        line_height = Pt(font_size * 1.2)

        # 计算文本的总高度，并冗余0.3行的高度
        return (lines + 0.3) * line_height


class MarkdownToPPTXArgsSchema(BaseModel):
    markdown: str = Field(description="要生成PPT内容的markdown文档字符串。")


class MarkdownToPPTXTool(BaseTool):
    """markdown转本地pptx工具"""
    name: str = "markdown_to_pptx"
    description: str = "这是一个可以将markdown文本转换成PPT的工具，传递的参数是markdown对应的文本字符串，返回的数据是PPT的下载地址。"
    args_schema: Type[BaseModel] = MarkdownToPPTXArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """根据传递的markdown文档内容调用python-pptx和mistune创建pptx文件并存储到cos中"""
        try:
            # 创建一个临时文件夹，用于存储ppt与下载的图片
            with tempfile.TemporaryDirectory() as temp_dir:
                # 创建一个空的PPT演示文稿与PPT渲染对象
                prs = Presentation()
                renderer = PPTRenderer(prs, temp_dir)
                markdown = mistune.Markdown(renderer)
                markdown(kwargs.get("markdown"))

                # 保存输出ppt
                filename = str(uuid.uuid4()) + ".pptx"
                filepath = os.path.join(temp_dir, filename)
                prs.save(filepath)

                # 获取cos服务中的客户端与存储桶
                from internal.service import CosService
                from app.http.module import injector

                cos_service = injector.get(CosService)
                client = cos_service.get_client()
                bucket = cos_service.get_bucket()

                # 将pptx文件上传到腾讯云cos存储
                key = f"builtin-tools/markdown-to-pptx/{filename}"
                client.upload_file(
                    Bucket=bucket,
                    Key=key,
                    LocalFilePath=filepath,
                    EnableMD5=False,
                    progress_callback=None,
                )

                # 返回对应的地址
                return cos_service.get_file_url(key)
        except Exception as error:
            logging.error("markdown_to_pptx出错: %(error)s", {"error": error}, exc_info=True)
            return f"生成PPT演示文稿失败，错误原因: {str(error)}"


@add_attribute("args_schema", MarkdownToPPTXArgsSchema)
def markdown_to_pptx(**kwargs) -> BaseTool:
    """一个可以将markdown文本转换成PPT的工具，传递的参数是markdown对应的文本字符串，返回的数据是PPT的下载地址。"""
    return MarkdownToPPTXTool()
