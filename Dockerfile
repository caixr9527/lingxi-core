# 使用Debian 12的Python 3.10版本作为基础镜像
FROM python:3.12-slim-bookworm AS base

# 将requirements.txt拷贝到根目录下
COPY requirements.txt .

# 安装 pandoc
RUN sed -i "1ideb https://mirrors.aliyun.com/debian/ bullseye main non-free contrib" /etc/apt/sources.list
RUN sed -i "2ideb-src https://mirrors.aliyun.com/debian/ bullseye main non-free contrib" /etc/apt/sources.list
RUN sed -i "3ideb https://mirrors.aliyun.com/debian-security/ bullseye-security main" /etc/apt/sources.list
RUN sed -i "4ideb-src https://mirrors.aliyun.com/debian-security/ bullseye-security main" /etc/apt/sources.list
RUN sed -i "5ideb https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib" /etc/apt/sources.list
RUN sed -i "6ideb-src https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib" /etc/apt/sources.list
RUN sed -i "7ideb https://mirrors.aliyun.com/debian/ bullseye-backports main non-free contrib" /etc/apt/sources.list
RUN sed -i "8ideb-src https://mirrors.aliyun.com/debian/ bullseye-backports main non-free contrib" /etc/apt/sources.list

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pandoc \
    wget \
    ca-certificates && \
    # 清理缓存以减小镜像大小
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 构建缓存并使用pip安装严格版本的requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/pkg -r requirements.txt

# 二阶段生产环境构建
FROM base AS production

# 设置工作目录
WORKDIR /app/api

# 定义环境变量
ENV FLASK_APP=app/http/app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV NLTK_DATA=/app/api/internal/core/unstructured/nltk_data
ENV HF_ENDPOINT=https://hf-mirror.com

# 设置容器时区为中国标准时间，避免时区错误
ENV TZ Asia/Shanghai

# 拷贝第三方依赖包+源码文件
COPY --from=base /pkg /usr/local
COPY . /app/api

# 拷贝运行脚本并设置权限
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 暴露5001端口
EXPOSE 5001

# 运行脚本并启动项目
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]