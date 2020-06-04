import typing as t

import blinker
# from pca.utils.serialization import load
# from pca.utils.imports import maybe_dotted
from python_path import PythonPath

with PythonPath("..", relative_to=__file__):
    from common.config import ProcessConfig, SpiderConfig


process_crawler_registering = blinker.signal('process:crawler_registering')
process_crawler_start = blinker.signal('process:crawler_start')
process_crawler_end = blinker.signal('process:crawler_end')


def load_config_dict(config_file: t.IO) -> dict:
    return {
        'process_config': {},
        'spider_configs': {
            'planszoman': {
                'domain': 'domain',
                'is_active': True,
                'allowed_domains': ['allowed'],
                'start_urls': ['start_urls'],
                'rules': [],
                'item_list_class': 'common.page_model.TestPageFragment',
                'item_details_class': None,
                'expected_start': '12:20:00',
            },
        },
    }


def get_configs(config_content: dict) -> t.List[SpiderConfig]:
    process_config = ProcessConfig(config_content.get('process_config', {}))
    return [
        SpiderConfig(process_config=process_config, name=name, **d)
        for name, d in config_content.get('spider_configs', {}).items()
    ]


def construct_scrappers(config: str):
    return []


def process_scrappers(spider, process):
    process_crawler_start.send(process)
    spider.start()  # the script will block here until all crawling jobs are finished
    process_crawler_end.send(process)
