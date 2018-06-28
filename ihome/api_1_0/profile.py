#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
from flask import request, g, jsonify, session
from ihome import db
from ihome.models import User
from ihome.libs.image_storage import storage
from ihome.utils import constants
from ihome.utils.common import login_required
from ihome.utils.response_code import RET
from . import api


@api.route('/users/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """上传用户头像"""
    # 获取用户的id和图片数据
    user_id = g.user_id
    image_file = request.files.get('avatar')

    # 校验参数
    if image_file is None:
        return jsonify(errno=RET.DATAERR, errmsg='用户图片上传失败')

    # 调用七牛云上传图片到对象存储
    image_data = image_file.read()
    try:
        url_name = storage(image_data)
        print url_name
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='七牛云存储错误')

    # 保存文件名到数据库
    try:
        User.query.filter_by(id=user_id).update({'avatar_url': url_name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='mysql存储图片错误')

    avatar_url = constants.QINIU_URL_DOMAIN + url_name
    return jsonify(errno=RET.DBERR, errmsg='上传头像成功', data={'avatar_url': avatar_url})


@api.route('/users/name', methods=['PUT'])
@login_required
def set_user_name():
    """修改用户的用户名"""
    # PUT /api/v1_0/users/name

    # 获取用户的id
    user_id = g.user_id

    # 获取新的用户名
    req_dict = request.get_json()
    if not req_dict:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    user_name = req_dict.get('name')

    if not user_name:
        return jsonify(errno=RET.PARAMERR, errmsg='用户名不能为空')

    try:
        User.query.filter_by(id=user_id).update({'name': user_name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rallback()
        return jsonify(errno=RET.DBERR, errmsg='mysql保存出错')

    session['user_name'] = user_name
    return jsonify(errno=RET.OK, errmsg='修改用户名成功', data={'name': user_name})

