import asyncio
from functools import singledispatch
import typing as t

from httpx import Response

from common.measures import Timer

from .config import ProcessState
from .spider import Spider


def serialize_kwargs(kwargs: t.Dict[str, t.Any]):
    return {name: serialize_value(value) for name, value in kwargs.items()}


@singledispatch
def serialize_value(obj: t.Any):
    """
    >>> serialize_value('str')
    'str'
    """
    return str(obj)


@serialize_value.register
def _serialize_exception(obj: Exception) -> str:
    """
    >>> serialize_value(ValueError('str'))
    "ValueError('str')"
    """
    return repr(obj)


@serialize_value.register
def _serialize_task(obj: asyncio.Task) -> str:
    return obj.get_name()


@serialize_value.register
def _serialize_process_state(obj: ProcessState) -> str:
    """
    >>> import datetime
    >>> serialize_value(ProcessState(start=datetime.datetime(2019, 8, 14, 12, 50, 32)))
    'process 2019-08-14T12:50:32'
    """
    return f"{obj.name} {obj.start.isoformat()}"


@serialize_value.register
def _serialize_spider(obj: Spider) -> str:
    return obj.config.name


@serialize_value.register(Response)
def _serialize_response(obj: Response) -> str:
    return f"[{obj.status_code}] len={len(obj.text)}"


@serialize_value.register(Timer)
def _serialize_timer(obj: Timer) -> t.Dict[str, str]:
    return obj.serialize()


@serialize_value.register(set)
@serialize_value.register(list)
def _serialize_sequence(obj: t.Sequence) -> t.Sequence[t.Any]:
    """
    >>> serialize_value({'foo'})
    ['foo']
    """
    return [serialize_value(v) for v in obj]  # type: ignore


@serialize_value.register
def _serialize_class_instance(obj: type) -> str:
    return obj.__name__
