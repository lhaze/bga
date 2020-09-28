import asyncio
import click
import pdb
import pprint
import typing as t

from pca.utils.imports import import_dotted_path

from common.debugging import post_mortem

from .page import PageFragment
from .fetching import fetch_response, Response


def bga_url_tester(url: str, model_path: str, debug: bool, interactive: bool):
    model_class: t.Type[PageFragment] = import_dotted_path(model_path)
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    response: Response = loop.run_until_complete(
        asyncio.wait_for(
            fetch_response(
                url,
                headers={
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
                },
            ),
            timeout=10,
        )
    )
    model: PageFragment = model_class(response.text)
    serialized: str = pprint.pformat(model.to_dict())
    click.secho("Result:", fg="yellow")
    click.echo(serialized)
    if interactive:
        click.secho("Interactive mode", fg="yellow")
        local_info = pprint.pformat({k: f"{type(v).__module__}.{type(v).__qualname__}" for k, v in locals().items()})
        click.secho("Locals: ", fg="yellow", nl=False)
        click.echo(local_info)
        pdb.set_trace()


@click.command()
@click.option("--debug/--no-debug", default=False)
@click.option("-i", "--interactive", is_flag=True)
@click.argument("url")
@click.argument("model_path")
def command(**kwargs):
    if kwargs["debug"]:
        post_mortem(bga_url_tester)(**kwargs)
    else:
        bga_url_tester(**kwargs)


if __name__ == "__main__":
    command()
