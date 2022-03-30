# -*- coding: utf-8 -*-
# @Time    : 2022/3/28 13:04
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : checker.py
import os


class checker:
    def __init__(self):
        pass

    def check(self):
        result = os.popen(
            "java -jar ./bin/knossos-0.3.9-SNAPSHOT-standalone.jar --model cas-register {}".format("C:/Users/jiangnanweishao/PycharmProjects/jepsen-in-python/histories/history-1647864354.9122956.edn"))
        for i in result.readlines():
            print(i)

if __name__ == "__main__":
    c = checker()
    c.check()