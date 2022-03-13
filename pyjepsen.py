# -*- coding: utf-8 -*-
# @Time    : 2022/2/15 16:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : pyjepsen.py
import logging
from util import util
from client.client import client
from logger.log_util import log
from threading import Thread
import time
import os
import random


def operation(database_connection, history):
    function_name = history["f"]
    try:
        if function_name == "write":
            database_connection.put("foo", history["value"])
            return {
                "type": "ok",
                "f": "write",
                "value": history["value"]
            }
        elif function_name == "read":
            read_result = database_connection.get("foo")
            return {
                "type": "ok",
                "f": "read",
                "value": int(read_result[0]) if read_result[0] else None
            }
        elif function_name == "cas":
            cas_result = database_connection.replace("foo", history["value"][0], history["value"][1])
            return {
                "type": "ok" if cas_result else "fail",
                "f": "cas",
                "value": history["value"]
            }
    except Exception:
        logging.error("somthing wrong")
        logging.error(Exception)
        return {
                 "type": "info",
                 "f": function_name,
                 "value": None
             }
        pass
    # finally:
    #     return {
    #         "type": "fail",
    #         "f": function_name,
    #         "value": None
    #     }


def write():
    return {
        "type": "invoke",
        "f": "write",
        "value": str(random.randint(1, 5))
    }


def read():
    return {
        "type": "invoke",
        "f": "read",
        "value": None
    }

    # compare and set


def cas():
    return {
        "type": "invoke",
        "f": "cas",
        "value": [str(random.randint(1, 5)), str(random.randint(1, 5))]
    }


if __name__ == '__main__':
    server_config = util.read_config("server.yaml")
    database_config = util.read_config("database.yaml")
    logger = log({})
    # 创建日志对象 用于写文件
    # 可传入日志的相关配置
    client_list = []
    index = 0
    for node in server_config:
        new_client = client(server_config[node], logger, database_config, operation, index)
        index += 1
        client_list.append(new_client)
    for client in client_list:
        t = Thread(target=client.setup_db())
        t.start()
    time.sleep(20)
    try:
        for client in client_list:
            client.connect_db()
        # 把list交给generator去操作
        method_list = [write, read, cas]
        print(client_list[0].hostname)
        client_list[0].operate(method_list[0])
        for i in range(30):
            client_list[random.randint(0, len(client_list) - 1)].operate(
                method_list[random.randint(0, len(method_list) - 1)])
        client_list[0].ssh_client.drop_all_net(
            ["42.192.52.249", "public-cd-a3.disalg.cn", "public-cd-a4.disalg.cn", "public-cd-a5.disalg.cn"])
        for i in range(30):
            client_list[random.randint(0, len(client_list) - 1)].operate(
                method_list[random.randint(0, len(method_list) - 1)])
        client_list[0].ssh_client.heal_net()
        for i in range(30):
            client_list[random.randint(0, len(client_list) - 1)].operate(
                method_list[random.randint(0, len(method_list) - 1)])
    except Exception:
        logging.error("somthing wrong")
        logging.error(Exception.with_traceback())

    for client in client_list:
        client.shutdown_db()
    # knossos打了个包 先这样用着
    result = os.popen(
        "java -jar knossos-0.3.9-SNAPSHOT-standalone.jar --model cas-register {}".format(logger.history_file))
    for i in result.readlines():
        print(i)
