# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import paramiko
import db.database as db_operation


class client:
    def __init__(self, hostname, port, username, passwd):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.passwd = passwd
        self.ssh_connection = paramiko.SSHClient()
        # todo 下面是将database中的对于数据库的操作函数持有化 暂时为占位
        self.database_connect = db_operation
        self.database_drop = db_operation
        self.database_operate = db_operation

    def connect_ssh(self):
        self.ssh_connection.connect(hostname=self.hostname,
                                    port=self.port,
                                    username=self.username,
                                    password=self.passwd)