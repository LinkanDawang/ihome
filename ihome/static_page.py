#!/usr/bin/python
# -*- coding:utf-8 -*-


"""处理静态文件的访问，不做模板的渲染"""

from flask import Blueprint, current_app, make_response
from flask_wtf.csrf import generate_csrf

static_html = Blueprint('static_html', __name__)


# 添加的自定义过滤器，使用一个路由完成静态页面的访问
@static_html.route('/<re(r".*"):file_name>')
def static_page(file_name):
    # 默认地址为主页
    if not file_name:
        file_name = 'index.html'

    if file_name != 'favicon.ico':
        file_name = 'html/' + file_name

    print file_name

    # 返回静态文件
    response = make_response(current_app.send_static_file(file_name))
    # 设置csrf-token
    csrf_token = generate_csrf()
    # 设置cookie
    response.set_cookie('csrf_token', csrf_token)

    return response

