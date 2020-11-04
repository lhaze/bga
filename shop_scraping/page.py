import dataclasses
import typing as t
from inspect import isawaitable

from parsel import Selector, SelectorList
from pca.data.descriptors import reify

from common.exceptions import BgaException
from common.urls import Url


Value = t.Union[str, dict, t.List[dict]]
Model = t.Union["PageFragment", t.List["PageFragment"]]
ValueOrModel = t.Union[Value, Model]
CleanFunction = t.Callable[["PageFragment", SelectorList], ValueOrModel]


class IgnoreThisItem(BgaException):
    pass


@dataclasses.dataclass
class PageMetadata:
    """Describes data about the page, passed from the spider task, other than the HTML itself."""

    url: Url
    domain: Url
    source_html: str


class Field:
    def __init__(
        self,
        *,
        clean: t.Optional[CleanFunction] = None,
        model: t.Type["PageFragment"] = None,
        many: bool = False,
        name: str = None,
        excluded: bool = False,
    ):
        self.model = model
        self.many = many
        self.excluded = excluded
        if name:
            self.name = name

        if clean:
            self._clean = clean
        elif model and many:
            self._clean = lambda page_fragment, selector_list: [
                model(selector=v, metadata=page_fragment.metadata) for v in selector_list
            ]
        elif model:
            self._clean = lambda page_fragment, selector_list: model(
                selector=selector_list[0], metadata=page_fragment.metadata
            )
        elif many:
            self._clean = lambda _, selector_list: selector_list.getall()
        else:
            self._clean = lambda _, selector_list: selector_list.get()

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(
        self,
        page_fragment: t.Optional["PageFragment"],
        owner: t.Optional[t.Type["PageFragment"]],
    ) -> t.Union["Field", ValueOrModel]:
        if page_fragment is None:
            return self
        value = self._get_value(page_fragment)
        page_fragment.__dict__[self.name] = value
        return value

    def to_value(self, page_fragment: "PageFragment") -> Value:
        if self.many and self.model:
            return [m.to_dict() for m in self._get_value(page_fragment)]
        if self.model:
            return self._get_value(page_fragment).to_dict()
        return self._get_value(page_fragment)

    async def async_to_value(self, page_fragment: "PageFragment"):
        if self.many and self.model:
            return [await m.async_to_dict() for m in await self._async_get_value(page_fragment)]
        if self.model:
            instance = await self._async_get_value(page_fragment)
            return await instance.async_to_dict()
        return await self._async_get_value(page_fragment)

    def _get_value(self, page_fragment: "PageFragment") -> ValueOrModel:
        # TODO research for async interface for Selector
        selector = self._get_selector(page_fragment)
        return self._clean(page_fragment, selector)

    async def _async_get_value(self, page_fragment: "PageFragment") -> ValueOrModel:
        selector = self._get_selector(page_fragment)
        if isawaitable(self._clean):
            value = await self._clean(page_fragment, selector)
        else:
            value = self._clean(page_fragment, selector)
        return value

    def _get_selector(self, page_fragment: "PageFragment") -> SelectorList:
        raise NotImplementedError

    def clean(self, method: CleanFunction) -> None:
        """Decorator for marking a field's clean method"""
        self._clean = method


class XPath(Field):
    def __init__(self, xpath: str, **kwargs):
        self.xpath = xpath
        super().__init__(**kwargs)

    def _get_selector(self, page_fragment: "PageFragment") -> SelectorList:
        return page_fragment.selector.xpath(self.xpath)


class Css(Field):
    def __init__(self, css_selector: str, **kwargs):
        self.css_selector = css_selector
        super().__init__(**kwargs)

    def _get_selector(self, page_fragment: "PageFragment") -> SelectorList:
        return page_fragment.selector.css(self.css_selector)


class Re(Field):
    def __init__(self, regex: str, *, clean: t.Callable = None, many: bool = False, **kwargs):
        self.regex = regex
        if not clean:
            if many:
                clean = lambda _, selected: selected
            else:
                clean = lambda _, selected: selected[0] if selected else None
        super().__init__(clean=clean, many=many, **kwargs)

    def _get_selector(self, page_fragment: "PageFragment") -> SelectorList:
        return page_fragment.selector.re(self.regex)


class Metadata(Field):
    def __init__(
        self,
        attr: str,
        *,
        clean: t.Optional[t.Callable[[Value], Value]] = None,
        name: str = None,
        excluded: bool = False,
    ):
        self.model = None
        self.many = False
        self.attr = attr
        self.name = name
        self.excluded = excluded
        self._clean = clean if clean else lambda value: value

    def _get_value(self, page_fragment: "PageFragment") -> ValueOrModel:
        value = getattr(page_fragment.metadata, self.attr, None)
        return self._clean(value)


