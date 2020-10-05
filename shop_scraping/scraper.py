import asyncio
import datetime
from time import process_time
import typing as t

import click
from rich import print as rprint

from common.debugging import (
    interactive_stop,
    post_mortem,
)
from common.measures import Timer
from .process import (
    get_spiders,
    process_signals,
    ProcessState,
    Spider,
)


async def async_main(spiders: t.Sequence[Spider], process_state: ProcessState):
    awaitables = (spider.run() for spider in spiders)
    try:
        await asyncio.gather(
            *awaitables
        )  # asyncio.wait_for(asyncio.gather(*awaitables), timeout=process_state.timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError) as e:
        process_signals.error.send(process_state, error=e)


def scraper(interactive: bool):
    ps = ProcessState(start=datetime.datetime.now(), interval=datetime.timedelta(hours=24))
    spiders = get_spiders(ps)
    process_signals.started.send(ps, spiders=spiders)
    interactive_stop(interactive, "process starting", locals())
    with Timer() as timer:
        if spiders:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(async_main(spiders, ps))
    process_signals.finished.send(ps, spiders=spiders, timer=timer.serialize())
    interactive_stop(interactive, "process finished", locals())


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
