import asyncio
import datetime

import click

from common.debugging import (
    interactive_stop,
    post_mortem,
)
from common.measures import Timer
from .logging import LogManager
from .spider import (
    get_spiders,
    ProcessState,
    SIGNALS,
)


async def async_main(process_state: ProcessState):
    async with LogManager(process_state):
        with Timer() as timer:
            spiders = get_spiders(process_state)
            SIGNALS.meta.started.send(process_state, spiders=spiders)
            awaitables = (spider.run() for spider in spiders)
            try:
                results = await asyncio.gather(
                    *awaitables
                )  # asyncio.wait_for(asyncio.gather(*awaitables), timeout=process_state.timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                SIGNALS.meta.error.send(process_state, error=e)
            else:
                task_errors = [result for result in results if isinstance(result, Exception)]
                if task_errors:
                    SIGNALS.meta.error.send(process_state, error=task_errors)
        SIGNALS.meta.finished.send(process_state, spiders=spiders, timer=timer)


def scraper(interactive: bool):
    interactive_stop(interactive, "process starting", locals())
    ps = ProcessState(interval=datetime.timedelta(hours=24))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main(ps))
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
