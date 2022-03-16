# -*- coding: utf-8 -*-
# @Time    : 2022/3/10 15:22
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : nemesis.py
import logging


def partition_nemesis(clients, partition_method):
    return nemesis(clients, "partition", partition_method=partition_method)


def clock_nemesis(clients):
    return nemesis(clients, "clock")


class nemesis:
    def __init__(self, clients, mode, partition_method=None):
        self.mode = mode
        self.clients = clients
        self.partition_method = partition_method

    def start(self):
        if self.mode == "partition":
            client_list = []
            for i in range(0, len(self.clients)):
                client_list.append(i+1)
            net_operation_group = self.partition_method(client_list)
            logging.info("start partition nemesis with judge function {}".format(self.partition_method.__name__))

            for key in net_operation_group.keys():
                target_group = []
                for i in net_operation_group[key]:
                    target_group.append(self.clients[i-1].hostname)
                self.clients[key-1].ssh_client.drop_all_net(target_group)
                logging.info("isolated [{}] and [{}]".format(self.clients[key - 1].hostname, ",".join(target_group)))

    def stop(self):
        if self.mode == "partition":
            for client in self.clients:
                client.ssh_client.heal_net()
                logging.info("healed netowrk of {}".format(client.hostname))






# if __name__ == "__main__":
#
#     server_config = util.read_config("../server.yaml")
#     database_config = util.read_config("../database.yaml")
#     # 创建日志对象 用于写文件
#     # 可传入日志的相关配置
#     client_l = []
#     index = 0
#     for node in server_config:
#         new_client = client(server_config[node], None, database_config, None, index)
#         index += 1
#         client_l.append(new_client)
#     n_nemesis = partition_nemesis(client_l, partition_method=majorities_ring)
#     n_nemesis.start()
#     n_nemesis.stop()