#!/usr/bin/python
# -*- coding:utf-8 -*-

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from config import DevelopmentConfig
from ihome import create_app
# 必须导入数据库模型
from ihome.models import User, Area, House, Facility, HouseImage, Order


# 由manager.py文件来管理程序的启动,通过对象来加载配置信息
app, db = create_app(DevelopmentConfig)

# 托管app的启动
manager = Manager(app)

# 执行迁移文件
Migrate(app, db)

# 在终端执行迁移需要添加db命令
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()

