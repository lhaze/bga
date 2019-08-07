from urllib import parse as urllib_parse


def get_url(current_href: str, relative: str):
    return urllib_parse.urljoin(current_href, relative)
