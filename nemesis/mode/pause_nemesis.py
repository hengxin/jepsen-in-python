# -*- coding: utf-8 -*-
# @Time    : 2022/3/25 0:58
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : pause_nemesis.py

import random
import logging

from util.globalvars import GlobalVars


class pause_nemesis:
    def __init__(self, clients):
        self.clients = clients
        self.paused_client = None
        self.killed_index = None

    # 随机关掉一个服务器上的数据库，并将它从列表中移除
    def start(self):
        index = random.randint(0, len(self.clients) - 1)
        hostname = self.clients[index].hostname
        logging.info("start kill nemesis to shut down db on client {}".format(hostname))
        self.paused_client = self.clients[index]
        self.clients[index].shutdown_db()
        self.clients[index] = None
        self.killed_index = index
        return {"type": "info", "f": "start", "value": "killed db on client '{}'".format(hostname), "process": "nemesis"}

    # 恢复这个clients与数据库间的连接，重新加入列表
    def stop(self):
        if not self.killed_index:
            return {"type": "info", "f": "stop", "value": "do nothing", "process": "nemesis"}
        hostname = self.paused_client.hostname
        logging.info("start recover the db on client {}".format(hostname))
        self.paused_client.recover()
        self.clients[self.killed_index] = self.paused_client
        GlobalVars.set_clients(self.clients)
        self.killed_index = None
        return {"type": "info", "f": "stop", "value": "recovered the db on client '{}'".format(hostname), "process": "nemesis"}
