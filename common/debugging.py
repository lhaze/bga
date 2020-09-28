import functools
import pdb
import typing as t


def post_mortem(f: t.Callable) -> t.Callable:
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            pdb.post_mortem()
            raise

    return wrapped
