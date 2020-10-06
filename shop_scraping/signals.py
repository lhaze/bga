import asyncblink
from blinker.base import Signal


class NamedNamespace(asyncblink.Namespace):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name

    def signal(self, name, doc=None):
        return super().signal(f"{self.name}:{name}", doc)

    def __getitem__(self, key: str) -> Signal:
        return super().__getitem__(f"{self.name}:{key}")


process_signals = NamedNamespace("process")
process_signals.started = process_signals.signal("started")
process_signals.spider_registered = process_signals.signal("spider_registered")
process_signals.spider_started = process_signals.signal("spider_started")
process_signals.spider_ticked = process_signals.signal("spider_ticked")
process_signals.url_registered = process_signals.signal("url_registered")
process_signals.url_processed = process_signals.signal("url_processed")
process_signals.url_fetched = process_signals.signal("url_fetched")
process_signals.url_failed = process_signals.signal("url_failed")
process_signals.url_response_valid = process_signals.signal("url_response_valid")
process_signals.url_response_invalid = process_signals.signal("url_response_invalid")
process_signals.items_extracted = process_signals.signal("items_extracted")
process_signals.spider_ended = process_signals.signal("spider_ended")
process_signals.error = process_signals.signal("error")
process_signals.finished = process_signals.signal("finished")
