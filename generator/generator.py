# -*- coding: utf-8 -*-
# @Time    : 2022/2/25
# @Author  : kylezhtao
# @Email   : kylezhtao@outlook.com
# @File    : generator.py
import logging
import random
import pprint
import copy
from functools import reduce
from inspect import isfunction
from builtins import map as map_builtin, filter as filter_builtin, any as any_builtin


def update(gen, test, context, event):
    if gen is None:
        return None
    elif isfunction(gen):
        return gen
    elif isinstance(gen, dict):
        return gen
    elif isinstance(gen, list):
        if gen:
            cur_gen, rest = gen[0], gen[1:]
            return [update(cur_gen, test, context, event), *rest]
        else:
            return None
    else:  # 非上述基本类型，自建包装类generator
        return gen.update(gen, test, context, event)


def op(gen, test, context):
    if gen is None:
        return None
    elif isfunction(gen):
        res = gen(test, context) \
            if gen.__code__.co_argcount == 2 else gen()
        if res:
            return op([res, gen], test, context)
        else:
            return None
    elif isinstance(gen, dict):  # 本身已经是一个op
        op_var = fill_in_op(gen, context)
        return [op_var, gen if op_var == 'pending' else None]
    elif isinstance(gen, list):
        if gen:
            cur_gen, rest = gen[0], gen[1:]
            if res := op(cur_gen, test, context):
                op_var, gen2 = res[0], res[1]
                return [op_var, [gen2, *rest] if rest else gen2]
            else:
                return op(gen[1:], test, context)
        else:
            return None
    else:  # 非上述基本类型，自建包装类generator
        return gen.op(gen, test, context)


class Generator:
    def update(self, gen, test, context, event):
        """
        :param gen:
        :param test:
        :param context:
        :param event:
        :return: gen'
        """

    def op(self, gen, test, context):
        """
        :param gen:
        :param test:
        :param context:
        :return:
        """


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


def get_free_threads(context) -> set:
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
               len(list(filter_builtin(lambda x: x != 'nemesis', get_all_processes(context))))
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


# def init():

class Validate(Generator):
    def __init__(self, gen):
        self.gen = gen

    def op(self, _, test, context):
        gen = self.gen
        res = op(gen, test, context)
        if res:
            problems = []
            if not (isinstance(res, list) and len(res) == 2):
                problems = ["should return a list of two elements."]
            else:
                op_var, gen2 = res[0], res[1]
                if op_var == 'pending':
                    pass
                else:
                    if isinstance(op_var, dict):
                        problems.append("op value should be 'pending' or a dict")
                    if op_var['type'] not in ['invoke', 'info', 'sleep', 'log']:
                        problems.append("type value should be 'invoke', 'info', 'sleep' or 'log'")
                    if not isinstance(op_var['time'], float):
                        problems.append("time value should be a float")
                    if not op_var['process']:
                        problems.append("no process")
                    if op_var['process'] and op_var['process'] not in get_free_processes(context):
                        problems.append("process {} is not free".format(op_var['process']))

            if problems:
                errmsg = "Generator produced an invalid [op, gen\'] list when asked for an operation:{:>10d}" \
                         "\nThe specific issues are as follows:\n" \
                    .format(res)
                for problem in problems:
                    errmsg += "  -{}".format(problem)
                errmsg += "Generator:\n" \
                          "{:>10d}\n" \
                          "Context:\n" \
                          "{}" \
                    .format(gen, pprint.pformat(context, indent=2))

                raise Exception(errmsg)
            else:
                return [res[0], Validate(res[1])]
        else:
            return None

    def update(self, this, test, context, event):
        return Validate(update(self.gen, test, context, event))


def validate(gen):
    return Validate(gen)


