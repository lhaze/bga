import datetime
import functools
import pdb
import pprint
import time
import typing as t

from rich import print as rprint


def post_mortem(f: t.Callable) -> t.Callable:
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            pdb.post_mortem()
            raise

    return wrapped


def interactive_stop(title: str, locals: dict):
    rprint(f"[yellow]Interactive mode: {title}")
    local_info = pprint.pformat({k: f"{type(v).__module__}.{type(v).__qualname__}" for k, v in locals.items()})
    rprint("[yellow]Locals: ", local_info)
    pdb.set_trace()


def timing(callback: t.Callable[[str], None]):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = f(*args, **kwargs)
            end = time.time()
            time_info = str(datetime.timedelta(seconds=end - start))
            callback(time_info)
            return result

        return wrapper

    return decorator
