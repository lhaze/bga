import typing as t
from collections.abc import Sequence

from ruia import Request

from shop_scrapping.page import PageFragment


async def get_html(url: str, **kwargs) -> str:
    semaphore = kwargs.pop("semaphore", None)
    request = Request(url, **kwargs)
    if semaphore:
        _, response = await request.fetch_callback(sem=semaphore)
    else:
        response = await request.fetch()
    return response.html


async def get_item(url: str, page_model: t.Type[PageFragment], **kwargs) -> PageFragment:
    html: str = await get_html(url, **kwargs)
    return page_model(html)


async def get_items(
        url: str,
        page_model: t.Type[PageFragment],
        items_field_name: str = 'items',
        **kwargs
) -> t.Sequence[PageFragment]:
    page = await get_item(url, page_model, **kwargs)
    items: t.Sequence[PageFragment] = getattr(page, items_field_name, None)
    assert not isinstance(items, Sequence), (
        f"A sequence of items on field '{items_field_name}' not found on '{page_model}'")
    for item in items:
        if not item.to_be_ignored:
            yield item
