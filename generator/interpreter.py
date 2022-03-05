# -*- coding: utf-8 -*-
# @Time    : 2022/2/15
# @Author  : kylezhtao
# @Email   : kylezhtao@outlook.com
# @File    : interpreter.py

"""
负责翻译generator的操作，处理worker线程，生成与clients和nemeses交互的线程，并记录历史。
"""
from functools import partial
import time
import threading
import logging
import traceback
import concurrent.futures
import queue
import generator.generator as gen
import client.client as cli
import util.util as util
import nemesis.nemesis as nemesis

logging.basicConfig(level=logging.DEBUG)

"""
When the generator is :pending, this controls the maximum interval before
we'll update the context and check the generator for an operation again.
Measured in microseconds.
"""
MAX_PENDING_INTERVAL = 1000

# Interface
class Worker:
    def open(self, test: dict, id):
        """
        :param test:
        :param id:
        :return:
        """
        raise Exception('subclass must implement this method')

    def invoke(self, test: dict, op: dict):
        """
        :param test:
        :param op:
        :return:
        """
        raise Exception('subclass must implement this method')

    def close(self, test: dict):
        """
        :param test:
        :return:
        """
        raise Exception('subclass must implement this method')


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


def spawn_worker(test, out: queue, worker, id) -> dict:
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


def goes_in_history(op) -> bool:
    """
    Should this operation be journaled to the history? We exclude :log and
    :sleep ops right now.
    :param op:
    :return: True or False
    """
    if op['type'] == 'sleep' or op['type'] == 'log':
        return False
    else:
        return True


def run(test):
    """
    :param test:
    :return:
    """
    gen.init()
    ctx = gen.context(test)
    worker_ids = gen.all_threads(ctx)
    completions = queue.Queue(maxsize=len(worker_ids))
    workers = list(map(
        partial(spawn_worker, test, completions),
        worker_ids))
    invocations = {}
    for worker in workers:
        invocations[worker['id']] = worker['in']
    gene = gen.validate(gen.friendly_exceptions(test['generator']))

    try:
        outstanding_0 = 0  # 未完成的操作数
        poll_timeout_0 = 0 # 单位：秒
        history_0 = []     #
        def _run_recursive(ctx, gene, outstanding, poll_timeout, history):
            cur_op = None if completions.empty() else completions.get(timeout=poll_timeout)
            if cur_op:
                print(cur_op['completed'])
                cur_thread = gen.process2thread(ctx, cur_op['process'])
                time_taken = util.compute_relative_time()
                cur_op.update({"time": time_taken})  # 更新时间戳
                ctx.update({  # 更新时间戳及线程释放信息
                    "time": time_taken,
                    # ctx['free-threads']类型为set
                    "free-threads": ctx['free-threads'].add(cur_thread)
                })


                gene = gen.update(gene, test, ctx, cur_op)

                if cur_thread == 'nemesis' or cur_op['type'] != 'info':
                    pass
                else: # 崩溃的线程（不包括nemesis线程）应该分配新的标识符
                    ctx['workers'][cur_thread] = gen.next_process(ctx, cur_thread)

                if goes_in_history(cur_op):
                    history.append(cur_op)

                _run_recursive(ctx, gene, outstanding-1 ,0, history)

            else:


        _run_recursive(ctx, gene, outstanding_0, poll_timeout_0, history_0)

    except Exception as e:

