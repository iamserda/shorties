import string
from app.alnumgen import alnum_generator
from app.constants import KEY_MAX


def test_alnum_generator():
    my_key: str = alnum_generator()
    assert my_key is not None
    assert isinstance(my_key, str)
    assert len(my_key) == KEY_MAX
    for elem in my_key:
        valid_characters_set = set(string.ascii_letters).union(set(string.digits))
        if elem not in valid_characters_set:
            raise ValueError("Error: Key includes invalid values! Key should be regenerated")
