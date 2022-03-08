# -*- coding: utf-8 -*-
# @Time    : 2022/2/25
# @Author  : kylezhtao
# @Email   : kylezhtao@outlook.com
# @File    : generator.py
import logging
import random
from inspect import isfunction


class Generator:
    def update(self, gen, test, context, event):
        """
        :param gen:
        :param test:
        :param context:
        :param event:
        :return:
        """
        if gen is None:
            return None
        elif isfunction(gen):
            return gen
        elif isinstance(gen, dict):
            return gen

    def op(self, gen, test, context):
        """
        :param gen:
        :param test:
        :param context:
        :return:
        """
        if gen is None:
            return None
        elif isfunction(gen):
            res = gen(test, context) \
                if gen.__code__.co_argcount == 2 else gen()
            if res:
                return self.op([res, gen], test, context)
            else:
                return None
        elif isinstance(gen, dict):  # 本身已经是一个op
            op = fill_in_op(gen, context)
            return [op, gen if op == 'pending' else None]


'''
一些helper函数
'''


def build_context(test):
    """ 通过test构建context """
    threads = ["nemesis"] + list(range(test['concurrency']))
    threads = set(threads)  # TODO: 原实现中使用了bifurcan包的Set（其提供高效率的nth），具体区别待验证

    return {
        "time": 0,
        "free-threads": threads,
        "workers": dict(zip(threads, threads))
    }


def get_free_processes(context):
    return [context['workers'][free_thread]
            for free_thread in context['free-threads']]


def get_all_processes(context):
    return context['workers'].values()


def get_some_free_process(context):
    free_threads = context['free-threads']
    if len(free_threads) == 0:
        return None
    else:
        return context['workers'][random.choice(list(free_threads))]


def get_free_threads(context):
    return context['free-threads']


def get_all_threads(context):
    return context['workers'].keys()


def process2thread(context, process):
    return [t for t, p in context['worker'].items() if p == process][0]


def thread2process(context, thread):
    return context['workers'][thread]


def next_process(context, thread):
    """仅在 *全局的* context中使用，用以在某线程崩溃时给出该线程的下一个process"""
    if thread != 'nemesis':
        return context['worker'][thread] + \
               len(list(filter(lambda x: x != 'nemesis', get_all_processes(context))))
    else:
        return thread


"""
Generator
"""


def fill_in_op(op, context):
    """ 使用context填补op缺失的键值对字段 type, process, time """
    p = get_some_free_process(context)
    if p:
        if op.get("time") is None: op["time"] = context["time"]
        if op.get("process") is None: op["process"] = p
        if op.get("type") is None: op["type"] = "invoke"
        return op
    else:
        return "pending"
