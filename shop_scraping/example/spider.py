from ruia.spider import Spider

from shop_scraping.example.items import ExamplePage, ExampleMoreNavigation
from pca.data.dao import InMemoryDao
from pca.interfaces.dao import IDao
from pca.utils.dependency_injection import Container, Inject


container = Container()
container.register_by_interface(IDao, InMemoryDao, qualifier='ShopScrapingSpider')


class SimpleSpider(Spider):

    __di_container__: Container = container
    dao: IDao = Inject(qualifier='ShopScrapingSpider')

    start_urls = ['http://example.com']

    async def parse(self, response):
        item = ExamplePage(response.html)
        print('parse', item.title)
        yield self.request(item.link_for_more, callback=self.parse_more)

    async def parse_more(self, response):
        navigation = ExampleMoreNavigation(response.html)
        for item in navigation.items:
            print('parse_more', item.title)
            self.dao.insert(**item.to_dict())
