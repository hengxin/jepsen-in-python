# -*- coding: utf-8 -*-
# @Time    : 2022/2/15 16:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : pyjepsen.py
from client.client import client
from log.log_util import log
from threading import Thread
import time
import os

if __name__ == '__main__':
    # 创建日志对象 用于写文件
    # 可传入日志的相关配置
    logger = log({})
    initial_cluster = "42.192.52.249=http://42.192.52.249:2380,119.3.69.98=http://119.3.69.98:2380"
    client1 = client("42.192.52.249", 22, "root", "Asdf159753", logger, initial_cluster)
    client2 = client("119.3.69.98", 22, "root", "T2419tzh", logger, initial_cluster)
    t1 = Thread(target=client1.setup_db())
    t2 = Thread(target=client2.setup_db())
    t1.start()
    t2.start()
    time.sleep(10)
    client1.connect_db()
    client2.connect_db()
    client1.operation("write", 'foo', '1')
    client2.operation('read', 'foo')
    client1.operation('cas', 'foo', '3', '1')
    client1.operation('cas', 'foo', '1', '4')
    client2.operation('read', 'foo')
    client2.operation("write", 'foo', '2')
    client1.operation('read', 'foo')
    client2.operation('write', 'foo', '3')
    client1.operation('read', 'foo')
    client1.operation('write', 'foo', '1')
    client2.operation("write", 'foo', '2')
    client1.operation('read', 'foo')
    client1.shutdown_db()
    client2.shutdown_db()
    # knossos打了个包 先这样用着
    result = os.popen("java -jar knossos-0.3.9-SNAPSHOT-standalone.jar --model cas-register history.edn")
    for i in result.readlines():
        print(i)
