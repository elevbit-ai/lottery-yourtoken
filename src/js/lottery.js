/*
 * Lottery yourToken — JavaScript mirror of the Python reference.
 * Runs in any modern browser (WebCrypto) and in Node >= 18.
 *
 * Construction (byte-for-byte identical to src/lottery_yourtoken/core.py):
 *   KDF     PBKDF2-HMAC-SHA256 (200 000 iterations, 16-byte salt)
 *   cipher  XOR against a SHA-256 counter keystream
 *   MAC     HMAC-SHA256 over salt || ciphertext
 *
 * Author: Joaquim Pedro de Morais Filho <j360074@hotmail.com>
 * License: MIT
 */

const subtle = globalThis.crypto.subtle;

export const FORMAT = "lottery-yourtoken/1";
export const PASSWORD_LENGTH = 30;
export const ITERATIONS = 200000;
export const DEFAULT_CHARSET = "23456789abcdefghjkmnpqrstuvwxyz";
export const AUTHOR = "Joaquim Pedro de Morais Filho <j360074@hotmail.com>";

/* ---------- small utils ---------- */

const te = new TextEncoder();
const td = new TextDecoder();

export const toHex = (u8) =>
  [...u8].map((b) => b.toString(16).padStart(2, "0")).join("");

export const fromHex = (hex) =>
  new Uint8Array((hex.match(/../g) || []).map((h) => parseInt(h, 16)));

function randomInt(maxExclusive) {
  // Rejection sampling for an unbiased secure integer.
  const buf = new Uint32Array(1);
  const limit = Math.floor(0x100000000 / maxExclusive) * maxExclusive;
  for (;;) {
    globalThis.crypto.getRandomValues(buf);
    if (buf[0] < limit) return buf[0] % maxExclusive;
  }
}

/* ---------- key material ---------- */

export function generatePassword(length = PASSWORD_LENGTH, charset = DEFAULT_CHARSET) {
  if (length < 2) throw new Error("password needs at least 2 characters");
  let out = "";
  for (let i = 0; i < length; i++) out += charset[randomInt(charset.length)];
  return out;
}

export function shufflePassword(password) {
  const chars = [...password];
  if (new Set(chars).size < 2) return password;
  for (;;) {
    for (let i = chars.length - 1; i > 0; i--) {
      const j = randomInt(i + 1);
      [chars[i], chars[j]] = [chars[j], chars[i]];
    }
    const anagram = chars.join("");
    if (anagram !== password) return anagram;
  }
}

export function isPermutation(anagram, candidate) {
  if (anagram.length !== candidate.length) return false;
  return [...anagram].sort().join("") === [...candidate].sort().join("");
}

/* ---------- cryptography ---------- */

async function deriveKeys(password, salt, iterations = ITERATIONS) {
  const base = await subtle.importKey("raw", te.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations }, base, 512);
  const material = new Uint8Array(bits);
  return { encKey: material.slice(0, 32), macKey: material.slice(32) };
}

async function keystream(encKey, length) {
  const out = new Uint8Array(Math.ceil(length / 32) * 32);
  const block = new Uint8Array(encKey.length + 8);
  block.set(encKey, 0);
  for (let counter = 0; counter * 32 < length; counter++) {
    const view = new DataView(block.buffer, encKey.length, 8);
    view.setUint32(0, 0);
    view.setUint32(4, counter);
    const digest = await subtle.digest("SHA-256", block);
    out.set(new Uint8Array(digest), counter * 32);
  }
  return out.slice(0, length);
}

const xor = (a, b) => a.map((v, i) => v ^ b[i]);

