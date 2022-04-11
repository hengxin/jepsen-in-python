# -*- coding: utf-8 -*-
# @Time    : 2022/2/15
# @Author  : kylezhtao
# @Email   : kylezhtao@outlook.com
# @File    : interpreter.py

"""
负责翻译generator产生的op，处理worker线程，生成与clients和nemeses交互的线程，并记录历史。
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

from pyjepsen import jepsen_clients, jepsen_nemesis

# logging.basicConfig(level=logging.DEBUG)

"""
When the generator is :pending, this controls the maximum interval before
we'll update the context and check the generator for an operation again.
Measured in microseconds.
"""
MAX_PENDING_INTERVAL = 1


class Worker:
    def open(self, id):
        raise Exception('subclass must implement this method')

    def invoke(self, op: dict):
        raise Exception('subclass must implement this method')

    def close(self):
        raise Exception('subclass must implement this method')


class ClientWorker(Worker):
    def __init__(self, process, client):
        self.process = process
        self.client = client
        self.id = None

    def open(self, id):
        self.client = jepsen_clients[id]
        self.id = id
        self.client.connect_db()
        return self

    def invoke(self, op):
        if self.process != op['process']:
            # 说明thread发生崩溃，分配了新的process
            # 关闭当前ClientWorker并创建新的
            self.close()

            # 尝试打开新的client
            try:
                self.client = jepsen_clients[self.id]
                self.client.connect_db()
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

            # 使用新的client去执行op
            self.invoke(op)
        else:
            self.client.operate(op)

    def close(self):
        if self.client:
            self.client.disconnect_db()
            self.client = None


class NemesisWorker(Worker):
    def __init__(self):
        self.nemesis = jepsen_nemesis

    def open(self, id):
        return self

    def invoke(self, op):
        return self.nemesis.start()

    def close(self):
        return


class ClientNemesisWorker(Worker):
    def open(self, id):
        if isinstance(id, int):
            return ClientWorker(None, None)
        else:
            return NemesisWorker()

    def invoke(self, op):
        return

    def close(self):
        return


def client_nemesis_worker():
    return ClientNemesisWorker()


def spawn_worker(test, out: queue, worker, id) -> dict:
    """
    :param test:
    :param out: 接收已完成op的队列
    :param worker: worker对象
    :param id: worker的id
    :return: dict
    """

    _in = queue.Queue(maxsize=1)  # 阻塞队列
    old_name = threading.current_thread().name

    # 扔进线程池里选一个线程运行
    def evaluate(_worker, _in: queue, _out: queue):
        threading.current_thread().name = "jepsen worker " + str(id)
        _worker = _worker.open(test, id)
        exit_flag = False
        try:
            while True:
                if exit_flag:
                    break
                op = _in.get()  # 阻塞获取元素
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
                        case _:  # invoke
                            result = _worker.invoke(test, op)
                            _out.put(result)
                            logging.info(str(result))
                            exit_flag = False

                except Exception as e:
                    logging.warning(repr(e) + " >> Process {} crashed.".format(op['process']))
                    # 出错，更改op类型为info
                    op_info = op.copy()
                    op_info.update({
                        "type": "info",
                        "exception": repr(e),
                        "error": traceback.format_exc()
                    })
                    _out.put(op_info)
                    exit_flag = True

        finally:
            _worker.close(test)
            threading.current_thread().name = old_name

    # 目前使用concurrent.futures模块新建线程去evaluate，效果待验证
    executor = concurrent.futures.ThreadPoolExecutor()
    future = executor.submit(evaluate, worker, _in, out)

    return {
        "id": id,  # worker id
        "in": _in,  # 将invocation交给worker
        "future": future
    }


def goes_in_history(op) -> bool:
    """
    :param op:
    :return: True or False
    """
    if not op:
        return False
    if op['type'] == 'sleep' or op['type'] == 'log':
        return False
    else:
        return True


def run(test):
    """
    :param test:
    :return: history
    """
    # gen.init()
    ctx = gen.build_context(test)
    worker_ids = gen.get_all_threads(ctx)
    completions = queue.Queue(maxsize=len(worker_ids))
    workers = list(map(
        partial(spawn_worker, test, completions, client_nemesis_worker()),
        worker_ids))
    invocations = {}
    for worker in workers:
        invocations[worker['id']] = worker['in']
    gene = gen.validate(
        gen.friendly_exceptions(test['generator'])
    )

    try:
        outstanding_0 = 0  # 未完成的op数
        poll_timeout_0 = 0.0
        history_0 = []

        def _run_recursive(ctx, gene, outstanding, poll_timeout, history):
            try:
                cur_op = None if completions.empty() else completions.get(timeout=poll_timeout)
            except queue.Empty:
                cur_op = None
                pass  # 忽略queue内置的超时抛的Empty异常

            if cur_op:
                # print(cur_op)
                cur_thread = gen.process2thread(ctx, cur_op['process'])
                time_taken = util.compute_relative_time()
                cur_op.update({"time": time_taken})  # 更新时间戳
                # 更新时间戳及线程释放信息
                ctx.update({"time": time_taken})
                ctx['free-threads'].add(cur_thread)

                gene = gen.update(gene, test, ctx, cur_op)

                if cur_thread == 'nemesis' or cur_op['type'] != 'info':
                    pass
                else:  # 崩溃的线程（不包括nemesis线程）应该分配新的标识符
                    ctx['workers'][cur_thread] = gen.next_process(ctx, cur_thread)

                if goes_in_history(cur_op):
                    history.append(cur_op)
                # 记录历史并继续
                return _run_recursive(ctx, gene, outstanding - 1, 0, history)

            else:
                time_taken = util.compute_relative_time()
                ctx.update({"time": time_taken})
                if res := gen.op(gene, test, ctx):
                    cur_op, gene2 = res[0], res[1]

                    if cur_op is None:
                        if outstanding > 0:
                            # 没有下一个op，但仍有未完成的op
                            # 等待worker
                            return _run_recursive(ctx, gene, outstanding,
                                                  MAX_PENDING_INTERVAL, history)
                        else:
                            # 完成，告知worker退出
                            for thread, in_queue in invocations.items():
                                in_queue.put({"type": "exit"})

                            # 阻塞获取future结果
                            for worker in workers:
                                fut = worker['future']
                                res = fut.result()
                                msg = "{}result:{!r}"
                                logging.debug(msg.format(fut, res))
                            return history

                    elif cur_op == 'pending':
                        return _run_recursive(ctx, gene, outstanding,
                                              MAX_PENDING_INTERVAL, history)

                    else:  # 得到一个op
                        # 时间未到，还不能处理
                        if time_taken < cur_op['time']:
                            return _run_recursive(ctx, gene, outstanding,
                                                  cur_op['time'] - time_taken, history)
                        else:
                            cur_thread = gen.process2thread(ctx, cur_op['process'])
                            in_queue = invocations[cur_thread]
                            in_queue.put(cur_op)
                            # 更新时间戳及线程占用信息
                            ctx.update({"time": cur_op['time']})
                            ctx['free-threads'].remove(cur_thread)
                            gene2 = gen.update(gene2, test, ctx, cur_op)

                            if goes_in_history(cur_op):
                                history.append(cur_op)

                            return _run_recursive(ctx, gene2, outstanding + 1, 0, history)
                else:
                    return history

        return _run_recursive(ctx, gene, outstanding_0, poll_timeout_0, history_0)

    except Exception as e:
        logging.info("Shutting down workers after abnormal exit")

        # 确保worker退出
        # 1. 尝试取消每个worker，仅*一次*
        for worker in workers:
            fut = worker['future']
            res = fut.cancel()
            msg = "{} is cancelled?:{!r}"
            logging.debug(msg.format(fut, res))

        # 2. 若1无效，轮询等所有worker完成后退出，并更新队列状态
        it = iter(workers)
        cursor = next(it)
        while True:
            try:
                in_queue, fut = cursor['in'], cursor['future']
                if fut.done():
                    cursor = next(it)
                else:
                    try:
                        in_queue.put_nowait({"type": "exit"})
                    except queue.Full:
                        pass  # 忽略满异常
            except StopIteration:
                break
        raise e
