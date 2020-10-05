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

from .page import PageFragment
from .fetching import Response


@dataclass
class ProcessState:
    """
    State of the process run.

    >>> ProcessState()
    ProcessState(start=datetime.datetime(...), interval=datetime.timedelta(seconds=900), timeout=3600)
    >>> ProcessState(start=datetime(2019, 8, 14, 12, 50, 32), interval=timedelta(minutes=30), timeout=20)
    ProcessState(start=datetime.datetime(2019, 8, 14, 12, 50, 32), interval=datetime.timedelta(seconds=1800),
    timeout=20)
    """

    start: datetime = field(default_factory=datetime.now)
    interval: timedelta = timedelta(minutes=15)
    timeout: int = 3600  # in seconds

    @reify
    def start_date(self) -> date:
        """
        >>> ProcessState(start=datetime(2019, 8, 14, 12, 50, 32)).start_date
        datetime.date(2019, 8, 14)
        """
        return self.start.date()

    @reify
    def start_date_iso(self) -> str:
        """
        >>> ProcessState(start=datetime(2019, 8, 14, 12, 50, 32)).start_date_iso
        '2019-08-14'
        """
        return self.start_date.isoformat()


@dataclass
class ConcurrencyPolicy:
    task_check_interval: int = 5  # in seconds
    task_limit: int = 3
    request_delay: float = 0.5  # in seconds
    url_retries: int = 2
    retry_delay: float = 0.5  # in seconds


@dataclass
class RequestPolicy:
    user_agent: str = "python/requests"
    timeout: int = 5
    is_valid: t.Optional[t.Callable[[Response], bool]] = None

    @property
    def headers(self) -> t.Dict[str, str]:
        return {
            "user-agent": self.user_agent,
        }

    @property
    def client_kwargs(self) -> t.Dict[str, t.Any]:
        return {
            "headers": self.headers,
        }


@dataclass
class SchedulePolicy:
    expected_start: time = time(hour=0)


@dataclass
class SpiderConfig:
    """
    >>> from dataclasses import asdict
    >>> sc = SpiderConfig(  # full setup
    ...     name='name',
    ...     domain='domain',
    ...     allowed_domains=['allowed'],
    ...     start_urls=['start_urls'],
    ...     is_active=True,
    ...     start_model='start_model',
    ...     catalogue_model='catalogue_model',
    ...     details_model='details_model',
    ... )
    >>> asdict(sc)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    {'name': 'name',
     'domain': 'domain',
     'allowed_domains': ['allowed'],
     'start_urls': ['start_urls'],
     'is_active': True,
     'start_model': 'start_model',
     'catalogue_model': 'catalogue_model',
     'details_model': 'details_model',
     'concurrency_policy': {'task_limit': 3, 'request_delay': 0.5, 'url_retries': 2, 'retry_delay': 0.5},
     'request_policy': {'user_agent': 'python/requests', 'timeout': 5, 'is_valid': None},
     'schedule_policy': {'expected_start': datetime.time(0, 0)}}
    >>> SpiderConfig(
    ...     name='name',
    ...     domain='domain'
    ... )  # minimal model setup checked
    Traceback (most recent call last):
     ...
    AssertionError: One of models - either `start_model` or `catalogue_model` - is needed
    >>> sc = SpiderConfig(
    ...     name='name',
    ...     domain='domain',
    ...     start_model='start_model'
    ... )  # minimal setup
    >>> asdict(sc)
    {'name': 'name',
     'domain': 'domain',
     'allowed_domains': {'domain'},
     'start_urls': ['domain'],
     'is_active': True,
     'start_model': 'start_model',
     'catalogue_model': None,
     'details_model': None,
     'concurrency_policy': {'task_limit': 3, 'request_delay': 0.5, 'url_retries': 2, 'retry_delay': 0.5},
     'request_policy': {'user_agent': 'python/requests', 'timeout': 5, 'is_valid': None},
     'schedule_policy': {'expected_start': datetime.time(0, 0)}}
    """

    name: str
    domain: str
    allowed_domains: t.Optional[t.Set[str]] = None
    start_urls: t.Optional[t.List[str]] = None
    is_active: bool = True

    start_model: t.Optional[t.Type[PageFragment]] = None
    catalogue_model: t.Optional[t.Type[PageFragment]] = None
    details_model: t.Optional[t.Type[PageFragment]] = None

    concurrency_policy: ConcurrencyPolicy = ConcurrencyPolicy()
    request_policy: RequestPolicy = RequestPolicy()
    schedule_policy: SchedulePolicy = SchedulePolicy()

    def __post_init__(self) -> None:
        if self.start_urls is None:
            self.start_urls = [self.domain]
        if self.allowed_domains is None:
            self.allowed_domains = {self.domain}
        assert (
            self.start_model or self.catalogue_model
        ), "One of models - either `start_model` or `catalogue_model` - is needed"
        if self.start_model is None:
            self.start_model = self.catalogue_model

    def should_start(self, process_state: ProcessState):
        """
        >>> kwargs = dict(
        ...     name='name',
        ...     domain='domain',
        ...     is_active=True,
        ...     start_model='start_model',
        ...     schedule_policy=SchedulePolicy(expected_start=time(12, 20))
        ... )
        >>> ps = ProcessState(start=datetime(2019, 8, 14, 12, 30, 32))
        >>> # inside the time slot
        >>> SpiderConfig(**kwargs).should_start(ps)
        True
        >>> # is_active is False
        >>> SpiderConfig(**dict(kwargs, is_active=False)).should_start(ps)
        False
        >>> # before time slot
        >>> SpiderConfig(**dict(kwargs, schedule_policy=SchedulePolicy(expected_start=time(10, 0)))).should_start(ps)
        False
        >>> # after time slot
        >>> SpiderConfig(**dict(kwargs, schedule_policy=SchedulePolicy(expected_start=time(15, 0)))).should_start(ps)
        False
        >>> # shorter time slot
        >>> ps.interval = timedelta(minutes=1)
        >>> SpiderConfig(**kwargs).should_start(ps)
        False
        """
        expected_start: datetime = datetime.combine(process_state.start_date, self.schedule_policy.expected_start)
        expected_end: datetime = expected_start + process_state.interval
        return self.is_active and expected_start <= process_state.start <= expected_end
