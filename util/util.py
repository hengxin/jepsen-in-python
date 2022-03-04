import time
import logging

logging.basicConfig(level=logging.DEBUG)

# dynamic, float
relative_time_origin = None


def with_relative_time(func, *args, **kwargs):
    global relative_time_origin
    relative_time_origin = time.time()
    logging.info("Relative time begins now")
    return func(*args, **kwargs)


def compute_relative_time() -> float:
    """
    计算从relative_time_origin的相对时间，单位：秒
    """
    global relative_time_origin
    return time.time() - relative_time_origin
