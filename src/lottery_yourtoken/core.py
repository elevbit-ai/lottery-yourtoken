"""
Lottery yourToken — reference implementation.

A Blockz10 application (blockz10.blogspot.com, 2021):
a public prize wallet whose private key is encrypted with a
30-character password. The password is published — but with its
characters SHUFFLED. Anyone can grow the prize by depositing
ERC-20 tokens into the wallet; whoever reorders the characters
correctly decrypts the key and takes everything.

The construction uses only standard, auditable primitives so the
game is verifiable end to end:

  * KDF     PBKDF2-HMAC-SHA256 (200 000 iterations, 16-byte salt)
  * cipher  XOR against a SHA-256 counter keystream
  * MAC     HMAC-SHA256 over salt || ciphertext

Every primitive exists natively both in the Python standard
library and in browser WebCrypto, so the Python and JavaScript
implementations mirror each other byte for byte.

Author: Joaquim Pedro de Morais Filho <j360074@hotmail.com>
License: MIT
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import secrets
from collections import Counter
from datetime import date

FORMAT = "lottery-yourtoken/1"
PASSWORD_LENGTH = 30
ITERATIONS = 200_000
SALT_BYTES = 16

# Unambiguous charset for generated passwords (no 0/O, 1/l/I).
DEFAULT_CHARSET = "23456789abcdefghjkmnpqrstuvwxyz"

AUTHOR = "Joaquim Pedro de Morais Filho <j360074@hotmail.com>"


# --------------------------------------------------------------------------
# key material
# --------------------------------------------------------------------------

def generate_password(length: int = PASSWORD_LENGTH,
                      charset: str = DEFAULT_CHARSET) -> str:
    """Generate a random lottery password."""
    if length < 2:
        raise ValueError("password needs at least 2 characters")
    if len(set(charset)) < 2:
        raise ValueError("charset needs at least 2 distinct characters")
    return "".join(secrets.choice(charset) for _ in range(length))


def shuffle_password(password: str) -> str:
    """Return the public anagram: same characters, shuffled order.

    Fisher-Yates driven by ``secrets``. If the shuffle happens to
    reproduce the original ordering (and another ordering exists),
    it is repeated — the published anagram must not be the answer.
    """
    chars = list(password)
    if len(set(chars)) < 2:
        return password  # single-symbol password: only one ordering
    while True:
        for i in range(len(chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            chars[i], chars[j] = chars[j], chars[i]
        anagram = "".join(chars)
        if anagram != password:
            return anagram


def is_permutation(anagram: str, candidate: str) -> bool:
    """True when ``candidate`` uses exactly the anagram's characters."""
    return Counter(anagram) == Counter(candidate)


# --------------------------------------------------------------------------
# cryptography (PBKDF2 -> SHA-256 counter keystream -> HMAC)
# --------------------------------------------------------------------------

def _derive_keys(password: str, salt: bytes,
                 iterations: int = ITERATIONS) -> tuple[bytes, bytes]:
    material = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations, dklen=64)
    return material[:32], material[32:]  # enc_key, mac_key


def _keystream(enc_key: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(enc_key + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:length])


def _xor(data: bytes, stream: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, stream))


def _tag(mac_key: bytes, salt: bytes, ciphertext: bytes) -> bytes:
    return hmac.new(mac_key, salt + ciphertext, hashlib.sha256).digest()


# --------------------------------------------------------------------------
# lottery lifecycle
# --------------------------------------------------------------------------

