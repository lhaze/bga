import typing as t

import asyncblink
from rich import print as rprint


class NamedNamespace(asyncblink.Namespace):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name

    def signal(self, name, doc=None):
        return super().signal(f"{self.name}:{name}", doc)


process_signals = NamedNamespace("process")
process_signals.started = process_signals.signal("started")
process_signals.spider_registered = process_signals.signal("spider_registered")
process_signals.spider_started = process_signals.signal("spider_started")
process_signals.spider_ticked = process_signals.signal("spider_ticked")
process_signals.url_registered = process_signals.signal("url_registered")
process_signals.url_processed = process_signals.signal("url_processed")
process_signals.url_responded_valid = process_signals.signal("url_responded_valid")
process_signals.url_responded_error = process_signals.signal("url_responded_error")
process_signals.url_ok = process_signals.signal("url_ok")
process_signals.url_failed = process_signals.signal("url_failed")
process_signals.items_extracted = process_signals.signal("items_extracted")
process_signals.spider_ended = process_signals.signal("spider_ended")
process_signals.error = process_signals.signal("error")
process_signals.finished = process_signals.signal("finished")


def rprint_signal_factory(name: str) -> t.Callable[..., None]:
    def rprint_handler(sender, **kwargs):
        rprint(f"{name} {sender} {kwargs}")

    return rprint_handler


for name, signal in process_signals.items():
    signal.connect(rprint_signal_factory(name), weak=False)