async function tag(macKey, salt, ciphertext) {
  const key = await subtle.importKey(
    "raw", macKey, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const msg = new Uint8Array(salt.length + ciphertext.length);
  msg.set(salt, 0);
  msg.set(ciphertext, salt.length);
  return new Uint8Array(await subtle.sign("HMAC", key, msg));
}

/* ---------- lottery lifecycle ---------- */

export async function createLottery(privateKey, password = null, opts = {}) {
  if (!privateKey) throw new Error("privateKey must not be empty");
  const iterations = opts.iterations ?? ITERATIONS;
  const salt = opts.salt ?? globalThis.crypto.getRandomValues(new Uint8Array(16));
  password = password ?? generatePassword();

  const { encKey, macKey } = await deriveKeys(password, salt, iterations);
  const plaintext = te.encode(privateKey);
  const ciphertext = xor(plaintext, await keystream(encKey, plaintext.length));
  const mac = await tag(macKey, salt, ciphertext);

  const bundle = {
    format: FORMAT,
    created: new Date().toISOString().slice(0, 10),
    anagram: shufflePassword(password),
    kdf: { name: "PBKDF2-HMAC-SHA256", iterations, salt: toHex(salt) },
    cipher: { name: "XOR-SHA256-CTR", ciphertext: toHex(ciphertext) },
    mac: { name: "HMAC-SHA256", tag: toHex(mac) },
    prize: { chain: "ethereum", address: opts.prizeAddress ?? null,
             note: "deposit ERC-20 tokens to grow the prize" },
    author: AUTHOR,
  };
  return { bundle, password };
}

export async function verifyGuess(bundle, candidate) {
  if (!isPermutation(bundle.anagram, candidate)) return false;
  const salt = fromHex(bundle.kdf.salt);
  const ciphertext = fromHex(bundle.cipher.ciphertext);
  const { macKey } = await deriveKeys(candidate, salt, bundle.kdf.iterations);
  const expected = fromHex(bundle.mac.tag);
  const got = await tag(macKey, salt, ciphertext);
  // Constant-time comparison.
  let diff = expected.length ^ got.length;
  for (let i = 0; i < Math.min(expected.length, got.length); i++) diff |= expected[i] ^ got[i];
  return diff === 0;
}

export async function revealKey(bundle, candidate) {
  if (!(await verifyGuess(bundle, candidate)))
    throw new Error("wrong ordering: this candidate does not win");
  const salt = fromHex(bundle.kdf.salt);
  const ciphertext = fromHex(bundle.cipher.ciphertext);
  const { encKey } = await deriveKeys(candidate, salt, bundle.kdf.iterations);
  return td.decode(xor(ciphertext, await keystream(encKey, ciphertext.length)));
}

/* ---------- difficulty ---------- */

function factorialBig(n) {
  let r = 1n;
  for (let i = 2n; i <= BigInt(n); i++) r *= i;
  return r;
}

export function difficulty(anagram, hints = 0) {
  const counts = new Map();
  for (const ch of anagram) counts.set(ch, (counts.get(ch) || 0) + 1);
  if (hints >= anagram.length) return { orderings: 1n, bits: 0 };
  for (let h = 0; h < hints; h++) {
    let best = null;
    for (const [ch, c] of counts) if (!best || c > counts.get(best)) best = ch;
    counts.set(best, counts.get(best) - 1);
    if (counts.get(best) === 0) counts.delete(best);
  }
  let n = 0;
  for (const c of counts.values()) n += c;
  let total = factorialBig(n);
  for (const c of counts.values()) total /= factorialBig(c);
  const bits = total > 1n ? Math.log2(Number(total)) : 0;
  return { orderings: total, bits };
}

/* ---------- Blockz10 {e,1} encoding (canonical) ---------- */

export function bzEncode(s) {
  if (!/^[e1]+$/.test(s)) throw new Error("alphabet {e,1} only");
  let out = "", i = 0;
  while (i < s.length) {
    const c = s[i];
    let j = i;
    while (j < s.length && s[j] === c) j++;
    let run = j - i;
    if (c === "e") {
      while (run > 9) { out += "9"; run -= 9; }
      out += run === 1 ? "e" : String(run);
    } else out += "1".repeat(run);
    i = j;
  }
  return out;
}

export function bzDecode(s) {
  if (!/^[e1-9]+$/.test(s)) throw new Error("valid symbols: e, 1-9");
  let out = "";
  for (const c of s) out += c === "1" ? "1" : c === "e" ? "e" : "e".repeat(+c);
  return out;
}

export function generateEthPuzzleKey(length = 64) {
  const a = new Uint8Array(length);
  globalThis.crypto.getRandomValues(a);
  return [...a].map((b) => (b & 1 ? "1" : "e")).join("");
}