class Noop(Field):
    def __init__(self, clean: t.Optional[t.Callable[[Value], Value]] = None, name: str = None, excluded: bool = False):
        self.model = None
        self.many = False
        self.name = name
        self.excluded = excluded
        self._clean = clean if clean else lambda value: value

    def _get_value(self, page_fragment: "PageFragment") -> ValueOrModel:
        return self._clean(page_fragment, page_fragment.selector)


class PageFragment:
    """
    >>> html = (
    ...     "<html>"
    ...     " <head>"
    ...     " <base href='http://example.com/' />"
    ...     "  <title>Example website</title>"
    ...     " </head>"
    ...     " <body>"
    ...     " <div id='images'>"
    ...     "  <a href='image1.html'>Name: My image 1 <br /><img src='image1_thumb.jpg' /></a>"
    ...     "  <a href='image2.html'>Name: My image 2 <br /><img src='image2_thumb.jpg' /></a>"
    ...     "  <a href='image3.html'>Name: My image 3 <br /><img src='image3_thumb.jpg' /></a>"
    ...     "  </div>"
    ...     " </body>"
    ...     "</html>"
    ... )

    Ad-hoc PageFragment with ad-hoc field
    >>> p = PageFragment(
    ...     text=html,
    ...     fields={'title': XPath('/html/head/title/text()', name='title')}
    ... )
    >>> p.to_dict()
    {'title': 'Example website'}

    Custom PageFragment with fields
    >>> class MyLink(PageFragment):
    ...     a = Css('a::attr(href)')
    ...     image = XPath('.//img/@src')
    >>> MyLink("<a href='image1.html'>Name: My image 1 <br /><img src='image1_thumb.jpg' /></a>").to_dict()
    {'a': 'image1.html', 'image': 'image1_thumb.jpg'}

    >>> class ThePage(PageFragment):
    ...     title = XPath('/html/head/title/text()')
    ...     mylinks = XPath('//a', many=True, model=MyLink)
    ...     mylink = XPath('//a', model=MyLink)
    ...     links = XPath('//a/img', many=True)


    >>> ThePage(html).to_dict() # doctest: +NORMALIZE_WHITESPACE
    {'title': 'Example website',
    'mylinks': [{'a': 'image1.html', 'image': 'image1_thumb.jpg'}, {'a': 'image2.html', 'image': 'image2_thumb.jpg'},
              {'a': 'image3.html', 'image': 'image3_thumb.jpg'}],
    'mylink': {'a': 'image1.html', 'image': 'image1_thumb.jpg'},
    'links': ['<img src="image1_thumb.jpg">', '<img src="image2_thumb.jpg">', '<img src="image3_thumb.jpg">']}
    """

    _fields: t.Dict[str, t.Optional[Field]] = {}
    to_be_ignored: bool = False

    def __init__(
        self,
        text: str = None,
        selector: Selector = None,
        fields: t.Mapping[str, Field] = None,
        metadata: PageMetadata = None,
    ):
        self.html = text
        self.selector = selector or Selector(text=text)
        self.metadata = metadata
        if fields:
            self._fields = {**self._fields, **fields}

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._fields = {k: v for k, v in cls.__dict__.items() if isinstance(v, Field) and not v.excluded}

    def get_field(self, name):
        return self._fields[name]

    def to_dict(self) -> dict:
        try:
            return {k: f.to_value(self) for k, f in self._fields.items()}
        except IgnoreThisItem:
            self.to_be_ignored = True

    async def async_to_dict(self) -> dict:
        try:
            return {k: await f.async_to_value(self) for k, f in self._fields.items()}
        except IgnoreThisItem:
            self.to_be_ignored = True

    def __repr__(self):
        data = repr(self.selector.get()[:40])
        return f"<{self.__class__.__name__} xpath={self.selector._expr} data={data}>"


class PageModel(PageFragment):
    catalogue_urls: t.Sequence[Url] = ()
    details_urls: t.Sequence[Url] = ()
    items: t.Sequence[PageFragment] = ()

    def is_valid_response(self) -> bool:
        return True

    @reify
    def extracted(self) -> t.List[dict]:
        return [value for i in self.items if (value := i.to_dict())]

    @classmethod
    def url_modifier(cls, url: Url) -> Url:
        return url
