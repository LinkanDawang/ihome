#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
import random
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from flask import jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.models import User
from ihome.libs.yuntongxun.SendTemplateSMS import CCP


@api.route('/image_codes/<image_code_id>', methods=['GET'])
def get_image_code(image_code_id):
    """获取图片验证码的接口"""
    # /api/v1_0/image_codes/a4805ed3-8d7e-425b-88cd-d6b3eaba838a

    # 1.获取图片验证码
    name, text, image_data = captcha.generate_captcha()

    # 2.把验证码存储到redis数据库中，设置有效时长为300秒
    try:
        redis_store.setex('image_code_%s' % image_code_id, 300, text)
    except Exception as e:
        logging.error(e)  # 捕捉异常记录到日志文件
        response = {
            'errno': RET.DBERR,
            'errmsg': 'redis存储验证码出错'
        }
        return jsonify(response)

    # 声明返回的是图片文件，传送图片给前端页面
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'

    print '图片验证码为：%s' % text

    return response


@api.route('/sms_codes/<re(r"1[356789][0-9]{9}"):mobile>')
def send_sms_code(mobile):
    """发送短信验证码"""
    # /api/v1_0/sms_codes/17717825607

    # 1.获取图片验证码，验证用户输入的验证码是否正确
    # ImmutableMultiDict([('image_code', u'aaaa'), ('image_code_id', u'8e4345b0-4ec5-438f-9d9c-e51da4a1dfa1')])
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')
    # 从redis中获取图形验证码作对比
    try:
        real_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        response = {
            'errno': RET.DBERR,
            'errmsg': 'redis获取数据失败'
        }
        return jsonify(response)

    # 判断验证码是否已经过期
    if real_code is None:
        response = {
            'errno': RET.DBERR,
            'errmsg': '验证码已经获取，请从新获取'
        }
        return jsonify(response)

    # 如果获取了验证码，无论验证成功或者失败，都要删除redis中的验证码，只用于一次验证
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        response = {
            'errno': RET.DBERR,
            'errmsg': 'redis删除数据失败'
        }
        return jsonify(response)

    # 验证用户输入的正确性,不区分大小写
    if real_code.lower() != image_code.lower():
        response = {
            'errno': RET.DATAERR,
            'errmsg': '验证码错误，请从新输入'
        }
        return jsonify(response)

    # 判断用户是否已经注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        response = {
            'errno': RET.DBERR,
            'errmsg': 'mysql查询数据失败'
        }
        return jsonify(response)
    else:
        if user is not None:  # 用户已经存在
            response = {
                'errno': RET.DATAEXIST,
                'errmsg': '该手机号已经被注册'
            }
            return jsonify(response)

    # 调用第三方SDK发送短信验证码
    # 生成随机的六位短信验证码,保存到redis中
    sms_code = '%06d' % random.randint(0, 999999)
    try:
        redis_store.setex('sms_code_%s' % mobile, 300, sms_code)
    except Exception as e:
        logging.error(e)
        response = {
            'errno': RET.DBERR,
            'errmsg': 'redis保存数据失败'
        }
        return jsonify(response)

    ccp = CCP()
    result = ccp.send_template_sms(mobile, [sms_code, '5'], 1)

    if result == '000000':
        response = {
            'errno': RET.OK,
            'errmsg': '短信发送成功'
        }
        return jsonify(response)
    else:
        response = {
            'errno': RET.THIRDERR,
            'errmsg': '短信发送失败'
        }
        return jsonify(response)

