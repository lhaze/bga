import asyncio
import typing as t

import blinker
from httpx import AsyncClient
from python_path import PythonPath

with PythonPath("..", relative_to=__file__):
    from common.config import ProcessState, SpiderConfig

from .fetching import bound_fetch


process_spider_registering = blinker.signal("process:spider_registering")
process_spider_start = blinker.signal("process:spider_start")
process_spider_end = blinker.signal("process:spider_end")


def load_config_dict(config_file: t.IO) -> dict:
    return {
        "process_config": {},
        "spider_configs": {
            "planszoman": {
                "domain": "domain",
                "is_active": True,
                "allowed_domains": ["allowed"],
                "start_urls": ["start_urls"],
                "rules": [],
                "item_list_class": "common.page_model.TestPageFragment",
                "item_details_class": None,
                "expected_start": "12:20:00",
            },
        },
    }


class Spider:
    def __init__(self, config: SpiderConfig, process_state: ProcessState):
        self.config = config
        self.process_state = process_state
        self.semaphore = asyncio.Semaphore(config.concurrency_policy.task_limit)

    async def run(self):
        tasks = []
        url = self.config.start_urls[0]

        # Create client session that will ensure we dont open new connection
        # per each request.
        async with AsyncClient() as client:
            # pass Semaphore and session to every GET request
            task = asyncio.create_task(bound_fetch(self.semaphore, url, client))
            tasks.append(task)

            responses = await asyncio.gather(*tasks)
            await responses


def get_active_configs(process_state: ProcessState) -> t.List[SpiderConfig]:
    from bgap import shops
    return [
        config
        for config in shops.CONFIGS
        if config.should_start(process_state)
    ]


def get_spiders(process_state: ProcessState) -> t.List[Spider]:
    configs = get_active_configs(process_state)
    return [Spider(config=config, process_state=process_state) for config in configs]
