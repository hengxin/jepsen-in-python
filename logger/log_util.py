# -*- coding: utf-8 -*-
# @Time    : 2022/2/4 17:40
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : log_util.py
import logging
import time
from logging.handlers import TimedRotatingFileHandler
import coloredlogs


class log:
    def __init__(self, option):
        self.option = option
        self.history_file = "histories/history-{}.edn".format(time.time())
        self.log_file = "logs/logger-{}.logger".format(time.time())
        logger = logging.getLogger()
        fmt = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s:%(lineno)s] %(message)s"
        formatter = logging.Formatter(fmt)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        fh = TimedRotatingFileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(fh)
        coloredlogs.install(fmt=fmt,
                            level=logging.INFO,
                            logger=logger)

    def write_history(self, process, type, function, value, time):
        if not value:
            value = "nil"
        if value.__class__ == list:
            value = "[{}]".format(",".join(str(i) for i in value))
        with open(self.history_file, 'a') as f:
            f.write('{')
            f.write(":process {}, :type :{}, :f :{}, :value {}, :time {}".format(str(process), type, function, value, time))
            f.write("}\n")
        f.close()
