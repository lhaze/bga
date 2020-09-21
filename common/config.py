from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from dataclasses import (
    dataclass,
    field,
)
import typing as t

from pca.data.descriptors import reify
from pca.utils.imports import import_dotted_path

from shop_scraping.page import PageFragment


@dataclass
class ProcessConfig:
    """
    >>> ProcessConfig()
    ProcessConfig(start=datetime.datetime(...), interval=datetime.timedelta(seconds=3600))
    >>> ProcessConfig(start=datetime(2019, 8, 14, 12, 50, 32), interval=timedelta(minutes=30))
    ProcessConfig(start=datetime.datetime(2019, 8, 14, 12, 50, 32), interval=datetime.timedelta(seconds=1800))
    """

    start: datetime = field(default_factory=datetime.now)
    interval: timedelta = timedelta(hours=1)

    @reify
    def start_date(self) -> date:
        """
        >>> ProcessConfig(start=datetime(2019, 8, 14, 12, 50, 32)).start_date
        datetime.date(2019, 8, 14)
        """
        return self.start.date()

    @reify
    def start_date_iso(self) -> str:
        """
        >>> ProcessConfig(start=datetime(2019, 8, 14, 12, 50, 32)).start_date_iso
        '2019-08-14'
        """
        return self.start_date.isoformat()


@dataclass
class SpiderConfig:
    """
    >>> p = ProcessConfig(start=datetime(2019, 8, 14, 12, 50, 32))
    >>> SpiderConfig(
    ...     process_config=p,
    ...     name='name',
    ...     domain='domain',
    ...     allowed_domains=['allowed'],
    ...     start_urls=['start_urls'],
    ...     expected_start='12:51:00',
    ...     item_details_class='common.config.ExamplePageFragment',
    ...     item_list_class='common.config.ExamplePageFragment',
    ...     is_active=True
    ... )   # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    SpiderConfig(process_config=ProcessConfig(start=datetime.datetime(2019, 8, 14, 12, 50, 32),
    interval=datetime.timedelta(seconds=3600)), name='name', domain='domain', allowed_domains=['allowed'],
    start_urls=['start_urls'], expected_start=datetime.time(12, 51),
    item_list_class=<class 'common.config.ExamplePageFragment'>,
    item_details_class=<class 'common.config.ExamplePageFragment'>, is_active=True)
    """

    process_config: ProcessConfig
    name: str
    domain: str
    allowed_domains: t.List[str]
    start_urls: t.List[str]
    expected_start: t.Union[str, time]
    item_list_class: t.Union[str, t.Type[PageFragment]]
    item_details_class: t.Union[str, t.Type[PageFragment], None] = None
    is_active: bool = True

    def __post_init__(self):
        if isinstance(self.expected_start, str):
            self.expected_start = time.fromisoformat(self.expected_start)
        if isinstance(self.item_list_class, str):
            self.item_list_class = t.cast(
                t.Type[PageFragment], import_dotted_path(self.item_list_class)
            )
        if self.item_details_class and isinstance(self.item_details_class, str):
            self.item_details_class = t.cast(
                t.Type[PageFragment], import_dotted_path(self.item_details_class)
            )

    def should_start(self):
        """
        >>> kwargs = dict(
        ...     name='name',
        ...     domain='domain',
        ...     allowed_domains=['allowed'],
        ...     start_urls=['start_urls'],
        ...     item_details_class='common.config.ExamplePageFragment',
        ...     item_list_class='common.config.ExamplePageFragment',
        ... )
        >>> p = ProcessConfig(datetime(2019, 8, 14, 12, 50, 32))
        >>> # inside the time slot
        >>> SpiderConfig(process_config=p, expected_start='12:20:00', is_active=True, **kwargs).should_start()
        True
        >>> # is_active
        >>> SpiderConfig(process_config=p, expected_start='12:20:00', is_active=False, **kwargs).should_start()
        False
        >>> # before time slot
        >>> SpiderConfig(process_config=p, expected_start='10:00:00', is_active=True, **kwargs).should_start()
        False
        >>> # after time slot
        >>> SpiderConfig(process_config=p, expected_start='15:00:00', is_active=True, **kwargs).should_start()
        False
        >>> # shorter time slot
        >>> p.interval = timedelta(minutes=1)
        >>> SpiderConfig(process_config=p, expected_start='12:20:00', is_active=True, **kwargs).should_start()
        False
        """
        expected_start: datetime = datetime.combine(
            self.process_config.start_date, self.expected_start
        )
        expected_end: datetime = expected_start + self.process_config.interval
        return (
            self.is_active
            and expected_start <= self.process_config.start <= expected_end
        )


class ExamplePageFragment(PageFragment):
    def items(self) -> t.Generator[dict, None, None]:
        yield from [{"value": i} for i in range(5)]
