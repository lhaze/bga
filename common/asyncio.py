import asyncio
import typing as t


class Event(asyncio.Event):
    def __init__(self, **params: t.Dict[str, t.Any]) -> None:
        self.params = params
