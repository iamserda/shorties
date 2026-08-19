from __future__ import annotations

import logging
import secrets
import string
from random import randint

from app.constants import KEY_MAX
from app.constants import KEY_MIN

if not KEY_MIN < 5 or KEY_MAX < KEY_MIN:
    raise ValueError("Invalid minimum and maximum length for key!")


def alnum_generator() -> str:
    key = ""
    try:
        alpha_nums = string.ascii_letters + string.digits

        while True:
            key = "".join(
                secrets.choice(alpha_nums) for _ in range(randint(KEY_MIN, KEY_MAX))
            )
            if is_valid_chars(key):
                break
        return key
    except ValueError as val_err:
        val_err
        return key


def is_valid_chars(my_key: str) -> bool:
    try:
        valid_characters_set = set(string.ascii_letters).union(set(string.digits))
        for elem in my_key:
            if elem not in valid_characters_set:
                raise ValueError(
                    f"WARNING: key-gen-error: Generated key includes invalid characters! Key {my_key} is NOT valid and should be regenerated!",
                )
        return True
    except ValueError as val_err:
        logger = logging.getLogger(__name__)
        logging.basicConfig(filename="src/app/logs/main.log", level=logging.INFO)
        logger.exception(val_err)
        return False


if __name__ == "__main__":
    my_key: str = alnum_generator()
    print(my_key)
    assert my_key is not None
    assert isinstance(my_key, str)
    assert len(my_key) >= KEY_MIN and len(my_key) <= KEY_MAX
    assert is_valid_chars(my_key) is True
    # TODO: MAYBE: log new key was generated?
