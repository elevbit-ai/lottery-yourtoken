<div align="center">

# «Lottery yourToken»

### The prize that grows until someone reorders 30 characters
*O prêmio que cresce até alguém reordenar 30 caracteres*

**[🌐 Site](https://elevbit-ai.github.io/lottery-yourtoken/) · [🎬 Vídeo explicativo](https://elevbit-ai.github.io/lottery-yourtoken/#video) · [📜 Especificação](SPECIFICATION.md) · [🧩 Sistema Blockz10](https://github.com/elevbit-ai/blockz10)**

![Python](https://img.shields.io/badge/Python-3.10+-00e676?style=flat-square&logo=python&logoColor=white&labelColor=060806)
![JavaScript](https://img.shields.io/badge/JavaScript-WebCrypto-00e676?style=flat-square&logo=javascript&logoColor=white&labelColor=060806)
![Tests](https://img.shields.io/badge/tests-32%2F32%20passing-00e676?style=flat-square&labelColor=060806)
![License](https://img.shields.io/badge/license-MIT-00e676?style=flat-square&labelColor=060806)

Criado por **Joaquim Pedro de Morais Filho** · j360074@hotmail.com · 2021–2026

</div>

---

## O que é / What it is

**PT** — Lottery yourToken é a aplicação nº 2 do sistema
[Blockz10](https://github.com/elevbit-ai/blockz10): uma carteira-prêmio
pública cuja chave privada é encriptada com uma senha de **30
caracteres** — publicada **embaralhada**. Qualquer um pode aumentar o
prêmio depositando tokens ERC-20; quem descobrir a ordem correta dos
caracteres decripta a chave e leva tudo. Uma caça ao tesouro
criptográfica, verificável de ponta a ponta, sem servidor e sem
confiança no organizador após a publicação.

**EN** — Lottery yourToken is application #2 of the
[Blockz10](https://github.com/elevbit-ai/blockz10) system: a public
prize wallet whose private key is encrypted with a **30-character**
password — published **shuffled**. Anyone can grow the prize by
depositing ERC-20 tokens; whoever finds the characters' correct
ordering decrypts the key and takes everything. A cryptographic
treasure hunt, verifiable end to end, serverless, and trustless after
publication.

## Como funciona / How it works

```
┌─ ORGANIZADOR / ORGANIZER ─────────────────────────────────────────┐
│ 1. chave da carteira-prêmio  K   (tradição Blockz10: {e,1} × 64)  │
│ 2. senha P de 30 caracteres                                       │
│ 3. encripta K com P          → ciphertext + tag                   │
│ 4. embaralha P               → anagrama A                         │
│ 5. publica { A, salt, ciphertext, tag, endereço }  e descarta P   │
└───────────────────────────────────────────────────────────────────┘
┌─ COMUNIDADE / COMMUNITY ──────────────────────────────────────────┐
│ • patrocinadores depositam ERC-20 → o prêmio cresce on-chain      │
│ • jogadores testam reordenações de A — offline, sem permissão     │
│ • a ordem certa passa no MAC → decripta K → transfere o prêmio    │
└───────────────────────────────────────────────────────────────────┘
```

A verificação de um palpite é **local e determinística**:
`PBKDF2-HMAC-SHA256 → HMAC-SHA256`. Ninguém sabe que você venceu até a
transação aparecer. / Guess verification is **local and deterministic**.
Nobody knows you won until your transaction lands.

## Uso rápido / Quick start

```bash
git clone https://github.com/elevbit-ai/lottery-yourtoken
cd lottery-yourtoken
python tests/test_lottery.py     # 21 tests passed.
node tests/test_lottery.mjs      # 11 tests passed (cross-language vector).
```

```python
>>> import sys; sys.path.insert(0, "src")
>>> from lottery_yourtoken import create_lottery, verify_guess, reveal_key, generate_key
>>> bundle, password = create_lottery(generate_key(64))   # organizer side
>>> bundle["anagram"]                                     # what the public sees
'k7mwp2qr9tvx3jn8hsau5ybcedg64f'
>>> verify_guess(bundle, "não-é-esta-ordem" + "x" * 14)   # player side
False
>>> reveal_key(bundle, password)                          # the winning ordering
'e11eee1e1...'
```

JavaScript (browser ou Node ≥ 18) — mesma construção, byte a byte:

```js
import { createLottery, verifyGuess, revealKey } from "./src/js/lottery.js";
const { bundle, password } = await createLottery(myKey);
await verifyGuess(bundle, password);   // true
```

## Dificuldade calibrável / Tunable difficulty

A composição do anagrama é o dial do organizador / The anagram's
composition is the organizer's dial:

| Anagrama de 30 / 30-char anagram | Ordens / Orderings | bits |
|---|---|---|
| 30 únicos / unique | 30! ≈ 2,65 × 10³² | 107,7 |
| 15 × 2 repetições / repeats | ≈ 8,1 × 10²⁷ | 92,7 |
| 6 × 5 repetições / repeats | ≈ 8,9 × 10¹⁹ | 66,3 |
| 2 × 15 repetições / repeats | ≈ 1,55 × 10⁸ | 27,2 |

Cada palpite custa 200 000 iterações de PBKDF2 — busca exaustiva é cara
por construção. Um **cronograma de dicas** opcional (revelar uma posição
por período) garante que a loteria termina ([§7 da especificação](SPECIFICATION.md)). /
Each guess costs 200 000 PBKDF2 iterations — exhaustive search is
expensive by construction. An optional **hint schedule** (reveal one
position per period) guarantees the lottery ends ([spec §7](SPECIFICATION.md)).

## Estrutura do repositório / Repository layout

```
lottery-yourtoken/
├── src/lottery_yourtoken/   # implementação de referência (Python, stdlib pura)
│   ├── core.py              # protocolo: criar, verificar, decriptar, dificuldade
│   └── blockz.py            # codificação {e,1} canônica do Blockz10
├── src/js/lottery.js        # implementação espelho (WebCrypto, browser + Node)
├── tests/                   # 32 testes, incluindo vetor cruzado Python → JS
├── docs/                    # site (GitHub Pages): demo jogável + vídeo
├── media/                   # vídeo explicativo + poster
├── tools/make_video.py      # gerador do vídeo (PIL + ffmpeg)
└── SPECIFICATION.md         # especificação formal bilíngue
```

## Segurança / Security

- Primitivos padrão apenas: PBKDF2-HMAC-SHA256, keystream SHA-256 em
  modo contador, HMAC-SHA256. Sem dependências externas. / Standard
  primitives only. No external dependencies.
- O vencedor deve transferir tudo **em uma única transação**; considere
  um relay privado contra front-running. / The winner should sweep in
  **a single transaction**; consider a private relay against
  front-running.
- Especificação técnica e implementação de referência para fins
  educacionais; a legalidade de uma instância real com prêmios é
  responsabilidade do organizador, conforme sua jurisdição. / Technical
  spec and reference implementation for educational purposes; the
  legality of a live prized instance is the organizer's responsibility
  under their jurisdiction.

Detalhes completos em [SPECIFICATION.md §8](SPECIFICATION.md).

## Origem / Origin

- Conceito publicado em [blockz10.blogspot.com](https://blockz10.blogspot.com) (2021),
  parte do sistema **Blockz10** — registrado on-chain como NFT
  (coleção Blockz10 · OpenSea).
- Repositório do sistema completo: [elevbit-ai/blockz10](https://github.com/elevbit-ai/blockz10)

## Autor / Author

**Joaquim Pedro de Morais Filho**
📧 j360074@hotmail.com

Criador do sistema Blockz10 (2020) e da Lottery yourToken (2021).
Todo o conteúdo, conceito e autoria pertencem exclusivamente ao autor.

## Licença / License

[MIT](LICENSE) © 2020–2026 Joaquim Pedro de Morais Filho
