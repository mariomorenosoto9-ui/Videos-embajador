"""Tres personajes originales en SVG, con estados de boca y ojos para animar."""
import subprocess, sys, os

DARK = "#0A281D"
LIME = "#B6F36A"
LIME2 = "#8FD14F"
GREEN = "#16804A"
CREAM = "#F6F2E7"
ORANGE = "#F2A33A"
PINK = "#FF8FA3"

def eyes(cx1, cx2, cy, r, blink=False, look=0):
    if blink:
        return (f'<path d="M{cx1-r},{cy} Q{cx1},{cy+r*0.6} {cx1+r},{cy}" stroke="{DARK}" stroke-width="9" fill="none" stroke-linecap="round"/>'
                f'<path d="M{cx2-r},{cy} Q{cx2},{cy+r*0.6} {cx2+r},{cy}" stroke="{DARK}" stroke-width="9" fill="none" stroke-linecap="round"/>')
    s = ""
    for cx in (cx1, cx2):
        s += f'<ellipse cx="{cx+look}" cy="{cy}" rx="{r*0.78}" ry="{r}" fill="{DARK}"/>'
        s += f'<circle cx="{cx+look+r*0.28}" cy="{cy-r*0.38}" r="{r*0.3}" fill="#fff"/>'
        s += f'<circle cx="{cx+look-r*0.25}" cy="{cy+r*0.35}" r="{r*0.12}" fill="#fff"/>'
    return s

def mouth(cx, cy, w, open_):
    """open_: 0 cerrada (sonrisa), 1 media, 2 abierta."""
    if open_ == 0:
        return f'<path d="M{cx-w},{cy} Q{cx},{cy+w*0.7} {cx+w},{cy}" stroke="{DARK}" stroke-width="9" fill="none" stroke-linecap="round"/>'
    h = w * (0.55 if open_ == 1 else 1.0)
    return (f'<path d="M{cx-w},{cy} Q{cx},{cy+h*1.6} {cx+w},{cy} Q{cx},{cy+h*0.35} {cx-w},{cy} Z" fill="{DARK}" stroke="{DARK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<ellipse cx="{cx}" cy="{cy+h*0.85}" rx="{w*0.42}" ry="{h*0.28}" fill="{PINK}"/>')

def cap(cx, top, w=120, tilt=-8):
    return (f'<g transform="rotate({tilt} {cx} {top+30})">'
            f'<path d="M{cx-w*0.55},{top+28} L{cx-w*0.55},{top+62} Q{cx},{top+82} {cx+w*0.55},{top+62} L{cx+w*0.55},{top+28} Z" fill="{DARK}"/>'
            f'<polygon points="{cx-w},{top+20} {cx},{top-18} {cx+w},{top+20} {cx},{top+58}" fill="{DARK}"/>'
            f'<circle cx="{cx}" cy="{top+20}" r="8" fill="{LIME}"/>'
            f'<path d="M{cx},{top+20} Q{cx+w*0.75},{top+30} {cx+w*0.8},{top+70}" stroke="{LIME}" stroke-width="7" fill="none" stroke-linecap="round"/>'
            f'<rect x="{cx+w*0.8-9}" y="{top+66}" width="18" height="30" rx="6" fill="{LIME}"/>'
            f'</g>')

def svg_wrap(inner, w=600, h=760):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{inner}</svg>'

