from decimal import Decimal
import typing as t


def text_to_money(value_str: str) -> t.Dict[str, str]:
    amount, currency = value_str.split(' ', 1)
    return {'amount': Decimal(amount.replace(',', '.')), 'currency': currency}