class FriendlyExceptions(Generator):
    def __init__(self, gen):
        self.gen = gen

    def op(self, _, test, context):
        try:
            gen = self.gen
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                return [op_var, FriendlyExceptions(gen2)]
        except Exception as e:
            errmsg = "Generator threw {} when asked for an operation\n" \
                     "Generator:{:>10d}\n" \
                     "Context:{}\n" \
                .format(repr(e), self.gen, context)
            raise Exception(errmsg)

    def update(self, _, test, context, event):
        try:
            if gen2 := update(self.gen, test, context, event):
                return FriendlyExceptions(gen2)
        except Exception as e:
            errmsg = "Generator threw {} when updated with an event.\n" \
                     "Generator:{:>10d}\n" \
                     "Context:{}\n" \
                     "Event:{}"\
                .format(repr(e), self.gen, context, event)
            raise Exception(errmsg)


def friendly_exceptions(gen):
    return FriendlyExceptions(gen)


class Map(Generator):
    def __init__(self, f, gen):
        """
        :param f: 映射函数
        :param gen:
        """
        self.f = f
        self.gen = gen

    def op(self, _, test, context):
        f, gen = self.f, self.gen
        if res := op(gen, test, context):
            op_var, gen2 = res[0], res[1]
            return [op_var if op_var == "pending" else f(op_var), Map(f, gen2)]
        else:
            return None

    def update(self, _, test, context, event):
        return Map(self.f, update(self.gen, test, context, event))


def map(f, gen):
    return Map(f, gen)


def f_map(f, gen):
    """ 将op["f"]转换为另一个给定的函数 """

    def func(op):
        op.update({"f": f})
        return op

    return map(func, gen)


class Filter(Generator):
    def __init__(self, f, gen):
        """
        :param f: 过滤函数
        :param gen:
        """
        self.f = f
        self.gen = gen

    def op(self, _, test, context):
        f, gen = self.f, self.gen
        while True:
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                if op_var == 'pending' or f(op_var):
                    return [op_var, Filter(f, gen2)]
                else:
                    gen = gen2
            else:
                return None

    def update(self, _, test, context, event):
        return Filter(self.f,
                      update(self.gen, test, context, event))


def filter(f, gen):
    return Filter(f, gen)


class OnUpdate(Generator):
    def __init__(self, f, gen):
        """
        :param f: update时调用
        :param gen:
        """
        self.f = f
        self.gen = gen

    def op(self, _, test, context):
        f, gen = self.f, self.gen
        if res := op(gen, test, context):
            op_var, gen2 = res[0], res[1]
            return [op_var, OnUpdate(f, gen2)]
        else:
            return None

    def update(self, this, test, context, event):
        return self.f(this, test, context, event)


def on_update(f, gen):
    """ 包装一个generator，update时调用传入的函数f(this, test, context, event)并返回结果
     f由用户自己编写，用于在update时施加自己需要的控制"""
    return OnUpdate(f, gen)


def on_threads_context(f, context):
    """ helper函数，用于为OnThreads转换context。
    参数f为过滤函数，当一个线程应该包含在context中时返回True
    返回更新后的context """
    target_threads = set()
    for f_thread in context['free-threads']:
        if f(f_thread):
            target_threads.add(f_thread)
    ctx = copy.deepcopy(context)
    target_workers = {}
    for w_thread, w_process in ctx['workers'].items():
        if f(w_thread):
            target_workers.update({w_thread: w_process})

    ctx.update({
        "free-threads": target_threads,
        "workers": target_workers
    })
    return ctx


def on_threads_context_set_param(t_set: set, context, complement=False):
    target_threads = set()
    for f_thread in context['free-threads']:
        if f_thread in t_set:
            target_threads.add(f_thread)
    if complement:
        target_threads = context['free-threads'] - target_threads

    target_workers = {}
    if not complement:
        for w_thread, w_process in context['workers'].items():
            if w_thread in t_set:
                target_workers.update({w_thread: w_process})
    else:
        for w_thread, w_process in context['workers'].items():
            if w_thread not in t_set:
                target_workers.update({w_thread: w_process})

    ctx = copy.deepcopy(context)
    ctx.update({
        "free-threads": target_threads,
        "workers": target_workers
    })
    return ctx