# ---------- 1. Alac, el alacrán duranguense ----------
def alac(open_=2, blink=False, wave=0.0):
    s = ""
    # cola: curva gruesa que sale de atrás y se enrosca sobre la cabeza
    tail = "M400,430 C540,400 545,190 420,150 C340,125 300,175 330,215"
    s += f'<path d="{tail}" stroke="{DARK}" stroke-width="64" fill="none" stroke-linecap="round"/>'
    s += f'<path d="{tail}" stroke="{LIME}" stroke-width="46" fill="none" stroke-linecap="round"/>'
    for (x1, y1, x2, y2) in ((470, 380, 505, 400), (495, 300, 535, 300), (480, 220, 512, 198), (420, 170, 432, 135), (365, 160, 360, 128)):
        s += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LIME2}" stroke-width="10" stroke-linecap="round"/>'
    s += f'<path d="M318,222 Q290,250 300,280 Q318,258 345,250" fill="{LIME}" stroke="{DARK}" stroke-width="9" stroke-linejoin="round"/>'
    # patitas
    for k in range(3):
        y = 540 + k * 22
        s += f'<path d="M{200 - k*6},{y} q-50,10 -70,40" stroke="{DARK}" stroke-width="12" fill="none" stroke-linecap="round"/>'
        s += f'<path d="M{400 + k*6},{y} q50,10 70,40" stroke="{DARK}" stroke-width="12" fill="none" stroke-linecap="round"/>'
    # brazos y pinzas
    wy = -40 * wave
    s += f'<path d="M200,470 Q140,440 120,{380+wy}" stroke="{DARK}" stroke-width="30" fill="none" stroke-linecap="round"/>'
    s += f'<path d="M200,470 Q140,440 120,{380+wy}" stroke="{LIME}" stroke-width="16" fill="none" stroke-linecap="round"/>'
    s += f'<path d="M400,470 Q460,440 480,380" stroke="{DARK}" stroke-width="30" fill="none" stroke-linecap="round"/>'
    s += f'<path d="M400,470 Q460,440 480,380" stroke="{LIME}" stroke-width="16" fill="none" stroke-linecap="round"/>'
    for cx, cy, sgn in ((118, 345 + wy, -1), (482, 345, 1)):
        s += f'<ellipse cx="{cx}" cy="{cy-18}" rx="40" ry="22" transform="rotate({-28*sgn} {cx} {cy-18})" fill="{LIME}" stroke="{DARK}" stroke-width="9"/>'
        s += f'<ellipse cx="{cx}" cy="{cy+16}" rx="34" ry="18" transform="rotate({24*sgn} {cx} {cy+16})" fill="{LIME2}" stroke="{DARK}" stroke-width="9"/>'
    # cuerpo
    s += f'<ellipse cx="300" cy="480" rx="160" ry="125" fill="{LIME}" stroke="{DARK}" stroke-width="10"/>'
    s += f'<path d="M190,540 Q300,590 410,540" stroke="{LIME2}" stroke-width="14" fill="none" stroke-linecap="round"/>'
    s += f'<ellipse cx="215" cy="505" rx="24" ry="14" fill="{PINK}" opacity="0.55"/><ellipse cx="385" cy="505" rx="24" ry="14" fill="{PINK}" opacity="0.55"/>'
    s += eyes(250, 350, 445, 30, blink)
    s += mouth(300, 505, 38, open_)
    s += cap(300, 330, 110, -10)
    return s

# ---------- 2. Lucho, el tecolote ----------
def lucho(open_=2, blink=False, wave=0.0):
    s = ""
    s += f'<path d="M205,640 l-18,40 M222,642 l0,42 M240,640 l18,40" stroke="{ORANGE}" stroke-width="12" stroke-linecap="round"/>'
    s += f'<path d="M360,640 l-18,40 M378,642 l0,42 M396,640 l18,40" stroke="{ORANGE}" stroke-width="12" stroke-linecap="round"/>'
    # alas
    wy = -70 * wave
    s += f'<ellipse cx="135" cy="{470+wy*0.6}" rx="55" ry="120" transform="rotate({20 + wave*60} 135 {470+wy*0.6})" fill="{GREEN}" stroke="{DARK}" stroke-width="10"/>'
    s += f'<ellipse cx="465" cy="470" rx="55" ry="120" transform="rotate(-20 465 470)" fill="{GREEN}" stroke="{DARK}" stroke-width="10"/>'
    # cuerpo
    s += f'<polygon points="170,250 200,160 250,240" fill="{GREEN}" stroke="{DARK}" stroke-width="10" stroke-linejoin="round"/>'
    s += f'<polygon points="430,250 400,160 350,240" fill="{GREEN}" stroke="{DARK}" stroke-width="10" stroke-linejoin="round"/>'
    s += f'<ellipse cx="300" cy="430" rx="175" ry="225" fill="{GREEN}" stroke="{DARK}" stroke-width="10"/>'
    s += f'<ellipse cx="300" cy="520" rx="110" ry="120" fill="#E3F2E6"/>'
    for k in range(3):
        y = 480 + k * 40
        s += f'<path d="M{270},{y} q15,14 30,0 q15,14 30,0" stroke="#B9D9C1" stroke-width="7" fill="none" stroke-linecap="round"/>'
    s += f'<circle cx="235" cy="350" r="72" fill="{CREAM}" stroke="{DARK}" stroke-width="9"/><circle cx="365" cy="350" r="72" fill="{CREAM}" stroke="{DARK}" stroke-width="9"/>'
    s += eyes(235, 365, 352, 36, blink)
    # pico (abre para hablar)
    op = {0: 0, 1: 12, 2: 26}[open_]
    if op:
        s += f'<ellipse cx="300" cy="{420+op/2}" rx="16" ry="{op/2+8}" fill="{DARK}"/>'
        s += f'<polygon points="286,{424+op} 314,{424+op} 300,{444+op}" fill="{ORANGE}" stroke="{DARK}" stroke-width="7" stroke-linejoin="round"/>'
    s += f'<polygon points="276,392 324,392 300,{424 if not op else 418}" fill="{ORANGE}" stroke="{DARK}" stroke-width="7" stroke-linejoin="round"/>'
    s += cap(300, 180, 125, 6)
    return s

