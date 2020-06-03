from pca.data.descriptors import reify
from python_path import PythonPath

with PythonPath("..", "..", relative_to=__file__):
    from common.page import (
        Css,
        PageFragment,
    )
    from common.texttools import (
        find_strip,
        text_to_money,
        to_money,
    )
    from common.urls import clean_url


class PlanszomaniaItem(PageFragment):
    domain: str

    title = Css('td.td_itemlist_gamebox a::attr(title)')
    current_price = Css('td.td_itemlist_cena_even::text')
    regular_price = Css('td.td_itemlist_cena_even span.stara_cena::text')
    availability = Css('td.td_itemlist_cena_even span.span_small::text')
    details_url = Css('td.td_itemlist_gamebox a::attr(href)', clean=clean_url)
    thumbnail_url = Css('td.td_itemlist_gamebox a img::attr(src)', clean=clean_url)

    @reify
    def title_link(self):
        return self._selector.css('td.td_itemlist_gamebox a')

    @current_price.clean
    def _(self, selector_list):
        return text_to_money(find_strip(selector_list.getall()))

    @reify
    def currency(self):
        return self.current_price['currency']

    @regular_price.clean
    def _(self, selector_list):
        value_found = selector_list.get()
        value_found = value_found.strip() if value_found is not None else None
        if not value_found:
            return
        return to_money(value_found, self.currency)

    @availability.clean
    def _(self, selector_list):
        value_found = find_strip(selector_list.getall())
        return value_found.strip('()')


class PlanszomaniaList(PageFragment):
    domain: str

    items = Css('#tab_itemlist tr', many=True, model=PlanszomaniaItem)
