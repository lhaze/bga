import asyncio
from asyncio import Task
from os import name
import typing as t

from httpx import AsyncClient

from common.measures import Timer
from common.urls import Url

from .config import ProcessState, SpiderConfig
from .fetching import bound_fetch
from .page import PageModel
from .signals import process_signals


class Spider:
    RUN_CHECK_INTERVAL = 5  # in seconds

    def __init__(self, config: SpiderConfig, process_state: ProcessState):
        self.config = config
        self.process_state = process_state
        self._semaphore = asyncio.Semaphore(config.concurrency_policy.task_limit)
        self._client = AsyncClient(**config.request_policy.client_kwargs)
        self._urls_processed: t.MutableSet[Url] = set()
        self._tasks: t.MutableSet[Task] = set()
        process_signals.spider_registered.send(self)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.config.name} {id(self)}>"

    async def run(self):
        process_signals.spider_started.send(self)
        self._create_tasks(self.config.start_urls, self.config.start_model)
        while len(self._tasks):
            done, pending = await asyncio.wait(self._tasks, timeout=self.RUN_CHECK_INTERVAL)
            process_signals.spider_ticked.send(self, done=done, pending=pending)
            self._tasks.difference_update(done)
        process_signals.spider_ended.send(self)

    def _create_tasks(self, urls: t.List[Url], model: PageModel) -> None:
        new_urls = set(urls) - self._urls_processed
        for url in new_urls:
            task = asyncio.create_task(self._process_url(url, model), name=url)
            self._urls_processed.add(url)
            self._tasks.add(task)
            process_signals.url_registered.send(self, level="DEBUG", task=task)

    async def _process_url(self, url: Url, model_class: t.Type[PageModel]):
        process_signals.url_processed.send(self, url=url, model_class=model_class)
        response = await self._make_request(url=url)
        model = model_class(response.text)
        process_signals.url_processed.send(self, url=url, model_class=model_class, extracted=model.extracted)
        # save results
        # create new tasks

    async def _make_request(self, url):
        await asyncio.sleep(self.config.concurrency_policy.request_delay)  # TODO coordinate between requests
        with Timer() as t:
            response = await bound_fetch(self._semaphore, url, self._client)
        process_signals.url_responded.send(self, level="INFO", url=url, response=response, timer=t.serialize())
        return response


def get_active_configs(process_state: ProcessState) -> t.List[SpiderConfig]:
    from bgap import shops_meta

    return [config for config in shops_meta.CONFIGS if config.should_start(process_state)]


def get_spiders(process_state: ProcessState) -> t.List[Spider]:
    configs = get_active_configs(process_state)
    return [Spider(config=config, process_state=process_state) for config in configs]
