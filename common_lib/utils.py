import functools
import time


def timer(func):
    """
    Function execution time decorator
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        print(f"Start of function : {func.__name__}...")
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"Function {func.__name__} executed in {duration:.6f} secs.")
        return result
    return wrapper


