import asyncio
import datetime
import typing as t

import click

from common.debugging import (
    interactive_stop,
    post_mortem,
)
from common.measures import Timer
from .logging import setup_json_files_logging, setup_print_logging
from .process import (
    get_spiders,
    process_signals,
    ProcessState,
    Spider,
)


async def async_main(spiders: t.Set[Spider], process_state: ProcessState):
    awaitables = (spider.run() for spider in spiders)
    try:
        await asyncio.gather(
            *awaitables
        )  # asyncio.wait_for(asyncio.gather(*awaitables), timeout=process_state.timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError) as e:
        process_signals.error.send(process_state, error=e)


def _setup_logging(process_state: ProcessState) -> None:
    setup_json_files_logging(process_state)
    setup_print_logging()


def scraper(interactive: bool):
    ps = ProcessState(start=datetime.datetime.now(), interval=datetime.timedelta(hours=24))
    _setup_logging(ps)
    spiders = get_spiders(ps)
    process_signals.started.send(ps, spiders=spiders)
    interactive_stop(interactive, "process starting", locals())
    with Timer() as timer:
        if spiders:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(async_main(spiders, ps))
    process_signals.finished.send(ps, spiders=spiders, timer=timer)
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
