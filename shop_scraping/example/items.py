from shop_scraping.model import PageModel
from shop_scraping.page import (
    Css,
    PageFragment,
    Re,
    XPath,
)


# for simple spider
from shop_scraping.task import ScrapingTask, ConcurrencyPolicy, RequestPolicy, SchedulePolicy


class ExamplePage(PageFragment):
    title = XPath('//head/title/text()')
    link_for_more = Css('div p a::attr(href)')
    charset = Re('charset=([a-z1-9-]+)')


class ExampleMoreLink(PageFragment):
    title = Css('a::text')
    url = Css('a::attr(href)')


class ExampleMoreNavigation(PageFragment):
    items = Css('.navigation a', many=True, model=ExampleMoreLink)


# for modelling spider

class StartPage(PageModel):
    title = XPath('//head/title/text()')
    catalogue_pages = Css('div p a::attr(href)', many=True)


class CataloguePage(PageModel):
    items = Css('.navigation a', many=True, model=ExampleMoreLink)


# class ExampleTask(ScrapingTask):
#     name = 'example.com'
#     start_urls = ['http://example.com']
#     start_model = StartPage
#     catalogue_model = CataloguePage
#     concurrency_policy = ConcurrencyPolicy()
#     request_policy = RequestPolicy()
#     schedule_policy = SchedulePolicy()
