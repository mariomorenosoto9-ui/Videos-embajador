"""Pregunta del día — video animado vertical 1080x1920, 30 fps."""
import sys, os, subprocess, math, wave, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/truetype/google-fonts/"
FI = "/usr/share/fonts/opentype/inter/"
def F(name, size):
    return ImageFont.truetype(name, size)

POP_B = FD + "Poppins-Bold.ttf"
POP_M = FD + "Poppins-Medium.ttf"
INT_M = FI + "Inter-Medium.otf"
INT_SB = FI + "Inter-SemiBold.otf"

WHITE = (255, 255, 255)
MUTED = (200, 228, 212)
LIME = (182, 243, 106)
DARK = (10, 40, 29)
CARD = (255, 255, 255)

# ---------------- Contenido (parametrizable) ----------------
DATA = {
    "num": 1,
    "categoria": "Cultura general",
    "pregunta": "¿Cuál es la capital de Australia?",
    "opciones": ["Sídney", "Canberra", "Melbourne"],
    "correcta": 1,
    "dato": "Sídney es la ciudad más grande, pero la capital es Canberra.",
    "handle": "@mario.moreno_dg",
}
if len(sys.argv) > 2:
    DATA.update(json.load(open(sys.argv[2])))

# ---------------- Tiempos ----------------
S1, S2, S3, S4 = 1.8, 5.2, 3.2, 2.4
T1, T2, T3 = S1, S1 + S2, S1 + S2 + S3
TOTAL = T3 + S4
CD_START, CD_LEN = 1.4, 3.0  # cuenta regresiva dentro de la escena 2

# ---------------- Utilidades ----------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))
def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3
def prog(t, start, dur):
    return ease((t - start) / dur)

def gradient():
    top = np.array([9, 38, 28], dtype=np.float32)
    bot = np.array([20, 112, 74], dtype=np.float32)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    g = top + (bot - top) * y
    arr = np.repeat(g[:, None, :], W, axis=1)
    # viñeta suave + círculos decorativos
    img = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(deco)
    d.ellipse((-260, -200, 520, 580), fill=(182, 243, 106, 22))
    d.ellipse((640, 1460, 1400, 2220), fill=(255, 255, 255, 14))
    return Image.alpha_composite(img, deco)
BG = gradient()

def wrap(text, font, maxw, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= maxw:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

class Canvas:
    def __init__(self):
        self.img = BG.copy()
    def layer(self, alpha, fn):
        if alpha <= 0.002: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(lay))
        if alpha < 0.999:
            a = lay.getchannel("A").point(lambda v: int(v * alpha))
            lay.putalpha(a)
        self.img = Image.alpha_composite(self.img, lay)

def text_c(d, text, font, cx, y, fill):
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)

def pill(d, cx, y, text, font, fg, bg, padx=34, h=74):
    w = d.textlength(text, font=font) + 2 * padx
    d.rounded_rectangle((cx - w / 2, y, cx + w / 2, y + h), radius=h / 2, fill=bg)
    bb = font.getbbox(text)
    ty = y + (h - (bb[3] - bb[1])) / 2 - bb[1]
    d.text((cx - w / 2 + padx, ty), text, font=font, fill=fg)

# ---------------- Escenas ----------------
f_pill = F(INT_SB, 34)
f_title = F(POP_B, 150)
f_q = F(POP_B, 82)
f_opt = F(POP_B, 62)
f_letter = F(POP_B, 50)
f_num = F(POP_B, 64)
f_fact = F(INT_M, 46)
f_out1 = F(POP_B, 118)
f_out2 = F(INT_M, 52)
f_handle = F(INT_SB, 46)

def header(c, a):
    c.layer(a, lambda d: pill(d, W / 2, 250, f"PREGUNTA DEL DÍA  ·  #{DATA['num']}", f_pill, DARK, LIME))
    c.layer(a, lambda d: text_c(d, DATA["categoria"].upper(), F(INT_SB, 32), W / 2, 350, MUTED))

