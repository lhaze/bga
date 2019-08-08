from python_path import PythonPath
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule

with PythonPath("..", "..", relative_to=__file__):
    from common import get_data_dir
    from common.urls import get_url
    from common.xpaths import (
        by_class,
        by_id,
    )


class PlanszomaniaSpider(CrawlSpider):
    name = 'planszomania'
    domain = 'www.planszomania.pl'
    allowed_domains = [domain]
    start_urls = [
        'http://www.planszomania.pl/strategiczne/',
    ]
    custom_settings = {
        'FEED_URI': get_data_dir(f'{name}.csv'),
        'FEED_FORMAT': 'jsonlines',
    }

    rules = (
        # Rule(
        #     LxmlLinkExtractor(restrict_css='.box_gray_cen'),
        #     callback="parse_item",
        #     follow=True
        # ),
    )

    def parse_item(self, response):
        for row in response.xpath(f"//table{by_id('tab_itemlist')}/tr"):
            title = row.xpath(f"./td{by_class('td_itemlist_gamebox')}/a")
            yield {
                'title': title.attrib.get('title'),
                'details_url': get_url(self.domain, title.attrib.get('href')),
                'thumbnail': get_url(self.domain, title.xpath('./img').attrib.get('src')),
                'current_price': row.xpath(f"./td{by_class('td_itemlist_cena_even')}/text()"),
                # 'base_price': '',
                # 'availability': '',
            }
