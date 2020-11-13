from bga.shop_scraping.config import SpiderConfig
from bga.shop_scraping.page import (
    Css,
    PageFragment,
    PageModel,
    Re,
    XPath,
)
from bga.common.urls import Url


class ExamplePage(PageFragment):
    title = XPath("//head/title/text()")
    link_for_more = Css("div p a::attr(href)")
    charset = Re("charset=([a-z1-9-]+)")


class ExampleMoreLink(PageFragment):
    title = Css("a::text")
    url = Css("a::attr(href)")


class ExampleMoreNavigation(PageFragment):
    items = Css(".navigation a", many=True, model=ExampleMoreLink)


class StartPage(PageModel):
    title = XPath("//head/title/text()")
    catalogue_pages = Css("div p a::attr(href)", many=True)


class CataloguePage(PageModel):
    items = Css(".navigation a", many=True, model=ExampleMoreLink)


config = SpiderConfig(
    name="example",
    domain=Url("https://example.com"),
    # start_urls=[self.domain] as default
    # is_active=True as default
    start_model=StartPage,
    catalogue_model=CataloguePage,
    # details_model=None as no model defined
    # concurrency_policy=ConcurrencyPolicy() as default
    # schedule_policy=SchedulePolicy() as default
    # request_policy=RequestPolicy() as default
)
