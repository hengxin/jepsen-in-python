# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:49
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : database.py
import logging

import etcd3


class database_op:
    def __init__(self, ssh_connection, hostname, port, logger, config):
        self.ssh_connection = ssh_connection
        self.hostname = hostname
        self.port = port
        self.logger = logger
        self.initial_cluster = config["initial_cluster"]

    def setup(self):
        command_list = [
            'wget https://storage.googleapis.com/etcd/v3.1.5/etcd-v3.1.5-linux-amd64.tar.gz',
            'tar -zxvf etcd-v3.1.5-linux-amd64.tar.gz',
            'mv etcd-v3.1.5-linux-amd64 etcd',
            '''/root/etcd/etcd --log-output stdout --name {0} --listen-peer-urls http://0.0.0.0:2380 --listen-client-urls http://0.0.0.0:2379 --advertise-client-urls http://{0}:2379 --initial-cluster-state new --initial-advertise-peer-urls http://{0}:2380 --initial-cluster {1}'''.format(self.hostname, self.initial_cluster)
        ]
        for c in command_list:
            stdin, stdout, stderr = self.ssh_connection.exec_command(c)
            i = stdout.readline()
           # print('{} started'.format(c))
            while i != '':
                i = stdout.readline()
            logging.info("{} completed".format(c))
        pass

    def shutdown(self):
        command_list = [
            '''ps -ef|grep etcd|grep -v grep|awk '{print $2}'|xargs kill -9''',
            'rm -rf /root/*'
        ]
        for c in command_list:
            stdin, stdout, stderr = self.ssh_connection.exec_command(c)
            while stderr.readline():
                continue
            logging.info("{} completed".format(c))
        self.ssh_connection.close()
        pass

    def connect_database(self):
        return etcd3.client(host=self.hostname, port=self.port)