class OnThreads(Generator):
    def __init__(self, f, gen):
        """
        :param f: 过滤函数，当一个线程应该包含在context中时返回True
        :param gen:
        """
        self.f = f
        self.gen = gen

    def op(self, _, test, context):
        f, gen = self.f, self.gen
        if res := op(gen, test, on_threads_context(f, context)):
            op_var, gen2 = res[0], res[1]
            return [op_var, OnThreads(f, gen2)]
        else:
            return None

    def update(self, this, test, context, event):
        if self.f(process2thread(context, event["process"])):
            return OnThreads(self.f,
                             update(self.gen, test, on_threads_context(self.f, context), event))
        else:
            return this


def on_threads(f, gen):
    return OnThreads(f, gen)


class EachThread(Generator):
    def __init__(self, fresh_gen, thr2gen_dict: dict):
        """
        :param fresh_gen: 用于初始化线程状态的generator
        :param thr2gen_dict: thread -> generator的映射字典
        """
        self.fresh_gen = fresh_gen
        self.thr2gen_dict = thr2gen_dict

    def op(self, this, test, context):
        fresh_gen, thr2gen_dict = self.fresh_gen, self.thr2gen_dict
        free, all = context["free-threads"], get_all_threads(context)

        def _op(_thread):
            """ 第一次调用将给每个线程初始化分配独立的generator（同一个gen的多份拷贝）。
             每个generator持有自己局部的context，只能看见自己对应的那个线程 """
            gen = thr2gen_dict.get(_thread) or fresh_gen
            process = context["workers"].get(_thread)
            threads = {_thread}
            ctx = copy.deepcopy(context)
            ctx.update({
                "free-threads": threads,
                "workers": {_thread: process}
            })
            if res := op(gen, test, ctx):
                op_var, _gen2 = res[0], res[1]
                return {
                    "op": op_var,
                    "gen2": _gen2,
                    "thread": _thread
                }
            else:
                return None

        soonest = reduce(soonest_op_dict,
                         filter_builtin(None, map_builtin(_op, free)),
                         initial=None)

        if soonest:
            # 一个空闲线程有op
            op_, gen2, thread = soonest.values()
            thr2gen_dict[thread] = gen2
            return [soonest["op"],
                    EachThread(fresh_gen, thr2gen_dict)]
        elif len(free) != len(all):
            # 一部分线程正忙，暂时挂起
            return ["pending", this]
        else:
            # 所有线程（generator）都抛不出op
            return None

    def update(self, _, test, context, event):
        """ update传播到gen对应的thread """
        fresh_gen, thr2gen_dict = self.fresh_gen, self.thr2gen_dict
        process = event["process"]
        thread = process2thread(context, process)
        gen = thr2gen_dict.get(thread) or fresh_gen
        ctx = copy.deepcopy(context)
        ctx.update({
            "free-threads": {thread} & ctx["free-threads"],
            "workers": {thread: process}
        })
        gen2 = update(gen, test, ctx, event)
        thr2gen_dict[thread] = gen2
        return EachThread(fresh_gen, thr2gen_dict)


def each_thread(gen):
    return EachThread(gen, {})


