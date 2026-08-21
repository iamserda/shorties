from __future__ import annotations

import logging
import secrets
import string
from pathlib import Path
from random import randint

from app.constants import KEY_MAX
from app.constants import KEY_MIN

FILE_STEM = Path(__file__).stem
logger = logging.getLogger(FILE_STEM)

if KEY_MIN < 5 or KEY_MAX < KEY_MIN:
    raise ValueError("Invalid minimum and maximum length for key!")


def alnum_generator() -> str:
    """Generates a random alphanumeric string of length between KEY_MIN and KEY_MAX."""
    try:
        alpha_nums = string.ascii_letters + string.digits

        while True:
            key = "".join(
                secrets.choice(alpha_nums) for _ in range(randint(KEY_MIN, KEY_MAX))
            )
            if is_valid_chars(key):
                return key
            else:
                warning_msg = f"WARNING: key-gen-error: Generated key includes invalid characters! Key {key} is NOT valid and should be regenerated!"
                logger.warning(warning_msg)
                raise ValueError(warning_msg)

    except ValueError as val_err:
        logger.exception(val_err)
        raise
    except Exception as e:
        logger.exception(e)
        raise


def is_valid_chars(my_key: str) -> bool:
    """Checks if the generated key contains only valid alphanumeric characters."""
    try:
        valid_characters_set = set(string.ascii_letters).union(set(string.digits))
        for elem in my_key:
            if elem not in valid_characters_set:
                raise ValueError(
                    f"WARNING: key-gen-error: Generated key includes invalid characters! Key {my_key} is NOT valid and should be regenerated!",
                )
        return True
    except ValueError as val_err:
        logger.exception(val_err)
        return False
    except Exception as e:
        logger.exception(e)
        raise


def test_alnum_generator() -> None:
    """Tests the alnum_generator function."""
    try:
        APP_DIR = Path(__file__).resolve().parent
        print(f"Testing alnum_generator() in {APP_DIR}")
        LOGS_DIR = APP_DIR / "logs"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=LOGS_DIR / "main.log",
            level=logging.DEBUG,
            datefmt="%m/%d/%Y %I:%M:%S %p",
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        for _ in range(10):
            my_key: str = alnum_generator()
            assert my_key is not None
            assert isinstance(my_key, str)
            assert len(my_key) >= KEY_MIN and len(my_key) <= KEY_MAX
            assert is_valid_chars(my_key) is True
            logger.info(f"New key generated: {my_key}")
    except AssertionError as assert_err:
        logger.exception(assert_err)
        raise
    except Exception as e:
        logger.exception(e)
        raise


if __name__ == "__main__":
    test_alnum_generator()  # Run the test function when the script is executed directly
