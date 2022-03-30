# -*- coding: utf-8 -*-
# @Time    : 2022/3/25 0:58
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : pause_nemesis.py

import random
import logging


class pause_nemesis:
    def __init__(self, clients):
        self.clients = clients
        self.paused_client = None

    # 随机关掉一个服务器上的数据库，并将它从列表中移除
    def start(self):
        index = random.randint(0, len(self.clients) - 1)
        hostname = self.clients[index].hostname
        logging.info("start kill nemesis to shut down db on client {}".format(hostname))
        self.paused_client = self.clients[index]
        self.clients[index].shutdown_db()
        self.clients.remove(self.paused_client)
        logging.info("killed db on client {}".format(hostname))
        pass

    # 恢复这个clients与数据库间的连接，重新加入列表
    def stop(self):
        hostname = self.paused_client.hostname
        logging.info("start recover the db on client {}".format(hostname))
        self.paused_client.recover()
        logging.info("recoverd the db on client {}".format(hostname))
        pass
