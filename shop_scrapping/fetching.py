import typing as t

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


async def get_item(
        url: str,
        page_model: t.Type[PageFragment],
        request_kwargs: dict,
        model_kwargs: dict
) -> PageFragment:
    html: str = await get_html(url, **request_kwargs)
    return page_model(html, **model_kwargs)


async def get_items(
        url: str,
        page_model: t.Type[PageFragment],
        items_field_name: str = 'items',
        **kwargs
) -> t.AsyncGenerator:
    page = await get_item(url, page_model, **kwargs)
    items: t.Sequence[PageFragment] = getattr(page, items_field_name, None)
    for item in items:
        if not item.to_be_ignored:
            yield item
