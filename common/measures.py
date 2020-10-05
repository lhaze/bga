import asyncio
import datetime
import functools
import time
import typing as t


def timing(callback: t.Callable[[t.Dict[str, str]], None]):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with Timer() as t:
                result = f(*args, **kwargs)
            callback(t.serialize())
            return result

        return wrapper

    return decorator


class Timer(object):
    wall_elapsed: int = None
    process_elapsed: int = None

    def __init__(self):
        self.wall_timer = time.perf_counter
        self.process_timer = time.process_time

    def __enter__(self):
        self.started = datetime.datetime.now()
        self.wall_start = self.wall_timer()
        self.process_start = self.process_timer()
        return self

    async def __aenter__(self):
        return self.__enter__()

    def __exit__(self, *args):
        wall_end = self.wall_timer()
        process_end = self.process_timer()
        self.wall_elapsed = datetime.timedelta(seconds=wall_end - self.wall_start)
        self.process_elapsed = datetime.timedelta(seconds=process_end - self.process_start)

    async def __aexit__(self, *args):
        self.__exit__(*args)

    def as_dict(self) -> dict:
        return {"wall_elapsed": self.wall_elapsed, "process_elapsed": self.process_elapsed, "started": self.started}

    def serialize(self) -> t.Dict[str, str]:
        return {
            "wall_elapsed": str(self.wall_elapsed),
            "process_elapsed": str(self.process_elapsed),
            "started": self.started.isoformat(),
        }

    # proxy methods methods
    @staticmethod
    def sleep(*args, **kwargs):
        return time.sleep(*args, **kwargs)

    @staticmethod
    async def async_sleep(*args, **kwargs):
        return await asyncio.sleep(*args, **kwargs)
