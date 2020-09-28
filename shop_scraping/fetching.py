import typing as t

from httpx import AsyncClient, Response  # noqa: F401

from shop_scraping.page import PageFragment


async def fetch_html(url: str, **kwargs) -> str:
    async with AsyncClient(**kwargs) as client:
        response = await client.get(url, **kwargs)
    return response.text


async def fetch_item(
    url: str,
    page_model: t.Type[PageFragment],
    request_kwargs: dict = None,
    model_kwargs: dict = None,
) -> PageFragment:
    html: str = await fetch_html(url, **request_kwargs or {})
    return page_model(html, **model_kwargs or {})


async def fetch_items(
    url: str, page_model: t.Type[PageFragment], items_field_name: str = "items", **kwargs
) -> t.AsyncGenerator:
    page = await fetch_item(url, page_model, **kwargs)
    items: t.Sequence[PageFragment] = getattr(page, items_field_name, None)
    for item in items:
        if not item.to_be_ignored:
            yield item


async def fetch(url, client):
    async with client.get(url) as response:
        delay = response.headers.get("DELAY")
        date = response.headers.get("DATE")
        print("{}:{} with delay {}".format(date, response.url, delay))
        return await response.read()


async def bound_fetch(semaphore, url, client):
    async with semaphore:
        return await fetch(url, client)
