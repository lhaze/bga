import asyncblink
from blinker.base import Signal
from pca.utils.collections import Bunch


class NamedNamespace(asyncblink.Namespace):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name

    def signal(self, name, doc=None):
        return super().signal(f"{self.name}:{name}", doc)

    def __getitem__(self, key: str) -> Signal:
        return super().__getitem__(f"{self.name}:{key}")


meta_signals = NamedNamespace("meta")
meta_signals.spider_registered = meta_signals.signal("spider_registered")
meta_signals.started = meta_signals.signal("started")
meta_signals.error = meta_signals.signal("error")
meta_signals.finished = meta_signals.signal("finished")

spider_signals = NamedNamespace("spider")
spider_signals.spider_started = spider_signals.signal("spider_started")
spider_signals.spider_ticked = spider_signals.signal("spider_ticked")
spider_signals.url_registered = spider_signals.signal("url_registered")
spider_signals.url_processing_started = spider_signals.signal("url_processing_started")
spider_signals.url_fetching_started = spider_signals.signal("url_fetching_started")
spider_signals.url_fetched = spider_signals.signal("url_fetched")
spider_signals.url_error = spider_signals.signal("url_error")
spider_signals.spider_ended = spider_signals.signal("spider_ended")

output_signals = NamedNamespace("output")
output_signals.url_failed = output_signals.signal("url_failed")
output_signals.url_response_valid = output_signals.signal("url_response_valid")
output_signals.url_response_invalid = output_signals.signal("url_response_invalid")
output_signals.items_extracted = output_signals.signal("items_extracted")

SIGNALS = Bunch(spider=spider_signals, meta=meta_signals, output=output_signals)