def scene1(t):
    c = Canvas()
    out = 1 - prog(t, S1 - 0.35, 0.35)
    p1, p2 = prog(t, 0.05, 0.55), prog(t, 0.25, 0.55)
    c.layer(p1 * out, lambda d: text_c(d, "PREGUNTA", f_title, W / 2 - (1 - p1) * 500, 720, WHITE))
    c.layer(p2 * out, lambda d: text_c(d, "DEL DÍA", f_title, W / 2 + (1 - p2) * 500, 880, LIME))
    p3 = prog(t, 0.6, 0.4)
    c.layer(p3 * out, lambda d: pill(d, W / 2, 1120 + (1 - p3) * 30, f"#{DATA['num']}  ·  {DATA['categoria']}", f_pill, WHITE, (255, 255, 255, 40)))
    return c.img

OPT_Y0, OPT_GAP, OPT_H, OPT_W = 900, 175, 140, 820

def draw_question(c, t, reveal=0.0):
    # t: tiempo dentro de la escena 2 (o fijo >S2 durante la 3)
    pq = prog(t, 0.0, 0.5)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = 82
    fq = F(POP_B, size)
    lines = wrap(DATA["pregunta"], fq, 900, tmp)
    while len(lines) > 3 and size > 56:
        size -= 4; fq = F(POP_B, size)
        lines = wrap(DATA["pregunta"], fq, 900, tmp)
    lh = int(size * 1.22)
    y0 = 800 - len(lines) * lh
    def dq(d):
        for i, ln in enumerate(lines):
            text_c(d, ln, fq, W / 2, y0 + i * lh + (1 - pq) * 40, WHITE)
    c.layer(pq, dq)
    for i, opt in enumerate(DATA["opciones"]):
        po = prog(t, 0.45 + i * 0.18, 0.45)
        correct = i == DATA["correcta"]
        alpha = po * (1 - 0.68 * reveal if not correct else 1)
        x0 = (W - OPT_W) / 2 + (1 - po) * 120
        y = OPT_Y0 + i * OPT_GAP
        grow = 10 * reveal if correct else 0
        def do(d, x0=x0, y=y, opt=opt, i=i, correct=correct, grow=grow):
            fill = tuple(int(CARD[k] + (LIME[k] - CARD[k]) * reveal) for k in range(3)) if correct else CARD
            d.rounded_rectangle((x0 - grow, y - grow, x0 + OPT_W + grow, y + OPT_H + grow), radius=36, fill=fill)
            cx, cy = x0 + 80, y + OPT_H / 2
            d.ellipse((cx - 44, cy - 44, cx + 44, cy + 44), fill=DARK)
            L = "ABC"[i]
            bb = f_letter.getbbox(L)
            d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), L, font=f_letter, fill=LIME)
            fo, size = f_opt, 62
            while d.textlength(opt, font=fo) > OPT_W - 300 and size > 36:
                size -= 2; fo = F(POP_B, size)
            bb = fo.getbbox(opt)
            d.text((x0 + 160, cy - (bb[3] - bb[1]) / 2 - bb[1]), opt, font=fo, fill=DARK)
            if correct and reveal > 0.5:
                k = clamp((reveal - 0.5) / 0.5)
                ex, ey = x0 + OPT_W - 90, cy
                pts = [(ex - 30, ey), (ex - 8, ey + 24), (ex + 34, ey - 26)]
                seg = pts[:2] if k < 0.4 else pts
                d.line(seg, fill=DARK, width=14, joint="curve")
        c.layer(alpha, do)

def scene2(t):
    c = Canvas()
    header(c, prog(t, 0.0, 0.4))
    draw_question(c, t)
    # cuenta regresiva
    pc = clamp((t - CD_START) / CD_LEN)
    shown = prog(t, CD_START - 0.3, 0.3)
    by = 1470
    def dbar(d):
        x0 = (W - OPT_W) / 2
        d.rounded_rectangle((x0, by, x0 + OPT_W, by + 20), radius=10, fill=(255, 255, 255, 50))
        wbar = OPT_W * (1 - pc)
        if wbar > 20:
            d.rounded_rectangle((x0, by, x0 + wbar, by + 20), radius=10, fill=LIME)
    c.layer(shown, dbar)
    if CD_START <= t < CD_START + CD_LEN:
        n = 3 - int(t - CD_START)
        frac = (t - CD_START) % 1.0
        pop = 1 - ease(frac / 0.25) * 0.0 if frac > 0.25 else 0.6 + 0.4 * ease(frac / 0.25)
        c.layer(1.0, lambda d: text_c(d, str(n), F(POP_B, int(70 * pop)), W / 2, 1520, WHITE))
    elif t >= CD_START + CD_LEN:
        c.layer(prog(t, CD_START + CD_LEN, 0.2), lambda d: text_c(d, "¡Tiempo!", f_num, W / 2, 1515, LIME))
    return c.img

