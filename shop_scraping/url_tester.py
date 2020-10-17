import asyncio
import click
import pprint
import typing as t

from pca.utils.imports import import_dotted_path
from rich import print as rprint

from common.debugging import (
    interactive_stop,
    post_mortem,
)
from common.urls import Url
from .page import PageFragment
from .fetching import fetch, Response


request_kwargs = dict(
    headers={
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
        ),
        "accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;"
            "q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
    },
)


async def async_main(url: Url):
    response: Response = await asyncio.wait_for(
        fetch(url, request_kwargs=request_kwargs),
        timeout=10,
    )
    return response


def bga_url_tester(url: Url, model_path: str, debug: bool, interactive: bool, domain: str):
    model_class: t.Type[PageFragment] = import_dotted_path(model_path)
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(async_main(url))
    model: PageFragment = model_class(response.text, domain=domain)
    serialized: str = pprint.pformat(model.to_dict())
    rprint("[yellow]Result:", serialized)
    interactive_stop(interactive, "after response", locals())


@click.command()
@click.option("--debug/--no-debug", default=False)
@click.option("-i", "--interactive", is_flag=True)
@click.option("-d", "--domain", default="")
@click.argument("url")
@click.argument("model_path")
def command(**kwargs):
    if kwargs["debug"]:
        post_mortem(bga_url_tester)(**kwargs)
    else:
        bga_url_tester(**kwargs)


if __name__ == "__main__":
    command()
