from shop_scraping.page import (
    Css,
    PageFragment,
    Re,
    XPath,
)


class ExampleItem(PageFragment):
    title = XPath('//head/title/text()')
    link_for_more = Css('div p a::attr(href)')
    charset = Re('charset=([a-z1-9-]+)')


class ExampleMoreLink(PageFragment):
    title = Css('a::text')
    url = Css('a::attr(href)')


class ExampleMoreNavigation(PageFragment):
    items = Css('.navigation a', many=True, model=ExampleMoreLink)
