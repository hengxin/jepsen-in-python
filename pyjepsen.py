# -*- coding: utf-8 -*-
# @Time    : 2022/2/15 16:35
# @Author  : jiangnanworker, _in, outweishao999
# @Email   : 2764065464@qq.com
# @File    : pyjepsen.py
from client.client import client
from threading import Thread
import time

if __name__ == '__main__':
    initial_cluster = "42.192.52.249=http://42.192.52.249:2380,119.3.69.98=http://119.3.69.98:2380"
    client1 = client("42.192.52.249", 22, "root", "Asdf159753", initial_cluster)
    client2 = client("119.3.69.98", 22, "root", "T2419tzh", initial_cluster)
    t1 = Thread(target=client1.setup_db())
    t2 = Thread(target=client2.setup_db())
    t1.start()
    t2.start()
    time.sleep(10)
    client1.connect_db()
    client2.connect_db()
    client1.operation("w", 'foo', 'hello')
    client2.operation('r', 'foo')
    client2.operation("w", 'foo', 'world')
    client1.operation('r', 'foo')
    client1.shutdown_db()
    client2.shutdown_db()
