# Generates media/lottery-explainer.mp4 frame by frame (PIL + ffmpeg).
# Aesthetic follows the Blockz10 blog: black background, terminal green,
# prize gold for the lottery identity.
import os
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
BG = (6, 8, 6)
GREEN = (0, 230, 118)
DIM = (110, 200, 150)
WHITE = (235, 235, 235)
GREY = (150, 150, 150)
GOLD = (255, 213, 79)
GOLD_DIM = (200, 176, 110)
RED = (244, 67, 54)
BLUE = (129, 212, 250)

FONTS = r"C:\Windows\Fonts"
MONO_B = lambda s: ImageFont.truetype(os.path.join(FONTS, "consolab.ttf"), s)
MONO = lambda s: ImageFont.truetype(os.path.join(FONTS, "consola.ttf"), s)
SANS = lambda s: ImageFont.truetype(os.path.join(FONTS, "segoeui.ttf"), s)
SANS_B = lambda s: ImageFont.truetype(os.path.join(FONTS, "segoeuib.ttf"), s)

OUT = Path(__file__).resolve().parents[1] / "media"
FRAMES = OUT / "_frames"
FRAMES.mkdir(parents=True, exist_ok=True)

frames: list[tuple[str, float]] = []
_n = 0
rng = random.Random(155)  # deterministic build


def canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def save(img, dur):
    global _n
    name = f"f{_n:04d}.png"
    img.save(FRAMES / name)
    frames.append((name, dur))
    _n += 1


