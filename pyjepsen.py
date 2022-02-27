# -*- coding: utf-8 -*-
# @Time    : 2022/2/15 16:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : pyjepsen.py
from util import util
from client.client import client
from log.log_util import log
from threading import Thread
import time
import os

if __name__ == '__main__':
    # 创建日志对象 用于写文件
    # 可传入日志的相关配置
    server_config = util.read_config("server.yaml")
    database_config = util.read_config("database.yaml")
    logger = log({})
    client_list = []
    for n in server_config:
        node = server_config[n]
        new_client = client(node["ip"], node["port"], node["username"], node["password"], logger, database_config)
        client_list.append(new_client)
    for client in client_list:
        t = Thread(target=client.setup_db())
        t.start()
    time.sleep(10)
    for client in client_list:
        client.connect_db()
    # 把list交给generator去操作
    client_list[0].operation("write", 'foo', '1')
    client_list[1].operation('read', 'foo')
    client_list[0].operation('cas', 'foo', '3', '1')
    client_list[0].operation('cas', 'foo', '1', '4')
    client_list[1].operation('read', 'foo')
    client_list[1].operation("write", 'foo', '2')
    client_list[0].operation('read', 'foo')
    client_list[1].operation('write', 'foo', '3')
    client_list[0].operation('read', 'foo')
    client_list[0].operation('write', 'foo', '1')
    client_list[1].operation("write", 'foo', '2')
    client_list[0].operation('read', 'foo')
    for client in client_list:
        client.shutdown_db()
    # knossos打了个包 先这样用着
    result = os.popen("java -jar knossos-0.3.9-SNAPSHOT-standalone.jar --model cas-register history.edn")
    for i in result.readlines():
        print(i)
