# -*- coding: utf-8 -*-
# @Time    : 2022/2/4 17:40
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : log_util.py
import logging


class log:
    def __init__(self, option):
        self.option = option

    def write_log(self, process, type, function, value):
        if not value:
            value = "nil"
        with open("history.edn", 'a') as f:
            f.write('{')
            f.write(":process {}, :type :{}, :f :{}, :value {}".format(str(process), type, function, value))
            f.write("}\n")
        f.close()

