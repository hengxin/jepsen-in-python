# -*- coding: utf-8 -*-
# @Time    : 2022/3/19 13:01
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : partition_nemesis.py
import logging


class partition_nemesis:
    def __init__(self, clients, partition_method=None):
        self.clients = clients
        self.partition_method = partition_method

    # 根据传入的分割算法对节点进行分割
    # 关闭同一组中的网络通信
    def start(self):
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
        return {"type": "info", "f": "start", "process": "nemesis", "value": "start partition nemesis with judge function {}".format(self.partition_method.__name__)}

    # 恢复网络
    def stop(self):
        for client in self.clients:
            client.ssh_client.heal_net()
            logging.info("healed netowrk of {}".format(client.hostname))
        return {"type": "info", "f": "stop", "process": "nemesis", "value": "stop partition nemesis with judge function {}".format(self.partition_method.__name__)}
