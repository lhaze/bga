import typing as t

from scrapy.selector import Selector


Value = t.Union[str, int]
Processor = t.Callable[['PageFragment', Value], Value]


class Field:
    def __init__(
            self,
            xpath: str = None,
            processor: t.Optional[Processor] = lambda model, value: value.extract(),
    ):
        self.xpath = xpath
        self.processor = processor
        self.name: t.Optional[str] = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner: 'PageFragment'):
        if instance is None:
            return self
        value = instance.__selector__.xpath(self.xpath) if self.xpath else None
        if self.processor:
            value = self.processor(instance, value)
        instance.__dict__[self.name] = value
        return value

    def register_processor(self, method: Processor) -> None:
        """Decorator for marking a field processor"""
        self.processor = method


class PageFragment:

    __fields__: t.Dict[str, t.Optional[Field]] = None

    def __init__(self, selector: Selector, **kwargs):
        self.__selector__ = selector
        self.__dict__.update(kwargs)

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__fields__ = {k: v for k, v in cls.__dict__.items() if isinstance(v, Field)}

    def as_dict(self) -> dict:
        return {k: getattr(self, k, None) for k in self.__fields__}

    def field(self, method: t.Callable):
        self.__fields__[method.__name__] = None

    def items(self) -> t.Generator[dict, None, None]:
        raise NotImplementedError


class TestPageFragment(PageFragment):
    def items(self) -> t.Generator[dict, None, None]:
        yield from [{'value': i} for i in range(5)]