class Reserve(Generator):
    def __init__(self, ranges: list[set], all_ranges: set, gens: list[Generator]):
        """
        :param ranges: gens里每个generator持有的线程集组成的列表
        :param all_ranges: 所有ranges的并集
        :param gens:
        """
        self.ranges = ranges
        self.all_ranges = all_ranges
        self.gens = gens

    def op(self, _, test, context):
        ranges, all_ranges, gens = self.ranges, self.all_ranges, self.gens

        # 处理 count, generator对 的函数
        # 计算context、调用op函数并返回格式化结果（带权重和索引）
        def fn(i, threads):
            gen = gens[i]
            # 缩小context范围至只包含所给的threads
            ctx = on_threads_context_set_param(threads, context)
            if _res := op(gen, test, ctx):
                _op_var, _gen2 = _res[0], _res[1]
                return {
                    "op": _op_var,
                    "gen2": _gen2,
                    "weight": len(threads),
                    "i": i
                }
            else:
                return None

        # 处理默认generator
        ctx_default = on_threads_context_set_param(all_ranges, context, complement=True)
        rt_default = None
        if res := op(gens[0] if gens else None, test, ctx_default):
            op_var, gen2 = res[0], res[1]
            rt_default = {
                "op": op_var,
                "gen2": gen2,
                "weight": len(ctx_default["workers"]),
                "i": len(ranges)
            }

        soonest = reduce(soonest_op_dict,
                         list(map_builtin(fn, enumerate(ranges))) + [rt_default],
                         initial=None)
        if soonest:
            gens[soonest["i"]] = soonest["gen2"]
            return [soonest["op"],
                    Reserve(ranges, all_ranges, gens)]
        else:
            return None

    def update(self, _, test, context, event):
        """ update传播到持有这个thread的generator """
        process = event["process"]
        thread = process2thread(context, process)

        # 返回产生这个event的generator的索引
        def fn():
            for i, _range in enumerate(self.ranges):
                if thread in _range:
                    return i
        index = fn()
        return Reserve(self.ranges,
                       self.all_ranges,
                       update(self.gens[index], test, context, event))


def reserve(*args):
    """
    接受2n+1（n为非负整数）个参数
    前面2n个为n组 count（分配给这个generator的线程数）, generator对，最后1个为默认generator
    例： reserve(5, write, 10, cas, read)

    每个generator持有单独的context，仅包含分配给它的线程集的信息
     """
    arg_cnt = len(args)
    assert arg_cnt > 0 and arg_cnt % 2 == 1
    default_gen = args[-1]
    cnt_gen = [args[i:i+2] for i in range(0, arg_cnt-1, 2)]
    n, pre = 0, 0
    ranges = []
    gens = []
    for cnt, gen in cnt_gen:
        n += cnt
        t_set = set(list(range(pre, n)))
        ranges.append(t_set)
        gens.append(gen)
        pre = n
    gens.append(default_gen)
    all_ranges = set().union(*ranges)
    return Reserve(ranges, all_ranges, gens)


def soonest_op_dict(d1, d2):
    """
    接受两个字典作为参数，每个字典有如下字段：
    op:         一个操作
    weight:     权重，int，可选
    :return 能更早产生op的那个dict
    """
    if d1 is None:
        return d2
    if d2 is None:
        return d1
    op1, op2 = d1["op"], d2["op"]
    if op1 == "pending":
        return d2
    if op2 == "pending":
        return d1
    t1, t2 = op1["time"], op2["time"]

    if t1 == t2:
        w1, w2 = d1.get("weight") or 1, d2.get("weight") or 1
        w = w1 + w2
        if random.randint(0, w) < w1:
            d1["weight"] = w
        else:
            d2["weight"] = w

    elif t1 < t2:
        return d1
    else:
        return d2


class Any(Generator):
    def __init__(self, gens: list[Generator]):
        self.gens = gens

    def op(self, _, test, context):
        gens = self.gens

        def convert2dict(i, gen):
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                return {
                    "op": op_var,
                    "gen2": gen2,
                    "i": i
                }
            else:
                return None

        soonest = reduce(soonest_op_dict,
                         map_builtin(convert2dict, enumerate(gens)),
                         initial=None)
        if soonest:
            gens[soonest["i"]] = soonest["gen2"]
            return Any(gens)
        else:
            return None

    def update(self, _, test, context, event):
        return Any(list(map_builtin(lambda gen: update(gen, test, context, event), self.gens)))


def any(*args):
    match len(args):
        case 0:
            return None
        case 1:
            return args[0]
        case _:
            return Any(list(args))


