import asyncio
import typing as t

import httpx
from pca.data.descriptors import reify

from common.measures import Timer
from common.urls import Url

from .config import ProcessState, SpiderConfig
from .fetching import bound_fetch
from .page import PageModel
from .signals import SIGNALS


class Spider:
    def __init__(self, config: SpiderConfig, process_state: ProcessState):
        self.config = config
        self.process_state = process_state
        self._semaphore = asyncio.Semaphore(config.concurrency_policy.task_limit)
        self._urls_processed: t.MutableSet[Url] = set()
        self._urls_failed: t.MutableSet[Url] = set()
        self._urls_invalid: t.MutableSet[Url] = set()
        self._tasks: t.MutableSet[asyncio.Task] = set()
        SIGNALS.meta.spider_registered.send(self)

    @reify
    def name(self):
        return self.config.name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} {id(self)}>"

    async def run(self):
        SIGNALS.spider.spider_started.send(self)
        self._create_tasks(urls=self.config.start_urls, model_class=self.config.start_model)
        while len(self._tasks):
            done, pending = await asyncio.wait(
                self._tasks
            )  # , timeout=self.config.concurrency_policy.task_check_interval)
            SIGNALS.spider.spider_ticked.send(self, done=done, pending=pending)
            self._tasks.difference_update(done)
        SIGNALS.spider.spider_ended.send(
            self, urls_failed=self._urls_failed, urls_invalid=self._urls_invalid, urls_total=len(self._urls_processed)
        )

    def _create_tasks(self, urls: t.Sequence[Url], model_class: t.Type[PageModel]) -> None:
        new_urls = set(urls) - self._urls_processed
        for url in new_urls:
            task = asyncio.create_task(self._process_url(url, model_class), name=url)
            self._urls_processed.add(url)
            self._tasks.add(task)
            SIGNALS.spider.url_registered.send(self, task=task)

    async def _process_url(self, url: Url, model_class: t.Type[PageModel]):
        SIGNALS.spider.url_processing_started.send(self, url=url, model_class=model_class)
        response = await self._make_request(url=url)
        if response:
            model = model_class(response.text)
            if model.is_valid_response():
                SIGNALS.output.url_response_valid.send(self, url=url, response=response)
                self._extract(model)
            else:
                self._urls_invalid.add(url)
                SIGNALS.output.url_response_invalid.send(self, url=url, response=response)

    async def _make_request(self, url) -> t.Optional[httpx.Response]:
        # TODO coordinate between requests and throttle request rate
        await asyncio.sleep(self.config.concurrency_policy.request_delay)
        response = timer = None
        SIGNALS.spider.url_fetching_started.send(self, url=url)
        for _ in range(tries := self.config.concurrency_policy.url_retries):
            with Timer() as timer:
                # TODO be resilent to 4xx & 5xx responses
                response = await bound_fetch(
                    semaphore=self._semaphore,
                    url=url,
                    client_kwargs=self.config.request_policy.client_kwargs,
                    request_kwargs=self.config.request_policy.request_kwargs,
                )
            if response.status_code < 400:
                SIGNALS.spider.url_fetched.send(self, url=url, response=response, timer=timer)
                return response
            else:
                SIGNALS.spider.url_error.send(self, url=url, response=response, timer=timer)
        self._urls_failed.add(url)
        SIGNALS.output.url_failed.send(self, url=url, response=response, tries=tries)
        return None

    def _extract(self, model: PageModel):
        if catalogue_model := self.config.catalogue_model:
            self._create_tasks(urls=model.catalogue_urls, model_class=catalogue_model)
        if details_model := self.config.details_model:
            self._create_tasks(urls=model.details_urls, model_class=details_model)
        if extracted_items := model.extracted:
            SIGNALS.output.items_extracted.send(self, items=extracted_items)


def get_active_configs(process_state: ProcessState) -> t.List[SpiderConfig]:
    from bgap import shops_meta

    return [config for config in shops_meta.CONFIGS if config.should_start(process_state)]


def get_spiders(process_state: ProcessState) -> t.Set[Spider]:
    configs = get_active_configs(process_state)
    return {Spider(config=config, process_state=process_state) for config in configs}
