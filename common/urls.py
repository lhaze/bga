from urllib import parse as urllib_parse
import typing as t


Url = t.NewType("Url", str)


def get_url(current_href: str, relative: str) -> Url:
    """
    >>> get_url('https://www.iana.org/domains/reserved', '/domains/int')
    'https://www.iana.org/domains/int'
    >>> get_url('https://www.iana.org/domains/reserved/', '/domains/int')
    'https://www.iana.org/domains/int'
    >>> get_url('https://www.iana.org/domains/reserved#foo', '/domains/int')
    'https://www.iana.org/domains/int'
    """
    return Url(urllib_parse.urljoin(current_href + "/", relative))


def clean_url(page_fragment, selector_list) -> Url:
    return get_url(page_fragment.metadata.domain, selector_list.get())


def get_host_from_url(url: Url):
    """
    >>> get_host_from_url(Url('https://www.iana.org/domains/reserved'))
    'www.iana.org'
    """
    return urllib_parse.urlparse(url).hostname
