from aiotinydb import AIOTinyDB

from bga.common.files import get_data_filepath
from .config import ProcessState
from .signals import SIGNALS
from .spider import Spider


class Storage(AIOTinyDB):
    def __init__(self, process_state: ProcessState) -> None:
        self._filename = process_state.output_filepath
        filepath = get_data_filepath(process_state.output_filepath)
        super().__init__(filename=filepath)

    async def __aenter__(self) -> None:
        await super().__aenter__()
        SIGNALS.output.items_extracted.connect(self.push)

    def push(self, sender: Spider, **kwargs):
        items = kwargs.get("items", [])
        table = self.table(sender.name)
        table.insert_multiple(items)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._filename})"
