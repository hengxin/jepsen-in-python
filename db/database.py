# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:49
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : database.py
import etcd3


class database_op:
    def __init__(self, ssh_client, hostname, config):
        self.ssh_client = ssh_client
        self.hostname = hostname
        self.config = config

    def setup(self):
        pass

    def shutdown(self):
        pass

    def connect_database(self):
        pass

    def disconnect_database(self):
        pass

    def is_running(self):
        return True
