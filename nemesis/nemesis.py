# -*- coding: utf-8 -*-
# @Time    : 2022/3/10 15:22
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : nemesis.py


def partition_nemesis(clients):
    return nemesis(clients, "partition")


def clock_nemesis(clients):
    return nemesis(clients, "clock")


class nemesis:
    def __init__(self, clients, mode):
        self.mode = mode
        self.clients = clients
        self.list = ()
        pass