# 使用官方的 Python 镜像作为基础
FROM python:3.11

# set the python env
ENV PYTHONUNBUFFERED 1

# 创建工作目录
WORKDIR /var/project/ExpCenter

# 复制项目文件
COPY . .

# 安装项目依赖
RUN pip install -r requirements.txt

# 暴露端口
EXPOSE 8000

# 在容器启动时运行数据库迁移然后启动 Gunicorn
CMD ["sh", "-c", "python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:8000"]
