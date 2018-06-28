#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
import re
from flask import request, jsonify, session
from ihome import redis_store, db
from ihome.models import User
from ihome.utils.response_code import RET
from . import api
from ihome.utils.common import login_required


@api.route('/users', methods=['POST'])
def register():
    """用户注册"""
    # /api/v1_0/users

    # 获取前端传送过来的数据
    resp_dict = request.get_json()
    mobile = resp_dict.get('mobile')
    password = resp_dict.get('password')
    sms_code = resp_dict.get('sms_code')

    # 校验数据完整性
    if not all([mobile, password, sms_code]):
        response = {
            'errno': RET.DATAERR,
            'errmsg': '参数不全'
        }
        return jsonify(response)

    # 判断手机号码是否合法
    if not re.match(r'1[356789][0-9]{9}$', mobile):
        response = {
            'errno': RET.DATAERR,
            'errmsg': '输入的手机号码有误'
        }
        return jsonify(response)

    # 获取短信验证码
    try:
        real_sms_code = redis_store.get('sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
        response = {
            'errno': RET.DBERR,
            'errmsg': 'redis获取数据出错'
        }
        return jsonify(response)

    # 判断短信验证码是否已经过期
    if real_sms_code is None:
        response = {
            'errno': RET.NODATA,
            'errmsg': '短信验证码已经过期'
        }
        return jsonify(response)

    # 与用户输入的验证码作对比
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='您输入的验证码有误')

    # 通过验证，删除短信验证码
    try:
        redis_store.delete('sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis删除数据短信验证码失败')

    # 判断用户是否已经注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='mysql查询用户失败')
    else:
        if user is not None:  # 手机已经被注册
            return jsonify(errno=RET.DATAEXIST, errmsg='该手机号已经被注册')
        else:  # 没有被注册就创建新用户
            user = User(name=mobile, mobile=mobile)
            user.password = password
        try:  # 保存用户信息到数据库
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='mysql添加用户失败')

    # 注册成功，直接登入，保存用户Session
    try:
        session['user_id'] = user.id
        session['user_name'] = user.mobile
        session['mobile'] = mobile
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.SESSIONERR, errmsg='session设置失败')

    return jsonify(errno=RET.OK, errmsg='注册成功')


@api.route('/sessions', methods=['POST'])
def login():
    """用户登入接口"""
    # /api/v1_0/sessions

    # 获取用户账号和密码
    resp_dict = request.get_json()
    mobile = resp_dict.get('mobile')
    password = resp_dict.get('password')

    # 校验参数完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.DATAERR, errmsg='参数不全')

    # 检验手机号码的合法性
    if not re.match(r'1[356789][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号有误')

    """用户登入错误超过一定次数直接返回"""
    # 获取用户IP地址
    user_ip = request.remote_addr

    # 获取用户的登入错误次数
    try:
        login_fail_count = redis_store.get('login_fail_count_%s' % user_ip)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis读取数据错误')

    # 错误次数超过5次
    if login_fail_count is not None and int(login_fail_count) >= 5:
        return jsonify(errno=RET.REQERR, errmsg='密码输入错误超过5次')

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='mysql查询用户信息失败')

    # 用户输入账号或者密码错误，记入错误次数
    if user is None or not user.check_password_hash(password):
        # 记录错误次数
        try:
            redis_store.incr('login_fail_count_%s' % user_ip)
            redis_store.expire('login_fail_count_%s' % user_ip, 86400)
        except Exception as e:
            logging.error(e)

        return jsonify(errno=RET.DATAERR, errmsg='用户名或密码错误')

    # 登入超过，设置Session信息
    try:
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['mobile'] = user.mobile
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='Session设置失败')

    # 删除用户的登入错误信息
    try:
        redis_store.delete('login_fail_count_%s' % user_ip)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis删除数据失败')

    return jsonify(errno=RET.OK, errmsg='登入成功')


@api.route('/sessions', methods=['GET'])
def check_login():
    """检查用户的登入"""
    # 从session获取用户信息
    name = session.get('user_name')
    # 如果session中有数据表示用户已经登入，没有的话表示未登入
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={'name': name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')


@api.route('/sessions', methods=['DELETE'])
@login_required
def logout():
    # 清除Session里的数据,csrf_token需要保留
    csrf_token = session['csrf_token']
    session.clear()
    session['csrf_token'] = csrf_token

    return jsonify(errno=RET.OK, errmsg='ok')

