# -*- coding: utf-8 -*-
# @Time    : 2022/3/25 0:58
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : kill_nemesis.py
import random
import logging


class kill_nemesis:
    def __init__(self, clients):
        self.clients = clients

    # 随机关掉一个服务器上的数据库，并将它从列表中移除
    def start(self):
        index = random.randint(0, len(self.clients) - 1)
        hostname = self.clients[index].hostname
        logging.info("start kill nemesis to shut down db on client {}".format(hostname))
        self.clients[index].shutdown_db()
        self.clients[index] = None
        logging.info("killed db on client {}".format(hostname))
        return {"type": "info", "f": "start", "value": "killed db on client {}".format(hostname)}

    def stop(self):
        # do noting
        return {"type": "info", "f": "stop", "value": "do nothing"}
