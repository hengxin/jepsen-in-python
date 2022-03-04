# -*- coding: utf-8 -*-
# @Time    : 2022/2/4 17:40
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : log_util.py
import logging


class log:
    def __init__(self, option):
        self.option = option
        self.history_file = "history.edn"
        self.log_file = "log.log"

    def write_history(self, process, type, function, value):
        if not value:
            value = "nil"
        if value.__class__ == list:
            value = "[{}]".format(",".join(str(i) for i in value))
        with open(self.history_file, 'a') as f:
            f.write('{')
            f.write(":process {}, :type :{}, :f :{}, :value {}".format(str(process), type, function, value))
            f.write("}\n")
        f.close()