# ---------- 3. Chispa ----------
def chispa(open_=2, blink=False, wave=0.0):
    s = ""
    # antena con chispa
    s += f'<path d="M300,215 Q290,170 310,130" stroke="{DARK}" stroke-width="10" fill="none" stroke-linecap="round"/>'
    s += (f'<polygon points="310,70 324,112 366,112 332,138 345,180 310,154 275,180 288,138 254,112 296,112" '
          f'fill="#FFD84D" stroke="{DARK}" stroke-width="8" stroke-linejoin="round"/>')
    # brazos
    wy = -60 * wave
    s += f'<path d="M150,470 Q90,430 85,{360+wy}" stroke="{DARK}" stroke-width="14" fill="none" stroke-linecap="round"/><circle cx="85" cy="{350+wy}" r="24" fill="{LIME}" stroke="{DARK}" stroke-width="9"/>'
    s += f'<path d="M450,470 Q510,500 515,560" stroke="{DARK}" stroke-width="14" fill="none" stroke-linecap="round"/><circle cx="515" cy="570" r="24" fill="{LIME}" stroke="{DARK}" stroke-width="9"/>'
    # pies
    s += f'<ellipse cx="240" cy="660" rx="50" ry="24" fill="{DARK}"/><ellipse cx="360" cy="660" rx="50" ry="24" fill="{DARK}"/>'
    # cuerpo blob
    s += (f'<path d="M300,210 C420,210 465,320 462,440 C460,580 390,650 300,650 C210,650 140,580 138,440 C135,320 180,210 300,210 Z" '
          f'fill="{LIME}" stroke="{DARK}" stroke-width="10"/>')
    s += f'<path d="M190,330 Q205,270 255,250" stroke="#fff" stroke-width="14" fill="none" stroke-linecap="round" opacity="0.55"/>'
    # lentes
    s += f'<circle cx="245" cy="400" r="56" fill="#ffffff" fill-opacity="0.35" stroke="{DARK}" stroke-width="9"/>'
    s += f'<circle cx="355" cy="400" r="56" fill="#ffffff" fill-opacity="0.35" stroke="{DARK}" stroke-width="9"/>'
    s += f'<path d="M290,395 Q300,385 310,395" stroke="{DARK}" stroke-width="9" fill="none"/>'
    s += eyes(245, 355, 402, 24, blink)
    s += f'<ellipse cx="200" cy="480" rx="24" ry="14" fill="{PINK}" opacity="0.6"/><ellipse cx="400" cy="480" rx="24" ry="14" fill="{PINK}" opacity="0.6"/>'
    s += mouth(300, 490, 42, open_)
    return s

CHARS = {"alac": alac, "lucho": lucho, "chispa": chispa}

def render_png(name, path, size=600, **kw):
    svg = svg_wrap(CHARS[name](**kw))
    p = subprocess.run(["rsvg-convert", "-w", str(size), "-f", "png", "-o", path], input=svg.encode(), check=True)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/monito"
    for n in CHARS:
        render_png(n, f"{out}/{n}.png", size=600, open_=2, wave=0.5)
