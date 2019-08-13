import datetime
from dataclasses import dataclass
import typing as t

from ruamel.yaml import YAML
from scrapy.spiders import Rule

from .page_model import PageFragment


@dataclass
class ProcessConfig:

    now: t.Callable[[str], datetime.datetime] = datetime.datetime.now

    @property
    def now_time(self):
        return self.now().time()

    @property
    def now_date(self):
        return self.now().date()


@dataclass
class SpiderConfig:

    process_config: ProcessConfig
    name: str
    domain: str
    allowed_domains: t.List[str]
    start_urls: t.List[str]
    item_list: t.Type[PageFragment]
    item_details: t.Optional[t.Type[PageFragment]]
    scan_timeslot: t.Tuple[datetime.time, datetime.time]
    rules: t.List[Rule]

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'SpiderConfig':
        kwargs = YAML(typ='unsafe').load(yaml_str)
        return SpiderConfig(**kwargs)
