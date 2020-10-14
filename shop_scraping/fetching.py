import asyncio
import typing as t

from httpx import (
    AsyncClient,
    Response,
)

from common.urls import Url
from .page import PageFragment


async def fetch(url: Url, client_kwargs: dict = None, request_kwargs: dict = None) -> Response:
    # TODO HTTP Client cache
    async with AsyncClient(**client_kwargs or {}) as client:
        response = await client.get(url, **request_kwargs or {})
    return response


async def bound_fetch(
    semaphore: asyncio.Semaphore, url: Url, client_kwargs: dict = None, request_kwargs: dict = None
) -> Response:
    async with semaphore:
        return await fetch(url, client_kwargs, request_kwargs)


async def fetch_item(
    url: Url,
    page_model: t.Type[PageFragment],
    client_kwargs: dict = None,
    request_kwargs: dict = None,
    model_kwargs: dict = None,
) -> PageFragment:
    response: Response = await fetch(url, client_kwargs, request_kwargs)
    html: str = response.text
    return page_model(html, **model_kwargs or {})


async def fetch_items(
    url: Url,
    page_model: t.Type[PageFragment],
    items_field_name: str = "items",
    client_kwargs: dict = None,
    request_kwargs: dict = None,
    model_kwargs: dict = None,
) -> t.AsyncGenerator[PageFragment, None]:
    page = await fetch_item(url, page_model, client_kwargs, request_kwargs, model_kwargs)
    items: t.Sequence[PageFragment] = getattr(page, items_field_name, None)
    for item in items:
        if not item.to_be_ignored:
            yield item
