import functools
import pdb
import pprint
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


def interactive_stop(is_interactive: bool, title: str, locals: dict):
    if is_interactive:
        rprint(f"[yellow]Interactive mode: {title}")
        local_info = pprint.pformat({k: f"{type(v).__module__}.{type(v).__qualname__}" for k, v in locals.items()})
        rprint("[yellow]Locals: ", local_info)
        pdb.set_trace()
