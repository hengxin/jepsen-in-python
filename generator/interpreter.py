# -*- coding: utf-8 -*-
# @Time    : 2022/2/15
# @Author  : kylezhtao
# @Email   : kylezhtao@outlook.com
# @File    : interpreter.py

"""
负责翻译generator的操作，处理worker线程，生成与clients和nemeses交互的线程，并记录历史。
"""
import time
import threading
import logging
import traceback
import concurrent.futures
import queue
import generator.generator as gen
import client.client as cli
import nemesis.nemesis as nemesis

logging.basicConfig(level=logging.DEBUG)


# Interface
class Worker:
    def open(self, test: dict, id):
        """
        :param test:
        :param id:
        :return:
        """
        raise Exception('子类必须实现该方法')

    def invoke(self, test: dict, op: dict):
        """
        :param test:
        :param op:
        :return:
        """
        raise Exception('子类必须实现该方法')

    def close(self, test: dict):
        """
        :param test:
        :return:
        """
        raise Exception('子类必须实现该方法')


class ClientWorker(Worker):
    def __init__(self, node, process, client):
        self.node = node
        self.process = process
        self.client = client

    def open(self, test, id):
        return self

    def invoke(self, test, op):
        if self.process != op['process'] \
                and not cli.is_reusable(self.client, test):
            # 新process，关闭当前ClientWorker并创建新的
            self.close(test)

            # 尝试打开新的client
            try:
                self.client = cli.open(
                    cli.validate(test['client']),
                    test,
                    self.node,
                )
                self.process = op['process']
            except Exception as e:
                logging.warning(repr(e) + " >> Error opening client.")
                self.client = None
                op_fail = op.copy()
                op_fail.update({
                    "type": "fail",
                    "error": traceback.format_exc() + " >> no client."
                })
                return op_fail

            # 使用新的client再次invoke
            self.invoke(test, op)
        else:
            self.client.invoke(test, op)

    def close(self, test):
        if self.client:
            cli.close(self.client, test)
            self.client = None


class NemesisWorker(Worker):
    def open(self, test, id):
        return self

    def invoke(self, test, op):
        return nemesis.invoke(test['nemesis'], test, op)

    def close(self, test):
        return


class ClientNemesisWorker(Worker):
    def open(self, test, id):
        if isinstance(id, int):
            nodes = test['nodes']
            return ClientWorker(nodes[id % len(nodes)], None, None)
        else:
            return NemesisWorker()

    def invoke(self, test, op):
        return

    def close(self, test):
        return


def spawn_worker(test, out: queue, worker, id):
    """
    :param test:
    :param out: 接收已完成操作的队列
    :param worker: worker对象
    :param id: worker的id
    :return: dict
    """

    _in = queue.Queue(maxsize=1)  # 阻塞队列
    thread_name = "jepsen worker " + str(id)

    def evaluate(_worker, _in: queue, _out: queue):
        _worker = _worker.open(test, id)
        exit_flag = False
        while True:
            if exit_flag:
                break
            op = _in.get()
            try:
                match op['type']:
                    case 'exit':
                        exit_flag = True
                    case 'sleep':
                        time.sleep(op['value'])
                        _out.put(op)
                        exit_flag = False
                    case 'log':
                        logging.info(op['value'])
                        _out.put(op)
                        exit_flag = False
                    case _:
                        logging.info(str(op))
                        _out.put(op)

                        op2 = _worker.invoke(test, op)
                        _out.put(op2)
                        logging.info(str(op2))
                        exit_flag = False

            except Exception as e:
                logging.warning(repr(e) + " >> Process {} crashed.".format(op['process']))
                # 将该op转换为info级别
                op_info = op.copy()
                op_info.update({
                    "type": "info",
                    "exception": repr(e),
                    "error": traceback.format_exc()
                })

            finally:
                _worker.close(test)

    # 具体实现待确定
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    future = executor.submit(evaluate, worker, _in, out)

    return {
        "id": id,
        "in": _in,
        "future": future
    }
