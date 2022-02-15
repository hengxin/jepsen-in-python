# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import paramiko
from db.database import database_op

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
