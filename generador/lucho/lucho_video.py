"""Video vertical de Lucho hablando con la voz de Mario.

Uso:
  python3 lucho_video.py --audio voz.m4a --guion guion.txt --titulo "Administración de Empresas" --out salida.mp4
  python3 lucho_video.py --preview --out muestra.mp4
"""
import argparse, os, subprocess, sys, math, wave, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monitos

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/truetype/google-fonts/"
FI = "/usr/share/fonts/opentype/inter/"
F = lambda p, s: ImageFont.truetype(p, s)
POP_B = FD + "Poppins-Bold.ttf"
INT_SB = FI + "Inter-SemiBold.otf"
WHITE, MUTED, LIME, DARK = (255, 255, 255), (200, 228, 212), (182, 243, 106), (10, 40, 29)
HANDLE = "@mario.moreno_dg"
END = 1.8  # segundos de cierre

def background():
    top = np.array([9, 38, 28], np.float32); bot = np.array([20, 112, 74], np.float32)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    arr = np.repeat((top + (bot - top) * y)[:, None, :], W, axis=1).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(deco)
    d.ellipse((-260, -200, 520, 580), fill=(182, 243, 106, 22))
    d.ellipse((640, 1460, 1400, 2220), fill=(255, 255, 255, 14))
    return Image.alpha_composite(img, deco)

def sprites(tmp):
    """Pre-render de Lucho: boca 0-2 × parpadeo × 5 posiciones de ala."""
    out = {}
    for o in range(3):
        for b in (False, True):
            for k, wv in enumerate([0, 0.25, 0.5, 0.75, 1.0]):
                p = os.path.join(tmp, f"l_{o}_{int(b)}_{k}.png")
                monitos.render_png("lucho", p, size=780, open_=o, blink=b, wave=wv)
                out[(o, b, k)] = Image.open(p).convert("RGBA")
    return out

def pill(d, cx, y, text, font, fg, bg, padx=34, h=74):
    w = d.textlength(text, font=font) + 2 * padx
    d.rounded_rectangle((cx - w / 2, y, cx + w / 2, y + h), radius=h / 2, fill=bg)
    bb = font.getbbox(text)
    d.text((cx - w / 2 + padx, y + (h - (bb[3] - bb[1])) / 2 - bb[1]), text, font=font, fill=fg)

def wrap(text, font, maxw, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def speech_bounds(src, thr="-38dB"):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"silencedetect=n={thr}:d=0.35", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    import re
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r)]
    dur = float(re.findall(r"Duration: (\d+):(\d+):([0-9.]+)", r)[0][2]) + 60 * float(re.findall(r"Duration: (\d+):(\d+):([0-9.]+)", r)[0][1])
    a = ends[0] if starts and starts[0] < 0.05 and ends else 0.0
    b = starts[-1] if starts and (len(ends) < len(starts) or ends[-1] >= dur - 0.15) else dur
    return max(0, a - 0.25), min(dur, b + 0.3)

def clean_audio(src, dst, extra_af=""):
    a, b = speech_bounds(src)
    af = "highpass=f=80,afftdn=nf=-25,agate=threshold=0.015:ratio=2.5:attack=5:release=150," + (extra_af + "," if extra_af else "") + "loudnorm=I=-16:TP=-1.5:LRA=11"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", src,
                    "-ac", "1", "-ar", "44100", "-af", af, dst], check=True)

def envelope(wav_path, nframes=None):
    with wave.open(wav_path) as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    hop = sr // FPS
    n = len(a) // hop
    rms = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    rms = np.convolve(rms, np.ones(2) / 2, mode="same")
    return rms / (np.percentile(rms, 95) + 1e-6), len(a) / sr

def chunks(text, max_chars=26):
    words = text.split()
    out, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) > max_chars and cur:
            out.append(cur); cur = w
        else:
            cur = t
        if cur.endswith((".", "?", "!")) and len(cur) >= 8:
            out.append(cur); cur = ""
    if cur: out.append(cur)
    return out

