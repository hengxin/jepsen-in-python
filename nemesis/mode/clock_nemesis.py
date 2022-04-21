# -*- coding: utf-8 -*-
# @Time    : 2022/3/19 13:06
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : clock_nemesis.py
import logging
import math
import time
import datetime


class clock_nemesis:
    def __init__(self, clients, step=60):
        self.clients = clients
        self.step = step

    # 随机修改每个服务器的时间
    def start(self):
        # 首先获取服务器的中间位置不改变其时间
        # 5->2 4->2 1->0
        # 0 1 2 3 4
        half = math.floor(len(self.clients) / 2)
        # 然后获取每个服务器的当前时间,根据他在数组中的位置去设置他的新时间
        for i in range(0, len(self.clients)):
            now_time = datetime.datetime.strptime(self.clients[i].ssh_client.get_time(), "%a %b %d %H:%M:%S %Y")
            new_time = now_time + datetime.timedelta(seconds=self.step * (i - half))
            self.clients[i].ssh_client.set_time(new_time)
        logging.info("changed the time of the all clients")
        return {"type": "info", "f": "start", "value": "changed the time of the all clients", "process": "nemesis"}

    # 恢复每个服务器的时间
    def stop(self):
        for client in self.clients:
            client.ssh_client.exec_sudo_command("ntpdate -p 1 -b 0.cn.pool.ntp.org")
            logging.info("reset the time of {}".format(client.hostname))
        return {"type": "info", "f": "stop", "value": "reset the time of the all clients", "process": "nemesis"}
