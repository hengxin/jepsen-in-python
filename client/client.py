# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import paramiko
from db.database import database_op


class client:
    def __init__(self, node, logger, database_config, operation):
        self.hostname = node["hostname"]
        self.port = node["port"]
        self.username = node["username"]
        self.passwd = node["password"]
        self.logger = logger
        self.operation = operation
        self.ssh_connection = paramiko.SSHClient()
        self.connect_ssh()
        self.database = database_op(self.ssh_connection, self.hostname, 2379, logger, database_config)
        self.database_connection = None

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
        self.database_connection = self.database.connect_database()

    def operate(self, f):
        history = f()
        self.logger.write_history(1, history["type"], history["f"], history["value"])
        history_b = self.operation(self.database_connection, history)
        self.logger.write_history(1, history_b["type"], history_b["f"], history_b["value"])

