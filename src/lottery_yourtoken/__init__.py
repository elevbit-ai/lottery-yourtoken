"""Lottery yourToken — a Blockz10 application.

Public prize wallet, encrypted private key, 30 shuffled characters.
Reorder the characters, decrypt the key, take the prize.

Author: Joaquim Pedro de Morais Filho <j360074@hotmail.com>
"""

from .blockz import decode, encode, generate_key, key_entropy_bits
from .core import (
    AUTHOR,
    DEFAULT_CHARSET,
    FORMAT,
    ITERATIONS,
    PASSWORD_LENGTH,
    create_lottery,
    difficulty,
    dumps,
    generate_password,
    is_permutation,
    loads,
    reveal_key,
    shuffle_password,
    verify_guess,
)

__version__ = "1.0.0"
__all__ = [
    "AUTHOR", "DEFAULT_CHARSET", "FORMAT", "ITERATIONS", "PASSWORD_LENGTH",
    "create_lottery", "difficulty", "dumps", "generate_password",
    "is_permutation", "loads", "reveal_key", "shuffle_password",
    "verify_guess", "encode", "decode", "generate_key", "key_entropy_bits",
    "__version__",
]
