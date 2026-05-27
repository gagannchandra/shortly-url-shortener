import random
import string

_CHARSET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    """Return a random alphanumeric code of the given length."""
    return "".join(random.choices(_CHARSET, k=length))
