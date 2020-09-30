import asyncio
import typing as t

from httpx import AsyncClient, Response

from common.urls import Url

from .page import PageFragment


async def fetch(url: Url, client: AsyncClient, request_kwargs: dict = None) -> Response:
    async with client:
        response = await client.get(url, **request_kwargs or {})
    return response


async def bound_fetch(
    semaphore: asyncio.Semaphore, url: Url, client: AsyncClient, request_kwargs: dict = None
) -> Response:
    async with semaphore:
        return await fetch(url, client, request_kwargs)


async def fetch_item(
    url: Url,
    client: AsyncClient,
    page_model: t.Type[PageFragment],
    request_kwargs: dict = None,
    model_kwargs: dict = None,
) -> PageFragment:
    response: Response = await fetch(url, client, request_kwargs)
    html: str = response.text
    return page_model(html, **model_kwargs or {})


async def fetch_items(
    url: Url,
    client: AsyncClient,
    page_model: t.Type[PageFragment],
    items_field_name: str = "items",
    request_kwargs: dict = None,
    model_kwargs: dict = None,
) -> t.AsyncGenerator[PageFragment, None]:
    page = await fetch_item(url, client, page_model, request_kwargs, model_kwargs)
    items: t.Sequence[PageFragment] = getattr(page, items_field_name, None)
    for item in items:
        if not item.to_be_ignored:
            yield item
