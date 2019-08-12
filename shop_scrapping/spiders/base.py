from scrapy.spiders import CrawlSpider, Rule
from ruamel.yaml import YAML


class BaseSpider(CrawlSpider):

    def __init__(self, config: str, **kwargs):
        super().__init__()
        self.__dict__.update(kwargs)
