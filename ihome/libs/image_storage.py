#!/usr/bin/python
# -*- coding:utf-8 -*-

from qiniu import Auth, put_data

"""使用七牛云存储图片"""

access_key = 'ZR0Jrp7a16J0ur1iH6s4tPjI9ZP8Nd64eKgAz2Y6'
secret_key = '0z09qqbA-j02tmOuZ_GcZdDqMJKrORGZR2HWCRk5'


# 封装成方法被调用
def storage(file_data):
    """上传图片到七牛云对象存储，file_data为二进制数据"""

    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 存储文件的空间
    bucket_name = 'ihomeimages'
    # 生成Token，指定过期时间
    token = q.upload_token(bucket_name, None, 3600)

    # 上传数据，获得返回结果
    ret, info = put_data(token, None, file_data)

    print 'info: %s' % info
    print 'ret: %s' % ret

    if info.status_code == 200:
        return ret.get('key')
    else:
        raise Exception('上传失败')


if __name__ == '__main__':
    with open('../static/favicon.ico', 'rb') as f:
        file_data = f.read()
        result = storage(file_data)

        print result

