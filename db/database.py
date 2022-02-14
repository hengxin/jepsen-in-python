# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:49
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : database.py
import eventlet


class database_op:
    def __init__(self, ssh_connection):
        self.ssh_connection = ssh_connection

    def setup(self):
        command_list = [
            'wget https://storage.googleapis.com/etcd/v3.1.5/etcd-v3.1.5-linux-amd64.tar.gz',
            'tar -zxvf etcd-v3.1.5-linux-amd64.tar.gz',
            'mv etcd-v3.1.5-linux-amd64 etcd',
            '/root/etcd/etcd --log-output stdout --name 42.192.52.249 --listen-peer-urls http://0.0.0.0:2380 --listen-client-urls http://0.0.0.0:2379 --advertise-client-urls http://42.192.52.249:2379 --initial-cluster-state new --initial-advertise-peer-urls http://42.192.52.249:2380 --initial-cluster 8.133.161.48=http://8.133.161.48:2380,42.192.52.249=http://42.192.52.249:2380 >/root/etcd/etcd.log &'

        ]
        for c in command_list:
            stdin, stdout, stderr = self.ssh_connection.exec_command(c)
            print(stdout.readlines())
        self.ssh_connection.close()
        pass

    def shutdown(self):
        pass

    def connect_database(self):
        pass

    def write(self, s):
        pass

    def read(self):
        pass

    def cas(self, a, b):
        pass
