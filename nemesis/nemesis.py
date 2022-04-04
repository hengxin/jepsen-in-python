# -*- coding: utf-8 -*-
# @Time    : 2022/3/10 15:22
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : nemesis.py
import logging
from nemesis.mode.partition_nemesis import partition_nemesis
from nemesis.mode.clock_nemesis import clock_nemesis
from nemesis.mode.kill_nemesis import kill_nemesis
from nemesis.mode.pause_nemesis import pause_nemesis
from nemesis.judge import majority, majorities_ring, one, primaries, minority_third


def nemesis_partition(clients, partition_method):
    return partition_nemesis(clients, partition_method=partition_method)


def nemesis_clock(clients, step=60):
    return clock_nemesis(clients, step)


def nemesis_kill(clients):
    return kill_nemesis(clients)


def nemesis_pause(clients):
    return pause_nemesis(clients)


class nemesis:
    def __init__(self, clients, nemesis_config):
        mode = nemesis_config["mode"]
        if mode == "partition":
            if "partition_method" in nemesis_config:
                self.n = nemesis_partition(clients, eval(nemesis_config["partition_method"]))
            else:
                logging.error("Please select a partition_method for nemesis!")
                raise Exception("Config Error")
        elif mode == "clock":
            if "step" in nemesis_config:
                self.n = nemesis_clock(clients, nemesis_config["step"])
            else:
                self.n = nemesis_clock(clients)
        elif mode == "kill":
            self.n = nemesis_kill(clients)
        elif mode == "pause":
            self.n = nemesis_pause(clients)
        else:
            self.n = None

    def start(self):
        if self.n:
            self.n.start()
        pass

    def stop(self):
        if self.n:
            self.n.stop()
        pass