def create_lottery(private_key: str,
                   password: str | None = None,
                   *,
                   iterations: int = ITERATIONS,
                   salt: bytes | None = None,
                   prize_address: str | None = None) -> tuple[dict, str]:
    """Encrypt ``private_key`` and build the public lottery bundle.

    Returns ``(bundle, password)``. The bundle is what the organizer
    publishes; the password is the SOLUTION and must be discarded or
    escrowed — the public only ever sees its anagram.
    """
    if not private_key:
        raise ValueError("private_key must not be empty")
    if password is None:
        password = generate_password()
    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)

    enc_key, mac_key = _derive_keys(password, salt, iterations)
    plaintext = private_key.encode("utf-8")
    ciphertext = _xor(plaintext, _keystream(enc_key, len(plaintext)))
    tag = _tag(mac_key, salt, ciphertext)

    bundle = {
        "format": FORMAT,
        "created": date.today().isoformat(),
        "anagram": shuffle_password(password),
        "kdf": {"name": "PBKDF2-HMAC-SHA256",
                "iterations": iterations,
                "salt": salt.hex()},
        "cipher": {"name": "XOR-SHA256-CTR",
                   "ciphertext": ciphertext.hex()},
        "mac": {"name": "HMAC-SHA256", "tag": tag.hex()},
        "prize": {"chain": "ethereum",
                  "address": prize_address,
                  "note": "deposit ERC-20 tokens to grow the prize"},
        "author": AUTHOR,
    }
    return bundle, password


def verify_guess(bundle: dict, candidate: str) -> bool:
    """Check a candidate ordering against the published bundle.

    Cheap rejection first (must be a permutation of the anagram),
    then the full KDF + MAC check. Constant-time tag comparison.
    """
    if not is_permutation(bundle["anagram"], candidate):
        return False
    salt = bytes.fromhex(bundle["kdf"]["salt"])
    ciphertext = bytes.fromhex(bundle["cipher"]["ciphertext"])
    _, mac_key = _derive_keys(candidate, salt, bundle["kdf"]["iterations"])
    expected = bytes.fromhex(bundle["mac"]["tag"])
    return hmac.compare_digest(_tag(mac_key, salt, ciphertext), expected)


def reveal_key(bundle: dict, candidate: str) -> str:
    """Decrypt the prize key with a winning ordering.

    Raises ``ValueError`` unless ``verify_guess`` passes.
    """
    if not verify_guess(bundle, candidate):
        raise ValueError("wrong ordering: this candidate does not win")
    salt = bytes.fromhex(bundle["kdf"]["salt"])
    ciphertext = bytes.fromhex(bundle["cipher"]["ciphertext"])
    enc_key, _ = _derive_keys(candidate, salt, bundle["kdf"]["iterations"])
    return _xor(ciphertext, _keystream(enc_key, len(ciphertext))).decode("utf-8")


# --------------------------------------------------------------------------
# difficulty
# --------------------------------------------------------------------------

def difficulty(anagram: str, hints: int = 0) -> tuple[int, float]:
    """Number of distinct orderings of the anagram, and its log2.

    With repeated characters the space is the multinomial
    ``n! / prod(count_i!)``. ``hints`` marks how many positions the
    organizer has already revealed (progressive-reveal schedule):
    each revealed position removes one character from the pool.

    >>> difficulty("aab")
    (3, 1.584962500721156)
    """
    counts = Counter(anagram)
    if hints:
        if hints >= len(anagram):
            return 1, 0.0
        # Worst-case bound: remove the most frequent characters first
        # keeps the count an upper bound independent of which hints fall.
        for ch, _ in counts.most_common(hints):
            counts[ch] -= 1
            if counts[ch] == 0:
                del counts[ch]
    n = sum(counts.values())
    total = math.factorial(n)
    for c in counts.values():
        total //= math.factorial(c)
    return total, math.log2(total) if total > 1 else 0.0


# --------------------------------------------------------------------------
# serialization helpers
# --------------------------------------------------------------------------

def dumps(bundle: dict) -> str:
    """Canonical JSON for publishing (sorted keys, 2-space indent)."""
    return json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False)


def loads(text: str) -> dict:
    bundle = json.loads(text)
    if bundle.get("format") != FORMAT:
        raise ValueError(f"unsupported bundle format: {bundle.get('format')!r}")
    return bundle
