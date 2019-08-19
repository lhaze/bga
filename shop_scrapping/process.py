import typing as t

import blinker
from pca.utils.serialization import load
from python_path import PythonPath
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider

with PythonPath("..", relative_to=__file__):
    from common.config import ProcessConfig, SpiderConfig


process_crawler_registering = blinker.signal('process:crawler_registering')
process_crawler_start = blinker.signal('process:crawler_start')
process_crawler_end = blinker.signal('process:crawler_end')


def load_config(config_file):
    config_dict = load(config_file)
    process_config = ProcessConfig(config_dict)
    return [SpiderConfig(process_config=process_config, **d) for d in config_dict]


def build_scrappers(config: str):
    return []


def process_scrappers(spider_classes: t.Iterable[t.Type[Spider]]):
    process = CrawlerProcess()
    for spider_class in spider_classes:
        process_crawler_registering.send(process, spider_class)
        process.crawl(spider_class)

    process_crawler_start.send(process)
    process.start()  # the script will block here until all crawling jobs are finished
    process_crawler_end.send(process)
