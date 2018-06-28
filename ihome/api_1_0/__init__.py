#!/usr/bin/python
# -*- coding:utf-8 -*-

from flask import Blueprint

# 创建了蓝图
api = Blueprint('api', __name__)

import verify_code, passport, profile


# 添加请求钩子，统一返回的数据为json格式
@api.after_request
def after_request(response):
    if response.headers.get('Content-Type').startswith('text'):
        response.headers['Content-Type'] = 'application/json'
    return response

