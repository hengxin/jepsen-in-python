# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import paramiko
from db.database import database_op
from threading import Thread
import time


class client:
    def __init__(self, hostname, port, username, passwd, *args):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.passwd = passwd
        self.ssh_connection = paramiko.SSHClient()
        self.connect_ssh()
        # todo 下面是将database中的对于数据库的操作函数持有化 暂时为占位
        self.database = database_op(self.ssh_connection, self.hostname, 2379, *args)


    def connect_ssh(self):
        self.ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_connection.connect(hostname=self.hostname,
                                    port=self.port,
                                    username=self.username,
                                    password=self.passwd)

    def setup_db(self):
        return self.database.setup

    def shutdown_db(self):
        self.database.shutdown()

    def connect_db(self):
        self.database.connect_database()

    def operation(self, type, *args):
        if type == "w":
            self.database.write(*args)
        elif type == "r":
            self.database.read(*args)
        elif type == "cas":
            self.database.cas(*args)



if __name__ == '__main__':
    initial_cluster = "42.192.52.249=http://42.192.52.249:2380,119.3.69.98=http://119.3.69.98:2380"
    client1 = client("42.192.52.249", 22, "root", "passwd", initial_cluster)
    client2 = client("119.3.69.98", 22, "root", "passwd", initial_cluster)
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
