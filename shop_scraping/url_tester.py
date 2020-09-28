import asyncio
import click
import pprint
import typing as t

from pca.utils.imports import import_dotted_path

from common.debugging import post_mortem

from .page import PageFragment
from .fetching import fetch_item


def bga_url_tester(url: str, model_path: str, debug: bool):
    model_class: t.Type[PageFragment] = import_dotted_path(model_path)
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    model: PageFragment = loop.run_until_complete(
        asyncio.wait_for(
            fetch_item(
                url,
                model_class,
                request_kwargs={
                    "headers": {
                        "user_agent": (
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
                        "cookie": "PHPSESSID=0b9f7468be6b214b13d1c2f823ee505a",
                        "referer": "https://www.planszomania.pl/",
                    }
                },
            ),
            timeout=10,
        )
    )
    serialized: str = pprint.pformat(model.to_dict())
    click.echo(serialized)
    click.echo((model.html or "")[:200])


@click.command()
@click.argument("url")
@click.argument("model_path")
@click.option("--debug/--no-debug", default=False)
def command(url: str, model_path: str, debug: bool):
    if debug:
        post_mortem(bga_url_tester)(url=url, model_path=model_path, debug=debug)
    else:
        bga_url_tester(url=url, model_path=model_path, debug=debug)


if __name__ == "__main__":
    command()
