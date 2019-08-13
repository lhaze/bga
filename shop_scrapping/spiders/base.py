from scrapy.spiders import CrawlSpider

from common import get_data_dir
from common.config import SpiderConfig


class BaseSpider(CrawlSpider):

    @property
    def name(self):
        return self.config.name

    @property
    def domain(self):
        return self.config.domain

    @property
    def allowed_domains(self):
        return [self.domain]

    @property
    def start_urls(self):
        return self.config.start_urls

    @property
    def rules(self):
        return self.config.rules

    @property
    def custom_settings(self):
        date_str = self.config.process_config.now_date.isoformat()
        return {
            'FEED_URI': get_data_dir(date_str, f'{self.name}.json_lines'),
            'FEED_FORMAT': 'jsonlines',
        }

    def __init__(self, config: SpiderConfig, **kwargs):
        super().__init__()
        self.config = config
        self.__dict__.update(kwargs)

    def parse_list(self, response):
        if not self.config.item_list:
            return
        yield from self.config.item_list(response, domain=self.domain).items()

    def parse_details(self, response):
        if not self.config.item_details:
            return
        yield from self.config.item_details(response, domain=self.domain).items()
