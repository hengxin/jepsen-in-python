# -*- coding: utf-8 -*-
# @Time    : 2022/2/15 16:35
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : pyjepsen.py
import logging

from checker.checker import checker
from util import util
from client.client import client
from logger.log_util import log
from threading import Thread
from nemesis.nemesis import nemesis
from nemesis.judge import *
import time
import os
import random
from fastcore.transform import Pipeline
from functools import partial
from generator import generator as gen, interpreter as gen_inter
from util.globalvars import GlobalVars


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


def cas():
    return {
        "type": "invoke",
        "f": "cas",
        "value": [str(random.randint(1, 5)), str(random.randint(1, 5))]
    }


if __name__ == '__main__':
    jepsen_config = util.read_config("config.yaml")
    server_config = jepsen_config["server"]
    database_config = jepsen_config["database"]
    nemesis_config = jepsen_config["nemesis"]
    checker_config = jepsen_config["checker"]
    logger = log({})  # 可传入日志的相关配置
    # 1. 根据自己实际测试需要配置组装generator
    jepsen_config["generator"] = Pipeline([
        gen.mix,
        # partial(gen.stagger, 1),
        partial(gen.nemesis, None),
        partial(gen.time_limit, 600000)
    ])([read, write, cas])

    jepsen_clients = []
    try:
        # 2. 创建所测试的分布式数据库节点对应的clients
        for node in server_config:
            new_client = client(server_config[node], database_config, operation)
            jepsen_clients.append(new_client)

        # 3. setup数据库
        for client in jepsen_clients:
            t = Thread(target=client.setup_db())
            t.start()
        time.sleep(20)

        # 4. 创建nemesis
        jepsen_nemesis = nemesis(jepsen_clients, nemesis_config)

        # 将初始化的clients和nemesis注入globalvars
        GlobalVars.set_clients(jepsen_clients)
        GlobalVars.set_nemesis(jepsen_nemesis)

        # 5.1 运行generator，获得op结果日志（dict格式）
        op_exec_history = util.with_relative_time(
            gen_inter.run, jepsen_config
        )

        # 5.2 运行时dict日志转换为knossos可识别的clojure的Map格式日志文件
        for op_result in op_exec_history:
            logger.write_history(op_result['process'], op_result['type'], op_result['f'], op_result['value'])

        # 6. 传入日记文件创建checker
        jepsen_checker = checker(logger.history_file, checker_config)

        # try:
        #     for client in client_list:
        #         client.connect_db()
        #     # 把list交给generator去操作
        #     method_list = [write, read, cas]
        #     client_list[0].operate(method_list[0])
        #     for i in range(30):
        #         client_list[random.randint(0, len(client_list) - 1)].operate(
        #             method_list[random.randint(0, len(method_list) - 1)])
        #     jepsen_nemesis.start()
        #     for i in range(30):
        #         client_list[random.randint(0, len(client_list) - 1)].operate(
        #             method_list[random.randint(0, len(method_list) - 1)])
        #     jepsen_nemesis.stop()
        #     for i in range(30):
        #         client_list[random.randint(0, len(client_list) - 1)].operate(
        #             method_list[random.randint(0, len(method_list) - 1)])
        # except Exception:
        #     logging.error("somthing wrong")
        #     logging.error(Exception.with_traceback())
        # 8. 调用knossos验证数据一致性
        jepsen_checker.check()
    finally:
        # 7. shutdown数据库
        for client in jepsen_clients:
            client.shutdown_db()
