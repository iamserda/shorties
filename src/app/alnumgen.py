import string
from random import randint

def alnum_generator()->str:
    alphabet = string.ascii_letters
    alphabet_min = 0
    alphabet_max = len(alphabet) - 1
    key: str = ""
    cap_index = 0
    num_index = 0
    while cap_index == num_index:
        cap_index = randint(0, 5)
        num_index = randint(0, 5)
    for i in range(6):
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

    def char_verification(key: str) -> bool:
        lowers = set(string.ascii_lowercase)
        uppers = set(string.ascii_uppercase)
        for char in key:
            if char not in alphanum:
                return False
        return True

    for i in range(10):
        my_key = alnum_generator()
        assert len(my_key) == 6
        assert my_key.isalnum()
