# -*- coding: utf-8 -*-
# @Time    : 2022/3/28 13:04
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : checker.py
import os


class checker:
    # models 可选参数 cas-register, mutex, register
    # algos 可选参数 competition, wgl, linear
    def __init__(self, file_path, checker_config):
        if "models" in checker_config:
            self.models = checker_config["models"]
        else:
            self.models = "cas-register"
        if "algos" in checker_config:
            self.algos = checker_config["algos"]
        else:
            self.algos = "competition"
        self.file_path = file_path
        pass

    def check(self):
        result = os.popen(
            "java -jar ./bin/knossos-0.3.9-SNAPSHOT-standalone.jar --model {} --algorithm {} {}".format(self.models,
                                                                                                        self.algos,
                                                                                                        self.file_path))
        for i in result.readlines():
            print(i)
