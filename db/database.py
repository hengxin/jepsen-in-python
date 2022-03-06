# -*- coding: utf-8 -*-
# @Time    : 2022/2/10 22:49
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : database.py
import etcd3


class database_op:
    def __init__(self, ssh_client, hostname, logger, config):
        self.ssh_client = ssh_client
        self.hostname = hostname
        self.port = config["port"]
        self.logger = logger
        self.initial_cluster = config["initial_cluster"]

    def setup(self):
        self.ssh_client.wget(url="https://storage.googleapis.com/etcd/v3.1.5/etcd-v3.1.5-linux-amd64.tar.gz",
                             save_path="/root")
        self.ssh_client.unzip(file_name="/root/etcd-v3.1.5-linux-amd64.tar.gz")
        self.ssh_client.mv("/root/etcd-v3.1.5-linux-amd64", "/root/etcd")
        self.ssh_client.exec_command(command="/root/etcd/etcd",
                                     opts={
                                         "--log-output": "stdout",
                                         "--name": self.hostname,
                                         "--listen-peer-urls": "http://0.0.0.0:2380",
                                         "--listen-client-urls": "http://0.0.0.0:2379",
                                         "--advertise-client-urls": "http://{0}:2379".format(self.hostname),
                                         "--initial-cluster-state": "new",
                                         "--initial-advertise-peer-urls": "http://{0}:2380".format(self.hostname),
                                         "--initial-cluster": self.initial_cluster
                                     })

    def shutdown(self):
        self.ssh_client.kill_by_process("etcd")
        self.ssh_client.exec_command("rm -rf /root/*")

    def connect_database(self):
        return etcd3.client(host=self.hostname, port=self.port)

