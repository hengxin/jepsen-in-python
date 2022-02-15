# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:49
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : database.py
import etcd3


class database_op:
    def __init__(self, ssh_connection, hostname, port, *args):
        self.ssh_connection = ssh_connection
        self.hostname = hostname
        self.port = port
        self.initial_cluster = args[0]
        self.database_connection = None

    def setup(self):
        command_list = [
            'wget https://storage.googleapis.com/etcd/v3.1.5/etcd-v3.1.5-linux-amd64.tar.gz',
            'tar -zxvf etcd-v3.1.5-linux-amd64.tar.gz',
            'mv etcd-v3.1.5-linux-amd64 etcd',
            '''/root/etcd/etcd --log-output stdout --name {0} --listen-peer-urls http://0.0.0.0:2380 --listen-client-urls http://0.0.0.0:2379 --advertise-client-urls http://{0}:2379 --initial-cluster-state new --initial-advertise-peer-urls http://{0}:2380 --initial-cluster {1}'''.format(self.hostname, self.initial_cluster)
        ]
        for c in command_list:
            stdin, stdout, stderr = self.ssh_connection.exec_command(c)
            print(stdout.readlines())
        pass

    def shutdown(self):
        command_list = [
            '''ps -ef|grep etcd|grep -v grep|awk '{print $2}'|xargs kill -9''',
            'rm -rf /root/*'
        ]
        for c in command_list:
            stdin, stdout, stderr = self.ssh_connection.exec_command(c)
            print(stdout.readlines())
        self.ssh_connection.close()
        pass

    def connect_database(self):
        self.database_connection = etcd3.client(host=self.hostname, port=self.port)

    def write(self, key, value):
        self.database_connection.put(key, value)
        pass

    def read(self, key):
        result = self.database_connection.get(key)
        print(result)
        pass

    # compare and set
    def cas(self, key, value_old, value_new):
        pass
