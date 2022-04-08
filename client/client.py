# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clients.py
import logging
import random
import time
from util.ssh import ssh_client
from db.database import database_op
from threading import Thread


class client:
    def __init__(self, node, logger, database_config, operation, index):
        self.hostname = node["hostname"]
        self.port = node["port"]
        self.username = node["username"]
        self.passwd = node["password"]
        self.logger = logger
        self.operation = operation
        self.ssh_client = ssh_client(self.hostname, self.port, self.username, self.passwd)
        self.database = database_op(self.ssh_client, self.hostname, logger, database_config)
        self.database_connection = None

    def setup_db(self):
        return self.database.setup

    def shutdown_db(self):
        self.database.shutdown()

    def recover(self):
        t = Thread(target=self.setup_db())
        t.start()
        time.sleep(20)
        self.connect_db()

    def connect_db(self):
        self.database_connection = self.database.connect_database()

    def disconnect_db(self):
        if self.database_connection:
            self.database_connection.close()
            self.database_connection = None
        else:
            pass

    def operate(self, history):
        self.logger.write_history(history["index"], history["type"], history["f"], history["value"])
        logging.info(self.hostname)
        logging.info(history)
        history_b = self.operation(self.database_connection, history)
        self.logger.write_history(history["index"], history_b["type"], history_b["f"], history_b["value"])
        logging.info(self.hostname)
        logging.info(history_b)