def center(d, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


def footer(d):
    center(d, H - 46, "Joaquim Pedro de Morais Filho  ·  j360074@hotmail.com", MONO(20), DIM)


def step_header(d, num, pt, en):
    d.ellipse([80, 56, 148, 124], outline=GOLD, width=5)
    w = d.textlength(str(num), font=MONO_B(40))
    d.text((114 - w / 2, 72), str(num), font=MONO_B(40), fill=GOLD)
    d.text((180, 62), pt, font=SANS_B(38), fill=WHITE)
    d.text((182, 116), en, font=SANS(24), fill=GREY)


def tiles(d, x, y, text, size, gap, color, box=None):
    f = MONO_B(int(size * 0.62))
    for i, ch in enumerate(text):
        x0 = x + i * (size + gap)
        d.rounded_rectangle([x0, y, x0 + size, y + size], radius=6,
                            outline=color, width=3, fill=box or (4, 18, 10))
        w = d.textlength(ch, font=f)
        d.text((x0 + (size - w) / 2, y + size * 0.16), ch, font=f, fill=color)


# ---- Scene 1: title ---------------------------------------------------------
img, d = canvas()
center(d, 165, "\u00abLottery yourToken\u00bb", MONO_B(74), GOLD)
center(d, 300, "O pr\u00eamio que cresce at\u00e9 algu\u00e9m reordenar 30 caracteres", SANS(32), WHITE)
center(d, 352, "The prize that grows until someone reorders 30 characters", SANS(24), GREY)
center(d, 440, "uma aplica\u00e7\u00e3o Blockz10 / a Blockz10 application", MONO(24), GREEN)
center(d, 510, "por Joaquim Pedro de Morais Filho \u00b7 desde 2021", SANS(26), DIM)
save(img, 5.0)

# ---- Scene 2: the concept ---------------------------------------------------
img, d = canvas()
center(d, 66, "Quatro pe\u00e7as p\u00fablicas, um segredo / Four public pieces, one secret",
       SANS_B(34), GOLD)
items = [
    ("CARTEIRA / WALLET", "endere\u00e7o p\u00fablico com o pr\u00eamio", "public address holding the prize"),
    ("CHAVE / KEY", "encriptada e publicada", "encrypted and published"),
    ("ANAGRAMA / ANAGRAM", "a senha \u2014 embaralhada", "the password \u2014 shuffled"),
    ("SEGREDO / SECRET", "apenas a ORDEM correta", "only the correct ORDER"),
]
y = 170
for i, (k, pt, en) in enumerate(items):
    col = GOLD if i == 3 else GREEN
    d.text((150, y), k, font=MONO_B(28), fill=col)
    d.text((560, y), pt, font=SANS(28), fill=WHITE)
    d.text((560, y + 38), en, font=SANS(22), fill=GREY)
    y += 100
footer(d)
save(img, 7.0)

# ---- Scene 3: step 1 — wallet & key ----------------------------------------
img, d = canvas()
step_header(d, 1, "A carteira-pr\u00eamio", "The prize wallet")
key = "".join(rng.choice("e1") for _ in range(64))
d.text((110, 200), "chave privada / private key  \u2014  alfabeto {e,1} \u00d7 64:", font=SANS(26), fill=WHITE)
d.text((110, 252), key[:32], font=MONO_B(34), fill=GREEN)
d.text((110, 296), key[32:], font=MONO_B(34), fill=GREEN)
d.text((110, 380), "hexadecimal v\u00e1lido p/ Ethereum \u00b7 valid Ethereum hex", font=SANS(24), fill=GREY)
d.text((110, 440), "e compress\u00edvel: Blockz10  \u00abeee11 \u2192 311\u00bb", font=SANS(26), fill=GOLD)
d.text((110, 484), "and compressible under the Blockz10 encoding", font=SANS(22), fill=GREY)
footer(d)
save(img, 8.0)

# ---- Scene 4: step 2 — the password ----------------------------------------
PWD = "k7mwp2qr9tvx3jn8hsau5ybcedg64f"
img, d = canvas()
step_header(d, 2, "A senha de 30 caracteres", "The 30-character password")
tiles(d, 95, 230, PWD[:15], 66, 6, GREEN)
tiles(d, 95, 320, PWD[15:], 66, 6, GREEN)
d.text((95, 440), "charset sem s\u00edmbolos amb\u00edguos \u00b7 unambiguous charset", font=SANS(24), fill=GREY)
d.text((95, 486), "a composi\u00e7\u00e3o \u00e9 o dial de dificuldade / composition is the difficulty dial",
       font=SANS(24), fill=GOLD)
footer(d)
save(img, 7.0)

# ---- Scene 5: step 3 — encryption -------------------------------------------
img, d = canvas()
step_header(d, 3, "Encriptar e autenticar", "Encrypt and authenticate")
rows = [
    ("senha / password", GREEN, "PBKDF2-HMAC-SHA256 \u00b7 200 000 itera\u00e7\u00f5es"),
    ("\u2193", GOLD, ""),
    ("enc_key \u2016 mac_key", WHITE, "64 bytes derivados / derived"),
    ("\u2193", GOLD, ""),
    ("ciphertext = chave \u2295 keystream SHA-256", GREEN, "XOR em modo contador / counter mode"),
    ("tag = HMAC-SHA256(salt \u2016 ciphertext)", GOLD, "autentica cada palpite / authenticates every guess"),
]
y = 195
for txt, col, note in rows:
    d.text((120, y), txt, font=MONO_B(30 if txt != "\u2193" else 34), fill=col)
    if note:
        d.text((760, y + 4), note, font=SANS(21), fill=GREY)
    y += 58 if txt != "\u2193" else 40
d.text((120, y + 16), "cada palpite custa 200 000 itera\u00e7\u00f5es \u2014 for\u00e7a bruta \u00e9 cara por constru\u00e7\u00e3o",
       font=SANS(23), fill=WHITE)
d.text((120, y + 52), "every guess costs 200 000 iterations \u2014 brute force is expensive by design",
       font=SANS(20), fill=GREY)
save(img, 9.0)

# ---- Scene 6: step 4 — shuffle animation ------------------------------------
chars = list(PWD)
states = [list(chars)]
for i in range(len(chars) - 1, 0, -1):
    j = rng.randrange(i + 1)
    chars[i], chars[j] = chars[j], chars[i]
    states.append(list(chars))
picks = [states[0]] + states[4::5] + [states[-1]]
for k, st in enumerate(picks):
    img, d = canvas()
    step_header(d, 4, "Embaralhar (Fisher\u2013Yates seguro)", "Shuffle (secure Fisher\u2013Yates)")
    d.text((95, 205), "senha / password:", font=SANS(22), fill=GREY)
    tiles(d, 95, 240, PWD[:15], 52, 5, (90, 130, 100))
    tiles(d, 95, 302, PWD[15:], 52, 5, (90, 130, 100))
    d.text((95, 395), "anagrama p\u00fablico / public anagram:", font=SANS(22), fill=GREY)
    s = "".join(st)
    col = GOLD if k == len(picks) - 1 else GREEN
    tiles(d, 95, 430, s[:15], 52, 5, col)
    tiles(d, 95, 492, s[15:], 52, 5, col)
    footer(d)
    save(img, 1.2 if k in (0, len(picks) - 1) else 0.45)
img, d = canvas()
step_header(d, 4, "Embaralhar (Fisher\u2013Yates seguro)", "Shuffle (secure Fisher\u2013Yates)")
s = "".join(states[-1])
tiles(d, 95, 250, s[:15], 66, 6, GOLD)
tiles(d, 95, 340, s[15:], 66, 6, GOLD)
d.text((95, 470), "mesmos caracteres \u00b7 ordem perdida / same characters \u00b7 order lost",
       font=SANS(26), fill=WHITE)
footer(d)
save(img, 3.5)

# ---- Scene 7: step 5 — publish & the growing prize --------------------------
img, d = canvas()
step_header(d, 5, "Publicar \u2014 e o pr\u00eamio cresce", "Publish \u2014 and the prize grows")
bundle_lines = [
    '{ "format": "lottery-yourtoken/1",',
    f'  "anagram": "{s}",',
    '  "kdf":    { "PBKDF2-HMAC-SHA256", 200000, salt },',
    '  "cipher": { "XOR-SHA256-CTR", ciphertext },',
    '  "mac":    { "HMAC-SHA256", tag },',
    '  "prize":  { "ethereum", "0x\u2026" } }',
]
y = 190
for ln in bundle_lines:
    d.text((100, y), ln, font=MONO(25), fill=GREEN)
    y += 40
d.text((100, y + 20), "a senha original \u00e9 descartada \u00b7 the original password is discarded",
       font=SANS(23), fill=GREY)
footer(d)
save(img, 7.0)

for amt in [1000, 2500, 6000, 14500, 32000, 75000]:
    img, d = canvas()
    step_header(d, 5, "Qualquer um pode depositar", "Anyone can deposit")
    center(d, 250, f"{amt:,} yTKN".replace(",", " "), MONO_B(86), GOLD)
    center(d, 380, "dep\u00f3sitos ERC-20 \u00b7 saldo p\u00fablico on-chain", SANS(28), WHITE)
    center(d, 428, "ERC-20 deposits \u00b7 balance public on-chain", SANS(22), GREY)
    footer(d)
    save(img, 0.55 if amt < 75000 else 3.0)

# ---- Scene 8: step 6 — play & win -------------------------------------------
img, d = canvas()
step_header(d, 6, "Jogar \u2014 verifica\u00e7\u00e3o offline", "Play \u2014 offline verification")
d.text((110, 200), "palpite errado / wrong guess:", font=SANS(24), fill=WHITE)
d.text((110, 244), "HMAC \u2260 tag", font=MONO_B(38), fill=RED)
d.text((450, 244), "\u2717", font=MONO_B(44), fill=RED)
d.text((110, 340), "ordem correta / correct ordering:", font=SANS(24), fill=WHITE)
d.text((110, 384), "HMAC = tag", font=MONO_B(38), fill=GREEN)
d.text((430, 384), "\u2713  decripta a chave / decrypts the key", font=MONO_B(30), fill=GOLD)
d.text((110, 480), "ningu\u00e9m sabe que voc\u00ea venceu at\u00e9 a transa\u00e7\u00e3o aparecer",
       font=SANS(24), fill=WHITE)
d.text((110, 516), "nobody knows you won until the transaction lands", font=SANS(20), fill=GREY)
footer(d)
save(img, 8.0)

img, d = canvas()
center(d, 130, "\U0001f3c6", SANS(90), GOLD)
center(d, 280, "VENCEDOR / WINNER", MONO_B(56), GOLD)
center(d, 380, "importa a chave \u00b7 transfere tudo em UMA transa\u00e7\u00e3o", SANS(28), WHITE)
center(d, 426, "import the key \u00b7 sweep everything in ONE transaction", SANS(22), GREY)
center(d, 500, "(relay privado contra front-running / private relay against front-running)",
       SANS(22), DIM)
save(img, 6.0)

# ---- Scene 9: difficulty math ------------------------------------------------
img, d = canvas()
center(d, 64, "A matem\u00e1tica / The mathematics", SANS_B(38), GOLD)
center(d, 130, "ordens distintas = n! / \u220f (repeti\u00e7\u00f5es!)", MONO_B(32), GREEN)
rows = [
    ("30 \u00fanicos / unique", "30!", "2,65 \u00d7 10\u00b3\u00b2", "107,7 bits"),
    ("15 s\u00edmbolos \u00d7 2", "30!/2\u00b9\u2075", "8,1 \u00d7 10\u00b2\u2077", "92,7 bits"),
    ("6 s\u00edmbolos \u00d7 5", "30!/(5!)\u2076", "8,9 \u00d7 10\u00b9\u2079", "66,3 bits"),
    ("2 s\u00edmbolos \u00d7 15", "C(30,15)", "1,55 \u00d7 10\u2078", "27,2 bits"),
]
y = 215
for a, b, c, e in rows:
    d.text((110, y), a, font=SANS(26), fill=WHITE)
    d.text((470, y), b, font=MONO_B(26), fill=GREY)
    d.text((720, y), c, font=MONO_B(28), fill=GOLD)
    d.text((1010, y), e, font=MONO(24), fill=GREEN)
    y += 66
d.text((110, y + 24), "o organizador escolhe: loteria de d\u00e9cadas ou puzzle de fim de semana",
       font=SANS(25), fill=WHITE)
d.text((110, y + 62), "the organizer chooses: decades-long lottery or weekend puzzle",
       font=SANS(21), fill=GREY)
save(img, 9.0)

# ---- Scene 10: hint schedule --------------------------------------------------
img, d = canvas()
center(d, 70, "Cronograma de dicas / Hint schedule", SANS_B(38), GOLD)
d.text((130, 180), "a cada per\u00edodo, o organizador revela uma posi\u00e7\u00e3o:", font=SANS(26), fill=WHITE)
d.text((130, 218), "each period, the organizer reveals one position:", font=SANS(21), fill=GREY)
reveal = [(1, s[0]), (7, s[6]), (19, s[18])]
y = 290
for pos, ch in reveal:
    d.text((180, y), f"posi\u00e7\u00e3o / position {pos:>2}  =  \u201c{ch}\u201d", font=MONO_B(32), fill=GREEN)
    y += 60
d.text((130, y + 20), "o espa\u00e7o de busca encolhe de forma verific\u00e1vel \u2014 a loteria sempre termina",
       font=SANS(25), fill=GOLD)
d.text((130, y + 58), "the search space shrinks verifiably \u2014 the lottery always ends",
       font=SANS(21), fill=GREY)
footer(d)
save(img, 7.0)

# ---- Scene 11: trust & security ------------------------------------------------
img, d = canvas()
center(d, 70, "Sem confian\u00e7a, sem servidor / Trustless, serverless", SANS_B(36), GOLD)
pts = [
    ("verifica\u00e7\u00e3o local: PBKDF2 + HMAC, offline", "local verification: PBKDF2 + HMAC, offline"),
    ("o organizador \u00e9 dispens\u00e1vel ap\u00f3s publicar", "the organizer is dispensable after publishing"),
    ("pr\u00eamio audit\u00e1vel on-chain a qualquer momento", "prize auditable on-chain at any time"),
    ("implementa\u00e7\u00f5es Python + JavaScript, 32 testes", "Python + JavaScript implementations, 32 tests"),
]
y = 180
for pt, en in pts:
    d.text((150, y), "\u25a0", font=SANS(24), fill=GOLD)
    d.text((200, y), pt, font=SANS_B(28), fill=WHITE)
    d.text((200, y + 38), en, font=SANS(22), fill=GREY)
    y += 96
footer(d)
save(img, 8.0)

# ---- Scene 12: credits ----------------------------------------------------------
img, d = canvas()
center(d, 150, "\u00abLottery yourToken\u00bb", MONO_B(64), GOLD)
center(d, 260, "uma aplica\u00e7\u00e3o do sistema \u00abBlockz10\u00bb", SANS(26), GREEN)
center(d, 330, "Criado por / Created by", SANS(26), GREY)
center(d, 375, "Joaquim Pedro de Morais Filho", SANS_B(40), WHITE)
center(d, 460, "j360074@hotmail.com", MONO_B(30), GOLD)
center(d, 525, "github.com/elevbit-ai/lottery-yourtoken", MONO(26), DIM)
center(d, 570, "\u00a9 2021\u20132026 \u00b7 conceito registrado on-chain \u00b7 NFT \u00b7 OpenSea", SANS(22), GREY)
save(img, 6.0)

# ---- assemble with ffmpeg --------------------------------------------------------
concat = FRAMES / "list.txt"
with open(concat, "w") as f:
    for name, dur in frames:
        f.write(f"file '{name}'\nduration {dur}\n")
    f.write(f"file '{frames[-1][0]}'\n")

mp4 = OUT / "lottery-explainer.mp4"
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat),
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
    "-shortest",
    "-vf", "fps=30,format=yuv420p,scale=1280:720",
    "-c:v", "libx264", "-preset", "slow", "-crf", "22",
    "-c:a", "aac", "-b:a", "64k",
    "-movflags", "+faststart",
    str(mp4),
]
subprocess.run(cmd, check=True, capture_output=True)
size = mp4.stat().st_size
print(f"OK {mp4} ({size/1e6:.2f} MB, {sum(x for _, x in frames):.1f}s, {len(frames)} frames)")

poster = Image.open(FRAMES / "f0000.png")
poster.save(OUT / "poster.png")
print("poster saved")
