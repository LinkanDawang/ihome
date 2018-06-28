#!/usr/bin/python
# -*- coding:utf-8 -*-

import redis


class Config(object):
    # 连接mysql数据的额配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 生成用于混淆加密的盐值
    # 先用os.urandom生成一串随机的字符串，再用base64.b64encode进行编码
    SECRET_KEY = 'GcwLdC0IL5+/dIKMVAVShr9a7xT8nTkJ'

    # REDIS连接的参数
    REDIS_HOST = '192.168.3.168'
    REDIS_PORT = 6379

    # 配置flask—Session的存储信息
    SESSION_TYPE = 'redis'
    SESSION_USE_SIGNER = True

    # 扩展默认会有redis的地址信息127.0.0.1:6379,以及前缀信息session
    SESSION_REDIS = redis.StrictRedis(port=REDIS_PORT, host=REDIS_HOST)
    PERMANENT_SESSION_LIFETIME = 86400 * 2  # 配置session存储的有效时间


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass

