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
        root_path = self.ssh_client.pwd() + "/tmp/"
        self.ssh_client.wget(url="https://storage.googleapis.com/etcd/v3.1.5/etcd-v3.1.5-linux-amd64.tar.gz")
        self.ssh_client.mkdir(root=root_path, filename="etcd")
        self.ssh_client.unzip(file_name="{}etcd-v3.1.5-linux-amd64.tar.gz".format(root_path),
                              opts={
                                  "-C": root_path + "/etcd",
                                  "--strip-components": 1
                              })
        self.ssh_client.touch(root=root_path, filename="etcd.log")
        self.ssh_client.exec_sudo_command(command="{}etcd/etcd".format(root_path),
                                          opts={
                                              "--log-output": "stdout",
                                              "--name": self.hostname,
                                              "--listen-peer-urls": "http://0.0.0.0:2380",
                                              "--listen-client-urls": "http://0.0.0.0:2379",
                                              "--advertise-client-urls": "http://{0}:2379".format(self.hostname),
                                              "--initial-cluster-state": "new",
                                              "--initial-advertise-peer-urls": "http://{0}:2380".format(self.hostname),
                                              "--initial-cluster": self.initial_cluster,
                                              "1>{}etcd.log".format(root_path): ""
                                          })

    def shutdown(self):
        root_path = self.ssh_client.pwd() + "/*"
        self.ssh_client.kill_by_process("etcd")
        self.ssh_client.exec_sudo_command("rm -rf {}".format(root_path))

    def connect_database(self):
        return etcd3.client(host=self.hostname, port=self.port)