def voiced_segments(env, thr=0.12, min_sil=9):
    v = env > thr
    segs, i, n = [], 0, len(v)
    while i < n:
        if v[i]:
            j = i
            while j < n and (v[j] or (j + 1 < n and not v[j] and np.any(v[j:j + min_sil]))): j += 1
            segs.append((i, j)); i = j
        else:
            i += 1
    return [s for s in segs if s[1] - s[0] >= 4]

def units(text):
    import re
    return [u.strip() for u in re.findall(r"[^.,?!]+[.,?!]*", text) if u.strip()]

def sentences(text):
    import re
    return [x.strip() for x in re.findall(r"[^.?!]+[.?!]+", text) if x.strip()]

def subtitle_timeline(env, text, tol=0.7):
    """Si cada oración viene separada por una pausa clara, las empareja una a una.
    Si no, reparte el guion sobre el tiempo con voz y ajusta cada fin de frase a la pausa más cercana."""
    sents = sentences(text)
    big = voiced_segments(env, min_sil=18)
    if len(sents) > 1 and len(big) == len(sents):
        out = []
        for (a, b), sent in zip(big, sents):
            parts = chunks(sent)
            w = np.array([len(p) for p in parts], float); cum = np.concatenate([[0], np.cumsum(w)]) / w.sum()
            for k, p in enumerate(parts):
                out.append([int(a + cum[k] * (b - a)), int(a + cum[k + 1] * (b - a)), p])
        for k in range(len(out) - 1):
            out[k][1] = max(out[k][1], out[k + 1][0])
        return [tuple(x) for x in out]
    segs = voiced_segments(env)
    if not segs: return []
    us = units(text)
    durs = [b - a for a, b in segs]
    V = float(sum(durs))
    gaps = list(np.cumsum(durs)[:-1])  # posiciones (en tiempo con voz) de cada pausa
    def v2t(x):
        acc = 0
        for (a, b), d in zip(segs, durs):
            if x <= acc + d: return a + (x - acc)
            acc += d
        return segs[-1][1]
    lens = np.array([len(u) for u in us], float)
    xs = list(np.concatenate([[0], np.cumsum(lens)]) / lens.sum() * V)
    used = set()
    for k in range(1, len(xs) - 1):
        if gaps and us[k - 1].endswith((".", "?", "!")):
            j = int(np.argmin([abs(g - xs[k]) for g in gaps]))
            if abs(gaps[j] - xs[k]) <= tol * FPS and j not in used and gaps[j] > xs[k - 1]:
                xs[k] = gaps[j]; used.add(j)
    out = []
    for k, u in enumerate(us):
        parts = chunks(u) if len(u) > 26 else [u]
        w = np.array([len(p) for p in parts], float); cum = np.concatenate([[0], np.cumsum(w)]) / w.sum()
        for i, p in enumerate(parts):
            x0 = xs[k] + cum[i] * (xs[k + 1] - xs[k])
            out.append([int(v2t(x0 + 0.01)), 0, p])
    # fusiona trozos muy cortos (< 0.5 s) con el siguiente
    merged = []
    for k, it in enumerate(out):
        nxt = out[k + 1][0] if k + 1 < len(out) else segs[-1][1] + 6
        if merged and nxt - it[0] < 15 and len(merged[-1][2]) + len(it[2]) <= 30:
            merged[-1][2] += " " + it[2]
        else:
            merged.append(it)
    for k in range(len(merged)):
        merged[k][1] = merged[k + 1][0] if k + 1 < len(merged) else segs[-1][1] + 6
    return [tuple(x) for x in merged]