def clients(client_gen, nemesis_gen=None):
    if nemesis_gen is None:
        return on_threads(lambda t: t != "nemesis", client_gen)
    else:
        return any(clients(client_gen),
                   nemesis(nemesis_gen))


def nemesis(nemesis_gen, client_gen=None):
    if client_gen is None:
        return on_threads(lambda t: t == "nemesis", nemesis_gen)
    else:
        return any(nemesis(nemesis_gen),
                   clients(client_gen))


class Mix(Generator):
    def __init__(self, i, gens: list[Generator]):
        self.i = i
        self.gens = gens

    def op(self, _, test, context):
        # 扔出op后重随索引i，
        # 下次将随机选择另一个（或恰好还是同一个）generator扔出op
        i, gens = self.i, self.gens
        if gens:
            gen = None if len(gens) <= i else gens[i]
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                gens.insert(i, gen2)
                return [op_var, Mix(random.randint(0, len(gens)), gens)]
            else:
                del gens[i]
                return op(
                    Mix(random.randint(0, len(gens)), gens),
                    test, context
                )
        else:
            return None

    def update(self, gen, test, context, event):
        return gen


def mix(gens):
    return Mix(random.randint(0, len(gens)), gens)


class Limit(Generator):
    def __init__(self, remaining, gen):
        """
        :param remaining: 该generator允许扔出op的次数
        :param gen:
        """
        self.remaining = remaining
        self.gen = gen

    def op(self, _, test, context):
        remaining, gen = self.remaining, self.gen
        if remaining > 0:
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                return [op_var, Limit(remaining - 1, gen2)]
            else:
                return None
        else:
            return None

    def update(self, _, test, context, event):
        return Limit(self.remaining, update(self.gen, test, context, event))


def limit(remaining, gen):
    return Limit(remaining, gen)


def once(gen):
    return Limit(1, gen)


def log(msg):
    return {
        "type": "log",
        "value": msg
    }


class Repeat(Generator):
    def __init__(self, remaining, gen):
        """
        :param remaining: generator可重复扔出同一种op的次数。 正数 -> 重复次数； -1 -> ”无限“重复（最多MIN_INT次）
        :param gen:
        """
        self.remaining = remaining
        self.gen = gen

    def op(self, _, test, context):
        remaining, gen = self.remaining, self.gen
        if remaining != 0:
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                return [op_var, Repeat(remaining - 1, gen)]  # gen状态不变
            else:
                return None
        else:
            return None

    def update(self, _, test, context, event):
        return Repeat(self.remaining,
                      update(self.gen, test, context, event))


def repeat(gen, times=-1):
    if times == -1:  # 当省略默认参数或第二个参数为-1时
        return Repeat(-1, gen)
    return Repeat(times, gen)


class Cycle(Generator):
    def __init__(self, remaining, original_gen, gen):
        """
        :param remaining: generator可供循环使用的次数（耗尽，无法扔出op视为一次循环），
        即有”几条命“。 正数 -> 循环次数； -1 -> ”无限“循环（最多MIN_INT次）
        :param original_gen: 初始generator
        :param gen: 随op, update函数变化的当前generator
        """
        self.remaining = remaining
        self.original_gen = original_gen
        self.gen = gen

    def op(self, _, test, context):
        remaining, original_gen, gen = self.remaining, self.original_gen, self.gen
        if remaining != 0:
            if res := op(gen, test, context):  # 还能抛出op
                op_var, gen2 = res[0], res[1]
                return [op_var, Cycle(remaining, original_gen, gen2)]
            else:  # 没有可以扔的，这一次循环使命结束了，开始下一次循环
                return op(Cycle(remaining - 1, original_gen, original_gen), test, context)
        else:
            return None

    def update(self, _, test, context, event):
        return Cycle(self.remaining, self.original_gen,
                     update(self.gen, test, context, event))


def cycle(gen, times=-1):
    if times == -1:  # 当省略默认参数或第二个参数为-1时
        return Cycle(-1, gen, gen)
    return Cycle(times, gen, gen)


