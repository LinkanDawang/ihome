#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config
from utils.common import RegexConverter


# 数据库对象
db = SQLAlchemy()
redis_store = None

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # 添加自定义的过滤器re
    app.url_map.converters['re'] = RegexConverter

    # 延迟家在数据库
    db.init_app(app)

    # 开启csrf保护
    CSRFProtect(app)

    # 创建redis连接对象
    global redis_store
    redis_store = redis.StrictRedis(port=Config.REDIS_PORT, host=Config.REDIS_HOST)

    # 默认session储存在浏览器的cookie中，需要手动修改，存到服务器中
    Session(app)

    # 导入蓝图，惰性执行避免循环加载，用到的时候在加载
    # 注册蓝图时可以自定义url前缀
    from ihome.api_1_0 import api
    app.register_blueprint(api, url_prefix='/api/v1_0')

    import static_page
    app.register_blueprint(static_page.static_html)

    return app, db

