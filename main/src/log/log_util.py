# -*- coding: utf-8 -*-
# @Time    : 2022/2/4 17:40
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : log_util.py
import logging

class log:
    def __init__(self, option):
        self.option = option
        self.file = self.new_history_file(option.type)

    @staticmethod
    def new_history_file(type):
        if type == "history":
            return "file_history"
        elif type == "log":
            return "file_log"

    def write_log(self, message):
        with open(self.file, 'w') as f:
            logging.log(message)
            f.write(message)
