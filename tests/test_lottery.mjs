// Cross-language test: the JS mirror must accept the Python-made vector.
// Run: node tests/test_lottery.mjs
import { readFileSync } from "node:fs";
import {
  bzDecode, bzEncode, createLottery, difficulty, isPermutation,
  revealKey, shufflePassword, verifyGuess,
} from "../src/js/lottery.js";

let passed = 0;
const ok = (cond, name) => {
  if (!cond) { console.error(`FAIL  ${name}`); process.exit(1); }
  passed++; console.log(`  ok  ${name}`);
};

const vector = JSON.parse(readFileSync(new URL("./vector.json", import.meta.url)));
const PASSWORD = "abcdefghjkmnpqrstuvwxyz2345678";

ok(await verifyGuess(vector, PASSWORD), "JS verifies the Python-made bundle");
ok((await revealKey(vector, PASSWORD)) === "e1".repeat(32),
  "JS decrypts the Python ciphertext to the exact key");
ok(!(await verifyGuess(vector, PASSWORD.split("").reverse().join(""))),
  "JS rejects a wrong ordering of the same characters");

// Native JS round-trip.
const { bundle, password } = await createLottery("11ee11ee", null, { iterations: 1000 });
ok(await verifyGuess(bundle, password), "JS round-trip verifies");
ok((await revealKey(bundle, password)) === "11ee11ee", "JS round-trip decrypts");
ok(bundle.anagram !== password, "JS anagram is not the answer");
ok(isPermutation(bundle.anagram, password), "JS anagram is a permutation");

// Difficulty + encoding parity with Python.
ok(difficulty("aab").orderings === 3n, "difficulty('aab') = 3");
ok(difficulty("abc", 3).orderings === 1n, "all hints => 1 ordering");
ok(bzEncode("eee11") === "311" && bzDecode("311") === "eee11",
  "Blockz10 encoding: eee11 <-> 311");
ok(sortedEq(shufflePassword("abcabc"), "abcabc"), "shuffle preserves multiset");

function sortedEq(a, b) {
  return [...a].sort().join("") === [...b].sort().join("");
}

console.log(`\n${passed} tests passed.`);
