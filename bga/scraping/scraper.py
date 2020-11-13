import asyncio
from contextlib import AsyncExitStack
import datetime
import typing as t

import click

from bga.common.debugging import (
    interactive_stop,
    post_mortem,
)
from bga.common.measures import Timer
from .logging import LogManager
from .spider import (
    get_spiders,
    ProcessState,
    SIGNALS,
)
from .storage import Storage


async def async_main(process_state: ProcessState):
    async with LogManager(process_state):
        # LogManager is separate from other managers because we want to close the managers
        # and then log something about them
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(timer := Timer())
            await stack.enter_async_context(Storage(process_state))
            spiders = get_spiders(process_state)
            SIGNALS.meta.started.send(process_state, spiders=spiders)
            awaitables = (spider.run() for spider in spiders)
            try:
                results = await asyncio.wait_for(asyncio.gather(*awaitables), timeout=process_state.timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                SIGNALS.meta.error.send(process_state, error=e)
            else:
                task_errors = [result for result in results if isinstance(result, Exception)]
                if task_errors:
                    SIGNALS.meta.error.send(process_state, error=task_errors)
        SIGNALS.meta.finished.send(process_state, spiders=spiders, timer=timer)


def scraper(interactive: bool, scheduler: bool, interval: int, spiders: t.Tuple[str, ...]):
    interactive_stop(interactive, "process starting", locals())
    ps = ProcessState(interval=datetime.timedelta(hours=interval), spiders_chosen=spiders, is_scheduler_on=scheduler)
    loop = asyncio.get_event_loop()
    loop.slow_callback_duration = ps.slow_task_duration
    loop.run_until_complete(async_main(ps))
    interactive_stop(interactive, "process finished", locals())


@click.command()
@click.option("--debug/--no-debug", default=False)
@click.option("-i", "--interactive", is_flag=True)
@click.option("-s", "--scheduler", is_flag=True)
@click.option("--interval", type=click.INT, default=1)
@click.argument("spiders", nargs=-1, default=None)
def command(debug: bool, **kwargs):
    if debug:
        post_mortem(scraper)(**kwargs)
    else:
        scraper(**kwargs)


if __name__ == "__main__":
    command()