def scene3(t):
    c = Canvas()
    header(c, 1.0)
    r = prog(t, 0.0, 0.45)
    draw_question(c, 99, reveal=r)
    pf = prog(t, 0.55, 0.4)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = wrap(DATA["dato"], f_fact, 860, tmp)
    def df(d):
        for i, ln in enumerate(lines):
            text_c(d, ln, f_fact, W / 2, 1465 + i * 62 + (1 - pf) * 20, WHITE)
    c.layer(pf, df)
    return c.img

def scene4(t):
    c = Canvas()
    p1, p2, p3 = prog(t, 0.0, 0.45), prog(t, 0.2, 0.45), prog(t, 0.4, 0.45)
    c.layer(p1, lambda d: text_c(d, "¿Le atinaste?", f_out1, W / 2, 700 + (1 - p1) * 40, WHITE))
    c.layer(p2, lambda d: text_c(d, "Comenta tu respuesta", f_out2, W / 2, 880 + (1 - p2) * 30, MUTED))
    c.layer(p2, lambda d: text_c(d, "y vuelve mañana por otra pregunta", f_out2, W / 2, 950 + (1 - p2) * 30, MUTED))
    c.layer(p3, lambda d: pill(d, W / 2, 1130 + (1 - p3) * 30, DATA["handle"], f_handle, DARK, LIME, padx=44, h=96))
    return c.img

SCENES = [(scene1, S1), (scene2, S2), (scene3, S3), (scene4, S4)]

def frame_at(T):
    if T < T1: return scene1(T)
    if T < T2: return scene2(T - T1)
    if T < T3: return scene3(T - T2)
    return scene4(T - T3)

# ---------------- Audio ----------------
def make_audio(path):
    sr = 44100
    n = int(TOTAL * sr) + sr // 10
    a = np.zeros(n, dtype=np.float32)
    def add(t0, sig):
        i = int(t0 * sr)
        a[i:i + len(sig)] += sig[: max(0, n - i)]
    def tone(freqs, dur, decay, vol):
        tt = np.arange(int(dur * sr)) / sr
        s = sum(np.sin(2 * np.pi * f * tt) for f in freqs) / len(freqs)
        env = np.exp(-tt * decay) * np.minimum(1, tt * 400)
        return (s * env * vol).astype(np.float32)
    # whoosh suave de entrada
    tt = np.arange(int(0.5 * sr)) / sr
    noise = np.random.default_rng(1).normal(0, 1, len(tt)).astype(np.float32)
    noise = np.convolve(noise, np.ones(40) / 40, mode="same")
    add(0.0, (noise * np.sin(np.pi * tt / 0.5) * 0.25).astype(np.float32))
    for k in range(3):
        add(T1 + CD_START + k, tone([1400], 0.08, 45, 0.35))
    add(T2, tone([880, 1320, 1760], 1.2, 3.5, 0.45))
    add(T3, tone([660, 990], 0.6, 5, 0.25))
    a = np.clip(a, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

# ---------------- Render ----------------
def render(out):
    tmpdir = out + "_parts"
    os.makedirs(tmpdir, exist_ok=True)
    parts = []
    t_start = 0.0
    for idx, (fn, dur) in enumerate(SCENES):
        nfr = int(round(dur * FPS))
        tmp = os.path.join(tmpdir, f"s{idx}.tmp.mp4")
        final = os.path.join(tmpdir, f"s{idx}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                              "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for k in range(nfr):
            p.stdin.write(fn(k / FPS).convert("RGB").tobytes())
        p.stdin.close()
        assert p.wait() == 0
        os.rename(tmp, final)
        parts.append(final)
    lst = os.path.join(tmpdir, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(x)}'\n" for x in parts))
    silent = os.path.join(tmpdir, "silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    wav = os.path.join(tmpdir, "a.wav")
    make_audio(wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if mode == "preview":
        for T in [1.0, T1 + 2.5, T2 + 1.5, T3 + 1.5]:
            frame_at(T).convert("RGB").save(f"/home/claude/video/prev_{T:.1f}.png")
    else:
        render(mode)
