#!/usr/bin/python
# -*- coding:utf-8 -*-

"""公用的工具类"""

from werkzeug.routing import BaseConverter
from flask import session, g, jsonify
from ihome.utils.response_code import RET
from functools import wraps


class RegexConverter(BaseConverter):
    # 添加自定义过滤器re
    def __init__(self, url_map, regex):
        super(RegexConverter, self).__init__(url_map)
        self.regex = regex


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # 获取用户id
        user_id = session.get('user_id')
        if user_id is not None:
            # 使用g变量来记录用户id，g变量只能使用一次
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登入')
    return wrapper

