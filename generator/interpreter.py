# -*- coding: utf-8 -*-
# @Time    : 2022/2/15
# @Author  : kylezhtao
# @Email   : kylezhtao@outlook.com
# @File    : interpreter.py

"""
负责获取generator产生的op并交予clients/nemesis执行，管理worker生命周期，并记录历史。
"""
import sys
from functools import partial
import time
import threading
import logging
import traceback
import concurrent.futures
import queue
import generator.generator as gen
import util.util as util
from abc import ABC, abstractmethod
from util.globalvars import GlobalVars

"""
When the generator is :pending, this controls the maximum interval before
we'll update the context and check the generator for an operation again.
Measured in seconds.
"""
MAX_PENDING_INTERVAL = 1.0


class TailRecurseException(BaseException):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def tail_call_optimized(g):
    """
    This function decorates a function with tail call
    optimization. It does this by throwing an exception
    if it is it's own grandparent, and catching such
    exceptions to fake the tail call optimization.

    This function fails if the decorated5
    function recurses in a non-tail context.
    """

    def func(*args, **kwargs):
        f = sys._getframe()
        if f.f_back and f.f_back.f_back and f.f_back.f_back.f_code == f.f_code:
            raise TailRecurseException(args, kwargs)
        else:
            while 1:
                try:
                    return g(*args, **kwargs)
                except TailRecurseException as e:
                    args = e.args
                    kwargs = e.kwargs

    func.__doc__ = g.__doc__
    return func


class Worker(ABC):
    @abstractmethod
    def open(self, id):
        """ please implement in subclass """

    @abstractmethod
    def invoke(self, op: dict):
        """ please implement in subclass """

    @abstractmethod
    def close(self):
        """ please implement in subclass """


class ClientWorker(Worker):
    def __init__(self, process, client, id):
        self.process = process
        self.client = client
        self.id = id

    def open(self, id):
        clis = GlobalVars.get_clients()
        self.client = clis[id]
        self.id = id
        self.client.connect_db()
        return self

    def invoke(self, op):
        clis = GlobalVars.get_clients()
        if self.process != op['process']:
            # 说明thread发生崩溃，分配了新的process
            # 关闭当前ClientWorker并创建新的
            self.close()

            # 尝试打开新的client
            try:
                self.process = op['process']
                self.client = clis[self.id]
                self.client.connect_db()
            except Exception as e:
                logging.warning("jepsen worker {} {}  >> Error opening client.".format(str(self.id), repr(e)))
                self.client = None
                op_fail = op.copy()
                op_fail.update({
                    "type": "info",
                    "error": traceback.format_exc() + " >> no client."
                })
                return op_fail

            # 使用新的client去执行op
            return self.invoke(op)
        elif self.client is None:
            op_fail = op.copy()
            op_fail.update({
                "type": "info",
                "error": traceback.format_exc() + " >> no client."
            })
            return op_fail
        else:
            return self.client.operate(op)

    def close(self):
        if self.client:
            self.client.disconnect_db()
            self.client = None


class NemesisWorker(Worker):
    def __init__(self):
        nemesis = GlobalVars.get_nemesis()
        self.nemesis = nemesis

    def open(self, id):
        return self

    def invoke(self, op):
        f = op["f"]
        if f == "start":
            return self.nemesis.start()
        elif f == "stop":
            return self.nemesis.stop()

    def close(self):
        return


class ClientNemesisWorker(Worker):
    def __init__(self, node_num):
        self.node_num = node_num

    def open(self, id):
        if isinstance(id, int):
            return ClientWorker(None, None, id % self.node_num)
        else:
            return NemesisWorker()

    def invoke(self, op):
        return

    def close(self):
        return


def client_nemesis_worker(node_num):
    return ClientNemesisWorker(node_num)


def spawn_worker(out: queue, worker, id) -> dict:
    """
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
        _worker = _worker.open(id)
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
                            logging.info("{} got op: {}".format(threading.current_thread().name, op))
                            result = _worker.invoke(op)
                            _out.put(result)
                            exit_flag = False

                except Exception as e:
                    logging.warning("{} {} >> Process {} crashed."
                                    .format(threading.current_thread().name, repr(e), op['process']))
                    # 出错，更改op类型为info
                    op_info = op.copy()
                    op_info.update({
                        "type": "info",
                        "exception": repr(e),
                        "error": traceback.format_exc()
                    })
                    _out.put(op_info)
                    exit_flag = False

        finally:
            _worker.close()
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
    ctx = gen.build_context(test)
    worker_ids = gen.get_all_threads(ctx)
    completions = queue.Queue(maxsize=len(worker_ids))
    node_num = len(test['server'].keys())
    workers = list(map(
        partial(spawn_worker, completions, client_nemesis_worker(node_num)),
        worker_ids))
    invocations = {}
    for worker in workers:
        invocations[worker['id']] = worker['in']
    generator = gen.validate(
        gen.friendly_exceptions(test['generator'])
    )

    try:
        outstanding_0 = 0  # 未完成的op数
        poll_timeout_0 = 0.0
        history_0 = []

        @tail_call_optimized
        def _run_recursive(ctx, gene, outstanding, poll_timeout, history):
            try:
                if poll_timeout != 0.0:
                    finished_op = completions.get(timeout=poll_timeout)
                else:
                    finished_op = completions.get_nowait()
            except queue.Empty:
                finished_op = None
                pass  # 忽略queue内置的超时抛的Empty异常

            if finished_op:
                # print(finished_op)
                cur_thread = gen.process2thread(ctx, finished_op['process'])
                time_taken = util.compute_relative_time()
                finished_op.update({"time": time_taken})  # 更新时间戳
                # 更新时间戳及线程释放信息
                ctx.update({"time": time_taken})
                ctx['free-threads'].add(cur_thread)

                logging.info("jepsen worker {} finished op: {}".format(cur_thread, finished_op))
                gene2 = gen.update(gene, test, ctx, finished_op)

                if cur_thread == 'nemesis' or finished_op['type'] != 'info':
                    pass
                else:  # 崩溃的线程（不包括nemesis线程）应该分配新的标识符
                    ctx['workers'][cur_thread] = gen.next_process(ctx, cur_thread)

                if goes_in_history(finished_op):
                    history.append(finished_op)
                # 记录历史并继续
                return _run_recursive(ctx, gene2, outstanding - 1, 0.0, history)

            else:
                time_taken = util.compute_relative_time()
                ctx.update({"time": time_taken})
                res = gen.op(gene, test, ctx)
                if res is None:
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
                else:
                    op_var, gene2 = res[0], res[1]
                    # print(op_var)
                    if op_var == 'pending':
                        return _run_recursive(ctx, gene, outstanding,
                                              MAX_PENDING_INTERVAL, history)

                    else:  # 得到一个op invocation
                        # 时间未到，还不能处理
                        if time_taken < op_var['time']:
                            return _run_recursive(ctx, gene, outstanding,
                                                  op_var['time'] - time_taken, history)
                        else:
                            cur_thread = gen.process2thread(ctx, op_var['process'])
                            in_queue = invocations[cur_thread]
                            in_queue.put_nowait(op_var)
                            # 更新时间戳及线程占用信息
                            ctx.update({"time": op_var['time']})
                            ctx['free-threads'].remove(cur_thread)
                            gene2 = gen.update(gene2, test, ctx, op_var)

                            if goes_in_history(op_var):
                                history.append(op_var)

                            return _run_recursive(ctx, gene2, outstanding + 1, 0.0, history)

        return _run_recursive(ctx, generator, outstanding_0, poll_timeout_0, history_0)

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
