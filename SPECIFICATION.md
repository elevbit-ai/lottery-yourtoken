# Lottery yourToken — Especificação formal / Formal specification

**Versão / Version:** 1.0.0 · **Formato / Format:** `lottery-yourtoken/1`
**Autor / Author:** Joaquim Pedro de Morais Filho · j360074@hotmail.com
**Origem / Origin:** aplicação nº 2 do sistema Blockz10 — [blockz10.blogspot.com](https://blockz10.blogspot.com) (2021)

---

## 1 · Conceito / Concept

**PT** — Uma carteira-prêmio pública guarda tokens ERC-20. Sua chave privada
é encriptada com uma senha de **30 caracteres** e o pacote encriptado é
publicado junto com a senha — porém com os caracteres **embaralhados**
(um anagrama). Qualquer pessoa pode aumentar o prêmio depositando tokens na
carteira; quem descobrir a **ordem correta** dos 30 caracteres decripta a
chave e leva tudo. É uma caça ao tesouro criptográfica, verificável de ponta
a ponta e **colaborativamente inflável**.

**EN** — A public prize wallet holds ERC-20 tokens. Its private key is
encrypted with a **30-character** password, and the encrypted bundle is
published together with the password — but with its characters **shuffled**
(an anagram). Anyone can grow the prize by depositing tokens into the
wallet; whoever discovers the **correct ordering** of the 30 characters
decrypts the key and takes everything. A cryptographic treasure hunt,
verifiable end to end and **collaboratively inflatable**.

## 2 · Papéis / Roles

| Papel / Role | PT | EN |
|---|---|---|
| **Organizador / Organizer** | cria a carteira, encripta a chave, publica o pacote | creates the wallet, encrypts the key, publishes the bundle |
| **Patrocinador / Sponsor** | qualquer um que deposite tokens no endereço-prêmio | anyone who deposits tokens into the prize address |
| **Jogador / Player** | busca a ordem correta do anagrama | searches for the anagram's correct ordering |
| **Vencedor / Winner** | decripta a chave e transfere o prêmio | decrypts the key and sweeps the prize |

## 3 · Protocolo / Protocol

### 3.1 Criação / Creation

1. Gerar a chave privada da carteira-prêmio `K`.
   Na tradição Blockz10, `K` é uma string {e,1} de 64 caracteres — uma
   chave Ethereum sintaticamente válida e ao mesmo tempo comprimível pela
   codificação canônica (`eee11 → 311`). / In the Blockz10 tradition, `K`
   is a 64-character {e,1} string — a syntactically valid Ethereum key
   that is also compressible by the canonical encoding.
2. Gerar a senha `P` de 30 caracteres (charset padrão sem símbolos
   ambíguos: `23456789abcdefghjkmnpqrstuvwxyz`). / Generate the
   30-character password `P` (default unambiguous charset).
3. Gerar `salt` de 16 bytes aleatórios. / Generate a random 16-byte salt.
4. Derivar chaves e encriptar (§4). / Derive keys and encrypt (§4).
5. Embaralhar `P` com Fisher–Yates seguro → anagrama `A` (garantido
   `A ≠ P` quando existe outra ordem). / Shuffle `P` with secure
   Fisher–Yates → anagram `A` (guaranteed `A ≠ P` when another ordering
   exists).
6. Publicar o pacote JSON (§5) e o endereço da carteira. **Descartar `P`**
   (ou custodiá-la de forma auditável para o cronograma de dicas, §7). /
   Publish the JSON bundle (§5) and the wallet address. **Discard `P`**
   (or escrow it auditably for the hint schedule, §7).

### 3.2 Jogo / Play

- Depositar tokens no endereço-prêmio aumenta o prêmio — o saldo é
  público on-chain. / Depositing tokens grows the prize — the balance is
  public on-chain.
- Um palpite é uma reordenação candidata `C` de `A`. A verificação é
  local, offline e sem interação com o organizador: `C` vence se e somente
  se o MAC confere (§4.3). / A guess is a candidate reordering `C` of `A`.
  Verification is local, offline, and requires no interaction with the
  organizer: `C` wins iff the MAC verifies (§4.3).

### 3.3 Vitória / Winning

O vencedor decripta `K`, importa a chave numa carteira e transfere **todos
os ativos imediatamente** (ver §8 sobre corrida e front-running). /
The winner decrypts `K`, imports the key into a wallet and sweeps **all
assets immediately** (see §8 on races and front-running).

## 4 · Criptografia / Cryptography

Somente primitivos padrão, presentes tanto na stdlib do Python quanto no
WebCrypto dos navegadores — as duas implementações espelham-se byte a
byte. / Standard primitives only, native to both the Python stdlib and
browser WebCrypto — the two implementations mirror each other byte for
byte.

### 4.1 Derivação de chaves / Key derivation

```
material = PBKDF2-HMAC-SHA256(password = UTF8(C), salt, iterations = 200 000, dkLen = 64)
enc_key  = material[0..31]
mac_key  = material[32..63]
```

### 4.2 Cifra / Cipher (`XOR-SHA256-CTR`)

```
keystream = SHA256(enc_key ‖ BE64(0)) ‖ SHA256(enc_key ‖ BE64(1)) ‖ …
ciphertext = UTF8(K) ⊕ keystream[0 .. len-1]
```

### 4.3 Autenticação / Authentication

```
tag = HMAC-SHA256(mac_key, salt ‖ ciphertext)
```

Um candidato `C` **vence** sse: `C` é permutação de `A` **e**
`HMAC-SHA256(mac_key(C), salt ‖ ciphertext) == tag` (comparação em tempo
constante). / A candidate `C` **wins** iff `C` is a permutation of `A`
**and** the tag verifies (constant-time comparison).

O custo de 200 000 iterações de PBKDF2 por palpite é deliberado: torna a
busca exaustiva cara sem impedir a verificação honesta de um palpite
único. / The 200 000-iteration PBKDF2 cost per guess is deliberate: it
makes exhaustive search expensive without hindering honest single-guess
verification.

## 5 · Pacote publicado / Published bundle

```json
{
  "format": "lottery-yourtoken/1",
  "created": "2026-09-24",
  "anagram": "k7mwp2qr9tvx3jn8hsau5ybcedg64f",
  "kdf":    { "name": "PBKDF2-HMAC-SHA256", "iterations": 200000, "salt": "<hex 16B>" },
  "cipher": { "name": "XOR-SHA256-CTR",     "ciphertext": "<hex>" },
  "mac":    { "name": "HMAC-SHA256",        "tag": "<hex 32B>" },
  "prize":  { "chain": "ethereum", "address": "0x…", "note": "deposit ERC-20 tokens to grow the prize" },
  "author": "Joaquim Pedro de Morais Filho <j360074@hotmail.com>"
}
```

Campos obrigatórios: todos exceto `prize.address` (o organizador o
preenche ao anunciar a carteira). / All fields required except
`prize.address` (filled when the wallet is announced).

## 6 · Dificuldade / Difficulty

O espaço de busca é o número de **permutações distintas** do anagrama —
multinomial, não fatorial simples quando há repetições: / The search
space is the number of **distinct permutations** of the anagram — a
multinomial, not a plain factorial when characters repeat:

```
orderings(A) = n! / ∏ᵢ (countᵢ!)        n = 30
```

| Composição do anagrama / Anagram composition | Ordens / Orderings | bits |
|---|---|---|
| 30 caracteres únicos / 30 unique chars | 30! ≈ 2,65 × 10³² | ≈ 107,7 |
| 15 símbolos × 2 repetições / 15 symbols × 2 | 30!/2¹⁵ ≈ 8,1 × 10²⁷ | ≈ 92,7 |
| 6 símbolos × 5 repetições / 6 symbols × 5 | 30!/(5!)⁶ ≈ 8,9 × 10¹⁹ | ≈ 66,3 |
| 2 símbolos × 15 repetições / 2 symbols × 15 | C(30,15) ≈ 1,55 × 10⁸ | ≈ 27,2 |

**A composição do anagrama é o dial de dificuldade** do organizador —
de loteria de décadas a puzzle de fim de semana. / **The anagram's
composition is the organizer's difficulty dial** — from a decades-long
lottery to a weekend puzzle.

## 7 · Cronograma de dicas / Hint schedule (opcional / optional)

Para garantir que a loteria termine, o organizador pode se comprometer
publicamente com um cronograma de revelação: a cada período, revela o
caractere de uma posição (`posição i = c`). Cada dica remove um símbolo do
multiconjunto livre e o espaço cai de forma verificável — `difficulty(A,
hints=h)` na implementação de referência dá o limite superior. / To
guarantee the lottery ends, the organizer may publicly commit to a reveal
schedule: each period, reveal one position's character. Each hint removes
a symbol from the free multiset and the space shrinks verifiably —
`difficulty(A, hints=h)` in the reference implementation gives the upper
bound.

## 8 · Considerações de segurança / Security considerations

1. **Corrida de vencedores / Winner races** — a verificação é offline:
   ninguém sabe que você venceu até a transação aparecer. Mas se dois
   jogadores resolvem em janelas próximas, vence quem confirma primeiro.
   Transfira **tudo em uma única transação** e considere um relay privado
   (ex.: Flashbots Protect) para evitar observação de mempool. /
   Verification is offline: nobody knows you won until your transaction
   appears. If two players solve close together, the first confirmation
   wins. Sweep **everything in a single transaction** and consider a
   private relay (e.g. Flashbots Protect) to avoid mempool observation.
2. **Entropia da chave {e,1} / {e,1} key entropy** — uma chave {e,1} de 64
   caracteres tem 64 bits de entropia, por design descobrível em tese.
   O prêmio é protegido pela **senha**, não pela forma da chave; ainda
   assim, calibre o valor do prêmio à dificuldade escolhida e nunca reuse
   a carteira. / A 64-char {e,1} key carries 64 bits of entropy, by
   design theoretically discoverable. The prize is protected by the
   **password**, not the key's shape; still, match prize value to chosen
   difficulty and never reuse the wallet.
3. **Confiança no organizador / Organizer trust** — o pacote prova que
   *alguma* ordenação do anagrama decripta *algum* texto; não prova que o
   texto é a chave da carteira anunciada. Mitigação: o organizador pode
   assinar uma mensagem com a chave da carteira-prêmio no anúncio,
   provando posse; a comunidade confere o endereço. / The bundle proves
   that *some* ordering decrypts *something*; it does not prove the
   plaintext is the announced wallet's key. Mitigation: the organizer
   signs an announcement message with the prize wallet's key, proving
   possession; the community checks the address.
4. **Sem canal lateral do organizador / No organizer side channel** —
   após a publicação, o organizador não é mais necessário: verificação e
   decriptação são locais. / After publication the organizer is no longer
   needed: verification and decryption are local.
5. **Jurisdição / Jurisdiction** — regras sobre loterias e promoções
   variam por país. Esta é uma especificação técnica e implementação de
   referência para fins educacionais e de pesquisa; a legalidade de uma
   instância real é responsabilidade de quem a organiza. / Lottery and
   promotion rules vary by country. This is a technical specification
   and reference implementation for educational and research purposes;
   the legality of a live instance is the organizer's responsibility.

## 9 · Implementações de referência / Reference implementations

| | Python | JavaScript |
|---|---|---|
| Arquivo / File | `src/lottery_yourtoken/core.py` | `src/js/lottery.js` |
| Dependências / Dependencies | stdlib apenas / stdlib only | WebCrypto (browser / Node ≥ 18) |
| Testes / Tests | `tests/test_lottery.py` (21) | `tests/test_lottery.mjs` (11, inclui vetor cruzado / incl. cross vector) |

O vetor `tests/vector.json` foi gerado pelo Python e é decriptado pelo
JavaScript — prova de compatibilidade byte a byte. / The vector
`tests/vector.json` was produced by Python and is decrypted by
JavaScript — proof of byte-for-byte compatibility.

---

© 2020–2026 Joaquim Pedro de Morais Filho · Licença MIT / MIT License
Conceito Blockz10 registrado on-chain (NFT · OpenSea) / Blockz10 concept registered on-chain (NFT · OpenSea)
