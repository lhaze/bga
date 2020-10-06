import asyncio
from functools import singledispatch
import typing as t

from httpx import Response

from common.measures import Timer

from .config import ProcessState


def serialize_kwargs(kwargs: t.Dict[str, t.Any]):
    return {name: serialize_value(value) for name, value in kwargs.items()}


@singledispatch
def serialize_value(obj: t.Any) -> t.Union[str, t.List[str], t.Dict[str, str], t.List[t.Dict[str, str]]]:
    return str(obj)


@serialize_value.register
def _serialize_task(obj: asyncio.Task) -> str:
    return obj.get_name()


@serialize_value.register
def _serialize_process_state(obj: ProcessState) -> str:
    return f"{obj.name} {obj.start_date_iso})"


@serialize_value.register(set)
def _serialize_task_set(obj: t.Set[asyncio.Task]) -> t.List[str]:
    return [f"<Task {task.get_name()}>" for task in obj]


@serialize_value.register(list)
def _serialize_extracted_items(obj: t.List[t.Dict[str, str]]) -> t.List[t.Dict[str, str]]:
    return obj


@serialize_value.register
def _serialize_class_instance(obj: type) -> str:
    return obj.__name__


@serialize_value.register(Response)
def _serialize_response(obj: Response) -> str:
    return f"[{obj.status_code}] len={len(obj.text)}"


@serialize_value.register(Timer)
def _serialize_timer(obj: Timer) -> t.Dict[str, str]:
    return obj.serialize()
