# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import logging
import random
import time
from util.ssh import ssh_client
from threading import Thread


class client:
    def __init__(self, node, database_op, database_config, operation):
        self.hostname = node["hostname"]
        self.port = node["port"]
        self.username = node["username"]
        self.passwd = node["password"]
        self.operation = operation
        self.ssh_client = ssh_client(self.hostname, self.port, self.username, self.passwd)
        self.database = database_op(self.ssh_client, self.hostname, database_config)
        self.database_connection = None

    def setup_db(self):
        return self.database.setup

    def shutdown_db(self):
        if self.database:
            self.database.shutdown()
        else:
            pass

    def is_running(self):
        running = self.ssh_client.exec_command("ps -ef|grep etcd|grep -v grep|grep -v wget|awk '{print $2}'", return_result=True)
        return len(running) >= 1

    def recover(self):
        t = Thread(target=self.setup_db())
        t.start()
        running = False
        retry = 10
        while not running and retry > 0:
            time.sleep(1)
            running = self.is_running()
            retry -= 1
        if retry <= 0:
            return
        self.connect_db()

    def connect_db(self):
        self.database_connection = self.database.connect_database()

    def disconnect_db(self):
        if self.database_connection:
            self.database_connection.close()
            self.database_connection = None
        else:
            pass

    def operate(self, op):
        exec_op_response = self.operation(self.database_connection, op)
        exec_op_response["process"] = op["process"]
        return exec_op_response

