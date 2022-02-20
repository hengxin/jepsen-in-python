# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import paramiko
from db.database import database_op


class client:
    def __init__(self, hostname, port, username, passwd, logger, *args):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.passwd = passwd
        self.logger = logger
        self.ssh_connection = paramiko.SSHClient()
        self.connect_ssh()
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
        value = None
        if len(args) > 1:
            value = args[1]
        self.logger.write_log(1, "invoke", type, value)
        try:
            if type == "write":
                self.database.write(*args)
                self.logger.write_log(1, "ok", type, value)
            elif type == "read":
                read_val = self.database.read(*args)
                self.logger.write_log(1, "ok", type, read_val)
            elif type == "cas":
                self.database.cas(*args)
        except Exception:
            print(Exception.with_traceback())
            self.logger.write_log(1, "fail", type, value)
