"""
Blockz10 encoding over the {e, 1} alphabet.

Original definition (blockz10.blogspot.com, 2021):

    "e" (1-9) and "1" (1)  —  "eee11" equals "311"

A run of ``e`` characters is replaced by the digit counting the run
(``eee`` -> ``3``) while ``1`` characters remain literal. Because both
``e`` and ``1`` are valid hexadecimal digits, a 64-character {e,1}
string is simultaneously a syntactically valid Ethereum private key
and a compressible Blockz10 message.

Canonical lossless form
-----------------------
The original compact notation is ambiguous for single-``e`` runs
(``1`` could mean "one e" or a literal ``1``). This reference
implementation defines the *canonical* form, which is bijective:

  * a run of n >= 2 ``e`` characters  ->  the digit n (2..9);
    runs longer than 9 are split greedily (``e``*13 -> ``94``);
  * a single ``e``                    ->  kept as ``e``;
  * ``1`` characters                  ->  kept literal.

Decoding inverts the rules exactly; encode/decode round-trips for
every {e,1} string.
"""

from __future__ import annotations

import secrets

ALPHABET = frozenset("e1")


def _check(s: str) -> None:
    if not s:
        raise ValueError("empty string")
    bad = set(s) - ALPHABET
    if bad:
        raise ValueError(f"invalid characters for Blockz10 alphabet {{e,1}}: {sorted(bad)}")


def encode(s: str) -> str:
    """Encode an {e,1} string into canonical Blockz10 form.

    >>> encode("eee11")
    '311'
    >>> encode("111e1ee1e1eeeee11111ee1111e11e11111e11e1e111e11ee11e1111ee1e1eee")
    '111e121e151111121111e11e11111e11e1e111e11211e111121e13'
    """
    _check(s)
    out: list[str] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        j = i
        while j < n and s[j] == c:
            j += 1
        run = j - i
        if c == "e":
            while run > 9:
                out.append("9")
                run -= 9
            out.append("e" if run == 1 else str(run))
        else:
            out.append("1" * run)
        i = j
    return "".join(out)


def decode(s: str) -> str:
    """Decode a canonical Blockz10 string back to its {e,1} source.

    >>> decode("311")
    'eee11'
    """
    if not s:
        raise ValueError("empty string")
    out: list[str] = []
    for c in s:
        if c == "1":
            out.append("1")
        elif c == "e":
            out.append("e")
        elif c in "23456789":
            out.append("e" * int(c))
        else:
            raise ValueError(f"invalid Blockz10 symbol: {c!r}")
    return "".join(out)


def generate_key(length: int = 64) -> str:
    """Generate a random {e,1} string of the given length.

    With the default length of 64, the result is a syntactically valid
    Ethereum private key (both ``e`` and ``1`` are hex digits).

    .. warning::
       An {e,1}-restricted 64-character key carries only 64 bits of
       entropy (2 symbols ** 64 positions) instead of the 256 bits of
       an unrestricted hexadecimal key. This is BY DESIGN for puzzle
       and lottery constructions, where the key must eventually be
       discoverable. NEVER use it to store real funds.
    """
    if length < 1:
        raise ValueError("length must be >= 1")
    return "".join(secrets.choice("e1") for _ in range(length))


def key_entropy_bits(length: int = 64, alphabet_size: int = 2) -> float:
    """Entropy in bits of a random key of ``length`` symbols."""
    import math

    return length * math.log2(alphabet_size)