def render(out, env, dur, titulo, subs, audio_wav=None, categoria="CONOCE LA CARRERA"):
    tmp = tempfile.mkdtemp()
    S = sprites(tmp)
    BG = background()
    f_pill, f_title, f_sub, f_handle = F(INT_SB, 34), F(POP_B, 74), F(POP_B, 58), F(INT_SB, 46)
    total = int(math.ceil((dur + END) * FPS))
    speak_frames = len(env)
    rng = np.random.default_rng(3)
    blinks = set()
    t = int(1.2 * FPS)
    while t < total:
        blinks.update(range(t, t + 4)); t += int(rng.uniform(2.6, 4.2) * FPS)
    tmpv = out + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                          "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    for fi in range(total):
        img = BG.copy(); d = ImageDraw.Draw(img)
        e = env[fi] if fi < speak_frames else 0
        o = 2 if e > 0.55 else (1 if e > 0.2 else 0)
        # ala: saluda al inicio y al final
        tt = fi / FPS
        if tt < 1.6 or tt > dur + 0.2:
            k = int(round((math.sin(tt * 9) * 0.5 + 0.5) * 4))
        else:
            k = 0
        spr = S[(o, fi in blinks, k)]
        bob = int(math.sin(tt * 2.2) * 8 + (e * 6))
        img.alpha_composite(spr, (int(W / 2 - 390), 440 + bob))
        # encabezado
        pill(d, W / 2, 200, categoria, f_pill, DARK, LIME)
        lines = wrap(titulo, f_title, 940, d)
        for i, ln in enumerate(lines):
            w = d.textlength(ln, font=f_title); d.text((W / 2 - w / 2, 300 + i * 88), ln, font=f_title, fill=WHITE)
        # subtítulos
        if fi < speak_frames:
            cur = [s for s in subs if s[0] <= fi < s[1]]
            if cur:
                sl = wrap(cur[0][2], f_sub, 900, d)
                y0 = 1460
                for i, ln in enumerate(sl):
                    w = d.textlength(ln, font=f_sub)
                    x = W / 2 - w / 2
                    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                        d.text((x + dx, y0 + i * 74 + dy), ln, font=f_sub, fill=DARK)
                    d.text((x, y0 + i * 74), ln, font=f_sub, fill=WHITE if i else LIME)
        # cierre
        if tt > dur:
            a = min(1, (tt - dur) / 0.4)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            pill(ld, W / 2, 1470, HANDLE, f_handle, DARK, LIME, padx=44, h=96)
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            img = Image.alpha_composite(img, lay)
        p.stdin.write(img.convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0
    if audio_wav:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", audio_wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", f"apad=pad_dur={END}",
                        "-movflags", "+faststart", out], check=True)
        os.remove(tmpv)
    else:
        os.rename(tmpv, out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio"); ap.add_argument("--guion"); ap.add_argument("--titulo", default="Administración de Empresas")
    ap.add_argument("--categoria", default="CONOCE LA CARRERA")
    ap.add_argument("--out", required=True); ap.add_argument("--preview", action="store_true")
    ap.add_argument("--voz_personaje", action="store_true", help="sube el tono para que suene a personaje")
    a = ap.parse_args()
    if a.preview:
        rng = np.random.default_rng(7)
        n = int(5.5 * FPS)
        env = np.zeros(n)
        i = int(0.4 * FPS)
        while i < n - 10:
            L = rng.integers(3, 8); env[i:i + L] = np.sin(np.linspace(0, np.pi, L)) * rng.uniform(0.4, 1.0); i += L + rng.integers(0, 3)
        text = "¡Hola! Soy Lucho y hoy te cuento de Administración de Empresas."
        render(a.out, env, n / FPS, a.titulo, subtitle_timeline(env, text), None, a.categoria)
    else:
        wav = a.out + ".voz.wav"
        clean_audio(a.audio, wav, "rubberband=pitch=1.25:tempo=1.04:window=short:pitchq=quality" if a.voz_personaje else "")
        env, dur = envelope(wav)
        text = open(a.guion, encoding="utf-8").read().strip()
        render(a.out, env, dur, a.titulo, subtitle_timeline(env, text), wav, a.categoria)
        os.remove(wav)
