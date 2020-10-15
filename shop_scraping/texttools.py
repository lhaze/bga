import typing as t


def find_strip(strings: t.Sequence[str]) -> str:
    """
    >>> find_strip(['\\n\\t\\t\\t ', ' 44,9 PLN\\n\\t\\t\\t\\t\\t\\t', '\\n\\t\\t\\t '])
    '44,9 PLN'
    """
    return next((s for s in (s.strip() for s in strings) if s), "")


def text_to_money(value_str: str) -> t.Optional[t.Dict[str, str]]:
    """
    >>> text_to_money('49,9 PLN')
    {'amount': '49.9', 'currency': 'PLN'}
    """
    if not value_str:
        return None
    amount, currency = value_str.split(" ", 1)
    return to_money(amount, currency)


def to_money(amount: str, currency: str) -> t.Dict[str, str]:
    """
    >>> to_money('49,9', 'PLN')
    {'amount': '49.9', 'currency': 'PLN'}
    """
    return {"amount": amount.replace(",", "."), "currency": currency}
