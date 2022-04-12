import time
import logging
import yaml

# dynamic, float
global relative_time_origin


def read_config(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        result = yaml.load(f.read(), Loader=yaml.FullLoader)
    return result


def with_relative_time(func, *args, **kwargs):
    global relative_time_origin
    relative_time_origin = time.time()
    logging.info("Relative time begins now: {}".format(relative_time_origin))
    return func(*args, **kwargs)


def compute_relative_time() -> float:
    """
    计算从relative_time_origin的相对时间，单位：浮点秒
    """
    global relative_time_origin
    assert relative_time_origin  # 须在调用with_relative_time函数设置起始时间后再调用这个
    return time.time() - relative_time_origin
