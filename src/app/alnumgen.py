from __future__ import annotations

import string
from random import randint

from app.constants import KEY_MAX


def alnum_generator() -> str:
    alphabet = string.ascii_letters
    alphabet_min = 0
    alphabet_max = len(alphabet) - 1
    key: str = ""
    cap_index = 0
    num_index = 0
    while cap_index == num_index:
        cap_index = randint(0, KEY_MAX)
        num_index = randint(0, KEY_MAX)
    for i in range(KEY_MAX):
        if i == cap_index:
            key += alphabet[randint(alphabet_min, alphabet_max)].upper()
            continue

        if i == num_index:
            key += str(randint(0, 9))
            continue

        add_cap = randint(0, 1)
        add_num = randint(0, 1)

        if add_cap:
            key += alphabet[randint(alphabet_min, alphabet_max)].upper()
            continue

        if add_num:
            key += str(randint(0, 9))
            continue
        key += alphabet[randint(alphabet_min, alphabet_max)]
    return key


if __name__ == "__main__":
    my_key: str = alnum_generator()
    assert my_key is not None
    assert isinstance(my_key, str)
    assert len(my_key) == KEY_MAX
    for elem in my_key:
        valid_characters_set = set(
            string.ascii_letters,
        ).union(set(string.digits))
        if elem not in valid_characters_set:
            raise ValueError(
                "Error: Key includes invalid values! Key should be regenerated",
            )
