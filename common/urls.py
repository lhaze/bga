from urllib import parse as urllib_parse


def get_url(current_href: str, relative: str):
    """
    >>> get_url('https://www.iana.org/domains/reserved', '/domains/int')
    'https://www.iana.org/domains/int'
    >>> get_url('https://www.iana.org/domains/reserved/', '/domains/int')
    'https://www.iana.org/domains/int'
    >>> get_url('https://www.iana.org/domains/reserved#foo', '/domains/int')
    'https://www.iana.org/domains/int'
    """
    return urllib_parse.urljoin(current_href + '/', relative)


def clean_url(page_fragment, selector_list):
    return get_url(page_fragment.domain, selector_list.get())


def get_host_from_url(url):
    """
    >>> get_host_from_url('https://www.iana.org/domains/reserved')
    'www.iana.org'
    """
    return urllib_parse.urlparse(url).hostname
