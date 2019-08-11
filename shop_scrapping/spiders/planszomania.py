from decimal import Decimal

from python_path import PythonPath
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule

with PythonPath("..", "..", relative_to=__file__):
    from common import get_data_dir
    from common.functools import reify
    from common.page_model import (
        Field,
        Model,
    )
    from common.texttools import text_to_money
    from common.urls import get_url
    from common.xpaths import (
        by_class,
        by_id,
    )


class PlanszomaniaItem(Model):
    domain: str = None

    title = Field(processor=lambda model, value: model.title_link.attrib.get('title'))
    current_price = Field(f"./td{by_class('td_itemlist_cena_even')}/text()")
    regular_price = Field(f"./td{by_class('td_itemlist_cena_even')}/span{by_class('stara_cena')}/text()")
    availability = Field(f"./td{by_class('td_itemlist_cena_even')}/span{by_class('span_small')}/text()")
    details_url = Field()
    thumbnail_url = Field()

    @reify
    def title_link(self):
        return self.__selector__.xpath(f"./td{by_class('td_itemlist_gamebox')}/a")

    @current_price.register_processor
    def _(self, value):
        value_found = next((f for f in (fragment.strip() for fragment in value.extract()) if f), None)
        return text_to_money(value_found)

    @regular_price.register_processor
    def _(self, value):
        value_found = value.get()
        value_found = value_found.strip() if value_found is not None else None
        if not value_found:
            return
        return Decimal(value_found.replace(',', '.'))

    @availability.register_processor
    def _(self, value):
        value_found = next((f for f in (fragment.strip() for fragment in value.extract()) if f), None)
        return value_found.strip('()')

    @details_url.register_processor
    def _(self, value):
        return get_url(self.domain, self.title_link.attrib.get('href'))

    @thumbnail_url.register_processor
    def _(self, value):
        return get_url(self.domain, self.title_link.xpath('./img').attrib.get('src'))


class PlanszomaniaList(Model):
    domain: str = None

    def items(self) -> PlanszomaniaItem:
        for selector in self.__selector__.xpath(f"//table{by_id('tab_itemlist')}/tr"):
            yield PlanszomaniaItem(selector, domain=self.domain).as_dict()


class PlanszomaniaSpider(CrawlSpider):
    name = 'planszomania'
    domain = 'www.planszomania.pl'
    allowed_domains = [domain]
    start_urls = [
        'https://www.planszomania.pl/strategiczne/',
    ]
    custom_settings = {
        'FEED_URI': get_data_dir(f'{name}.csv'),
        'FEED_FORMAT': 'jsonlines',
    }

    rules = (
        Rule(
            LxmlLinkExtractor(restrict_css='.box_gray_cen'),
            callback="parse_list",
            follow=True
        ),
    )

    def parse_list(self, response):
        yield from PlanszomaniaList(response, domain=self.domain).items()
