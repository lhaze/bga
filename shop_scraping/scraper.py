import asyncio
import datetime
import typing as t

import click
from rich import print as rprint

from common.debugging import (
    interactive_stop,
    post_mortem,
    timing,
)

from .process import (
    get_spiders,
    process_error,
    process_finished,
    ProcessState,
    Spider,
)


@timing(lambda time_info: process_finished.send(time_info))
def async_main(spiders: t.Sequence[Spider], process_state: ProcessState):
    loop = asyncio.get_event_loop()
    awaitables = (spider.run() for spider in spiders)
    try:
        result = loop.run_until_complete(asyncio.wait_for(asyncio.gather(*awaitables), timeout=process_state.timeout))
    except asyncio.TimeoutError as e:
        process_error.send(e)
        raise
    return result


def scraper(interactive: bool):
    ps = ProcessState(start=datetime.datetime.now(), interval=datetime.timedelta(hours=24))
    spiders = get_spiders(ps)
    if interactive:
        interactive_stop("process starting", locals())
    if not spiders:
        pass
    result = async_main(spiders, ps)
    if interactive:
        interactive_stop("process finished", locals())
    else:
        rprint(result)


@click.command()
@click.option("--debug/--no-debug", default=False)
@click.option("-i", "--interactive", is_flag=True)
def command(debug: bool, **kwargs):
    if debug:
        post_mortem(scraper)(**kwargs)
    else:
        scraper(**kwargs)


if __name__ == "__main__":
    command()
