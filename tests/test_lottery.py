# Tests for Lottery yourToken — run: python tests/test_lottery.py
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lottery_yourtoken import (  # noqa: E402
    create_lottery, decode, difficulty, dumps, encode, generate_key,
    generate_password, is_permutation, loads, reveal_key, shuffle_password,
    verify_guess,
)

PASSED = 0


def ok(cond, name):
    global PASSED
    assert cond, name
    PASSED += 1
    print(f"  ok  {name}")


# Fast KDF for tests (the construction is iteration-count agnostic).
FAST = {"iterations": 1_000}

KEY = generate_key(64)
BUNDLE, PASSWORD = create_lottery(KEY, **FAST)

# --- lifecycle -------------------------------------------------------------
ok(reveal_key(BUNDLE, PASSWORD) == KEY, "correct ordering reveals the exact key")
ok(verify_guess(BUNDLE, PASSWORD), "correct ordering verifies")
ok(BUNDLE["anagram"] != PASSWORD, "published anagram is not the answer")
ok(is_permutation(BUNDLE["anagram"], PASSWORD), "anagram is a permutation of the answer")
ok(len(PASSWORD) == 30, "password has 30 characters")

# --- wrong guesses ---------------------------------------------------------
wrong = PASSWORD[1:] + PASSWORD[0]
if wrong == PASSWORD:
    wrong = PASSWORD[::-1]
ok(not verify_guess(BUNDLE, wrong), "wrong ordering fails verification")
ok(not verify_guess(BUNDLE, "x" * 30), "non-permutation is rejected")
ok(not verify_guess(BUNDLE, PASSWORD[:-1]), "shorter candidate is rejected")
try:
    reveal_key(BUNDLE, wrong)
    ok(False, "reveal_key must raise on a losing candidate")
except ValueError:
    ok(True, "reveal_key raises on a losing candidate")

# --- tamper detection ------------------------------------------------------
import copy  # noqa: E402

tampered = copy.deepcopy(BUNDLE)
ct = bytes.fromhex(tampered["cipher"]["ciphertext"])
tampered["cipher"]["ciphertext"] = bytes([ct[0] ^ 1]) .hex() + ct[1:].hex()
ok(not verify_guess(tampered, PASSWORD), "tampered ciphertext fails the MAC")

# --- determinism -----------------------------------------------------------
salt = bytes(range(16))
b1, _ = create_lottery("secret-key", password="abcabcabcabcabcabcabcabcabcabc",
                       salt=salt, **FAST)
b2, _ = create_lottery("secret-key", password="abcabcabcabcabcabcabcabcabcabc",
                       salt=salt, **FAST)
ok(b1["cipher"]["ciphertext"] == b2["cipher"]["ciphertext"]
   and b1["mac"]["tag"] == b2["mac"]["tag"],
   "same password + salt => same ciphertext and tag (auditable)")

# --- difficulty ------------------------------------------------------------
ok(difficulty("aab")[0] == 3, "difficulty('aab') = 3 orderings")
n30, bits30 = difficulty("abcdefghjkmnpqrstuvwxyz2345678")  # 30 unique chars
ok(n30 == math.factorial(30), "30 unique characters => 30! orderings")
ok(abs(bits30 - math.log2(math.factorial(30))) < 1e-9, "log2 difficulty matches")
full, _ = difficulty(BUNDLE["anagram"])
hinted, _ = difficulty(BUNDLE["anagram"], hints=5)
ok(hinted < full, "hints reduce the search space")
ok(difficulty("abc", hints=3)[0] == 1, "all positions hinted => 1 ordering")

# --- serialization ---------------------------------------------------------
ok(loads(dumps(BUNDLE))["mac"]["tag"] == BUNDLE["mac"]["tag"],
   "bundle JSON round-trips")

# --- Blockz10 {e,1} tie-in -------------------------------------------------
ok(set(KEY) <= {"e", "1"} and len(KEY) == 64, "prize key is a 64-char {e,1} string")
ok(decode(encode(KEY)) == KEY, "Blockz10 encoding round-trips the prize key")
ok(encode("eee11") == "311", "blog example: eee11 -> 311")

# --- shuffle sanity ---------------------------------------------------------
p = generate_password()
ok(sorted(shuffle_password(p)) == sorted(p), "shuffle preserves the multiset")

print(f"\n{PASSED} tests passed.")