class ProcessLimit(Generator):
    def __init__(self, n, processes: set, gen):
        """
        :param n: 设置的并发流程数上限
        :param processes: 流程集合，generator只给这些流程扔出op
        :param gen:
        """
        self.n = n
        self.processes = processes
        self.gen = gen

    def op(self, _, test, context):
        n, processes, gen = self.n, self.processes, self.gen
        if res := op(gen, test, context):
            op_var, gen2 = res[0], res[1]
            if op_var == 'pending':
                return [op_var, ProcessLimit(n, processes, gen2)]
            else:
                processes2 = processes | set(get_all_processes(context))
                if len(processes2) <= n:
                    return [op_var, ProcessLimit(n, processes2, gen2)]
                else:
                    return None
        else:
            return None

    def update(self, _, test, context, event):
        return ProcessLimit(self.n, self.processes,
                            update(self.gen, test, context, event))


def process_limit(n, gen):
    return ProcessLimit(n, set(), gen)


class TimeLimit(Generator):
    def __init__(self, t_limit, deadline, gen):
        """
        :param t_limit: generator只在该时间内扔出op（从第一次扔出op开始计时），单位：浮点秒
        :param deadline: 截止时间，单位：浮点秒
        :param gen:
        """
        self.t_limit = t_limit
        self.deadline = deadline
        self.gen = gen

    def op(self, _, test, context):
        t_limit, deadline, gen = self.t_limit, self.deadline, self.gen
        res = op(gen, test, context)
        op_var, gen2 = res[0], res[1]
        match op_var:
            case None:
                return None
            case "pending":
                return ["pending", TimeLimit(t_limit, deadline, gen2)]
            case _:
                # 有op，计时开始
                if deadline is None:
                    if not op_var.get('time'):
                        logging.warning("No time for op:{}".format(op_var))
                        return None
                    deadline = op_var['time'] + t_limit
                    if op_var['time'] < deadline:
                        return [op_var, TimeLimit(t_limit, deadline, gen2)]
                    else:
                        return None

    def update(self, _, test, context, event):
        return TimeLimit(self.t_limit, self.deadline,
                         update(self.gen, test, context, event))


def time_limit(t_limit, gen):
    return TimeLimit(float(t_limit), None, gen)


class Stagger(Generator):
    def __init__(self, dt, next_time, gen):
        """
        :param dt: 时间间隔，大约以dt/2为周期（每次摇摆时间为随机 0 ~ dt 秒）扔出op，单位：浮点秒
        :param next_time: 下一次扔出op的最晚时间点，单位：浮点秒
        :param gen:
        """
        self.dt = dt
        self.next_time = next_time
        self.gen = gen

    def op(self, this, test, context):
        dt, next_time, gen = self.dt, self.next_time, self.gen
        if res := op(gen, test, context):
            op_var, gen2 = res[0], res[1]
            now = context['time']
            next_time = next_time or now
            if op_var == 'pending':
                return [op_var, this]  # 原样返回
            elif next_time <= op_var['time']:
                return [op_var, Stagger(dt, (op_var['time'] + random.uniform(0, dt)), gen2)]
            else:
                op_var["time"] = next_time
                return [op_var, Stagger(dt, (next_time + random.uniform(0, dt)), gen2)]
        else:
            return None

    def update(self, _, test, context, event):
        return Stagger(self.dt, self.next_time,
                       update(self.gen, test, context, event))


def stagger(dt, gen):
    """ 以 *大约* dt为间隔扔出op，该延迟应用于所有operations，而不是单独每个线程"""
    return Stagger(float(dt * 2), None, gen)


