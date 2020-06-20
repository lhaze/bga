import typing as t

from common.urls import Url
from .page import PageFragment


class PageModel(PageFragment):
    catalogue_pages: t.Sequence[Url] = ()
    details_pages: t.Sequence[Url] = ()
    items: t.Sequence[PageFragment] = ()

    @property
    def extracted(self) -> t.List[dict]:
        return [i.to_dict() for i in self.items]