class Delay(Generator):
    def __init__(self, dt, next_time, gen):
        self.dt = dt
        self.next_time = next_time
        self.gen = gen

    def op(self, _, test, context):
        dt, next_time, gen = self.dt, self.next_time, self.gen
        if res := op(gen, test, context):
            op_var, gen2 = res[0], res[1]
            if op_var == "pending":
                return [op_var, Delay(dt, next_time, gen2)]
            else:
                next_time = next_time or op_var["time"]
                op_var.update({
                    "time": max(op_var["time"], next_time)
                })
                return [op_var, Delay(dt, op["time"] + dt, gen2)]
        else:
            return None

    def update(self, _, test, context, event):
        return Delay(self.dt, self.next_time,
                     update(self.gen, test, context, event))


def delay(dt, gen):
    """ 以精确的每dt秒间隔扔出op，该延迟作用于单个线程而非全局 """
    return Delay(float(dt), None, gen)


def sleep(dt):
    """ 一个特殊的op，使接收到它的process睡眠dt秒 """
    return {
        "type": "sleep",
        "value": float(dt)
    }


class Synchronize(Generator):
    def __init__(self, gen):
        self.gen = gen

    def op(self, this, test, context):
        if len(context["free-threads"]) == len(get_all_threads(context)) and \
                len(set(context["free-threads"]) - set(get_all_threads(context))) == 0:
            return op(self.gen, test, context)
        else:
            return ["pending", this]

    def update(self, _, test, context, event):
        return Synchronize(update(self.gen, test, context, event))


def synchronize(gen):
    """ 包装一个generator，等待所有worker都空闲时才能抛出op """
    return Synchronize(gen)


def phases(*gens):
    """ 接受若干个generator，返回一个均Synchronize化的generator列表
    直到前一个generator无法抛出op或pending后才接着处理下一个generator（取消并行） """
    return list(map_builtin(synchronize, gens))


def then(gen_a, gen_b):
    """ gen_a处理 -> synchronize(等所有worker空闲) -> gen_b处理 """
    return [gen_a, synchronize(gen_b)]


class UntilOk(Generator):
    def __init__(self, gen, done, active_processes: set):
        self.gen = gen
        self.done = done
        self.active_processes = active_processes

    def op(self, this, test, context):
        gen, done, active_processes = self.gen, self.done, self.active_processes
        if not done:
            if res := op(gen, test, context):
                op_var, gen2 = res[0], res[1]
                if op_var == "pending":
                    this.gen = gen2
                    return [op_var, this]
                else:
                    return [op_var,
                            UntilOk(gen2, done, active_processes | {op_var["process"]})]
            else:
                return None
        else:
            return None

    def update(self, _, test, context, event):
        gen, done, active_processes = self.gen, self.done, self.active_processes
        gen2 = update(gen, test ,context, event)
        p = event["process"]
        if p in active_processes:
            match event["type"]:
                case "ok":
                    return UntilOk(gen2, True, active_processes - p)
                # crashed
                case "info":
                    return UntilOk(gen2, done, active_processes - p)
                # failed
                case "fail":
                    return UntilOk(gen2, done, active_processes - p)
                case _:
                    raise Exception("Unknown type value:{}", event["type"])
        else:
            return UntilOk(gen2, done, active_processes)


def until_ok(gen):
    """ 包装一个generator，抛出ops直到其中一个op处理完成（'type':'ok'） """
    return UntilOk(gen, False, set())


class FlipFlop(Generator):
    def __init__(self, i, gens: list[Generator]):
        self.i = i
        self.gens = gens

    def op(self, _, test, context):
        i, gens = self.i, self.gens
        if res := op(gens[i], test, context):
            op_var, gen2 = res[0], res[1]
            gens[i] = gen2
            return [op_var, FlipFlop((i+1) % len(gens), gens)]
        else:
            return None

    def update(self, this, test, context, event):
        return this


def flip_flop(a, b):
    """ 接受两个generator a和b， 二者交替抛出op（a->b->a->b...），直到其中一个无法抛出op（None）， 忽略update """
    return FlipFlop(0, [a, b])


# TODO GeneratorWrapperClass: Trace FriendlyExceptions CycleTimes
