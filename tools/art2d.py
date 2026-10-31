"""CLASS BUSTER — 2D art & sound: Korean menu graphics, title/help/credit/ending screens,
intermission labels, the student status-bar face, non-gore wall/flat replacements, sound effects.  (GPLv2)"""
import glob
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from wadlib import picture_from_rgba, decode_picture, encode_picture, dmx_sound


def _font(pref):
    for p in pref:
        g = glob.glob('/usr/share/fonts/**/' + p, recursive=True)
        if g:
            return g[0]
    raise SystemExit('Korean font not found (install fonts-nanum): ' + str(pref))


FONT_HEAVY = _font(['NanumSquareEB.ttf', 'NanumSquare_acEB.ttf', 'NanumGothicExtraBold.ttf', 'NanumSquareB.ttf', 'NanumGothicBold.ttf'])
FONT_BOLD = _font(['NanumSquareB.ttf', 'NanumGothicBold.ttf'])
FONT_BRUSH = _font(['NanumBrush.ttf', 'NanumGothicExtraBold.ttf', 'NanumGothicBold.ttf'])
SS = 4


def F(path, size):
    return ImageFont.truetype(path, size)


def _grad(w, h, stops):
    """vertical gradient, stops = [(pos0..1, '#rrggbb'), ...]"""
    ys = np.linspace(0, 1, h)[:, None]
    cols = [(p, np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)) for p, c in stops]
    out = np.zeros((h, 3))
    for (p0, c0), (p1, c1) in zip(cols, cols[1:]):
        m = (ys[:, 0] >= p0) & (ys[:, 0] <= p1)
        t = ((ys[m, 0] - p0) / max(p1 - p0, 1e-6))[:, None]
        out[m] = c0 * (1 - t) + c1 * t
    return np.repeat(out[:, None, :], w, 1).astype(np.uint8)


ACADEMIC_CYAN = [(0, '#e4ffff'), (0.35, '#77e8ee'), (0.72, '#21a9c3'), (1, '#14506f')]
DOOM_RED = ACADEMIC_CYAN  # Legacy name retained for compatibility; school edition uses cool lab colors.
GOLD = [(0, '#fff7c2'), (0.4, '#ffd66b'), (0.75, '#c99536'), (1, '#6d4e22')]


def text_rgba(text, size, stops=DOOM_RED, font=FONT_HEAVY, stroke=1.0, outline='#2a0000', shadow=1, extrude=0, tracking=0):
    """Supersampled, outlined, gradient-filled text -> RGBA ndarray at 1x."""
    f = F(font, size * SS)
    sw = max(1, int(stroke * SS))
    bb = f.getbbox(text, stroke_width=sw)
    w = bb[2] - bb[0] + (shadow + extrude) * SS + 2 * SS + tracking * SS * len(text)
    h = bb[3] - bb[1] + (shadow + extrude) * SS + 2 * SS
    ox, oy = -bb[0] + SS, -bb[1] + SS
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)

    def draw(dx, dy, fill, strokecol=None):
        if tracking:
            x = ox + dx
            for ch in text:
                d.text((x, oy + dy), ch, font=f, fill=fill, stroke_width=sw if strokecol else 0, stroke_fill=strokecol)
                x += f.getlength(ch) + tracking * SS
        else:
            d.text((ox + dx, oy + dy), text, font=f, fill=fill, stroke_width=sw if strokecol else 0, stroke_fill=strokecol)
    for e in range(extrude * SS, 0, -SS // 2):
        draw(e, e, (40, 0, 0, 255), (20, 0, 0, 255))
    if shadow:
        draw((shadow + extrude) * SS, (shadow + extrude) * SS, (0, 0, 0, 220), (0, 0, 0, 220))
    draw(0, 0, outline, outline)
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    if tracking:
        x = ox
        for ch in text:
            md.text((x, oy), ch, font=f, fill=255); x += f.getlength(ch) + tracking * SS
    else:
        md.text((ox, oy), text, font=f, fill=255)
    tb = mask.getbbox() or (0, 0, w, h)
    g = np.zeros((h, w, 3), np.uint8)
    g[tb[1]:tb[3]] = _grad(w, tb[3] - tb[1], stops)
    base.paste(Image.fromarray(g), (0, 0), mask)
    small = base.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    return np.array(small)


def patch_text(pal, text, size=15, stops=DOOM_RED, lo=0, to=0, **kw):
    a = text_rgba(text, size, stops, **kw)
    return picture_from_rgba(pal, a, lo, to, alpha_thresh=110), a.shape[1], a.shape[0]


# ---------------------------------------------------------------- full screens
def _noise(h, w, s, amp, seed=1):
    r = np.random.default_rng(seed)
    n = r.random((h // s + 2, w // s + 2))
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((w + 2 * s, h + 2 * s), Image.BICUBIC)
    return (np.array(im)[:h, :w] / 255.0 - 0.5) * amp


def school_scene(w=320, h=200, sky='night', seed=3):
    """Pixel-painted science academy exterior: observatory, lab windows and school crest."""
    night = sky == 'night'
    if night:
        img = _grad(w, h, [(0, '#071522'), (0.42, '#123d59'), (0.78, '#286b7c'), (1, '#d2a16a')]).astype(float)
    else:
        img = _grad(w, h, [(0, '#2d75b5'), (0.55, '#8ccbe5'), (1, '#f7e4b7')]).astype(float)
    img += _noise(h, w, 12, 10 if night else 7, seed)[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    rnd = np.random.default_rng(seed)

    # Stars / soft clouds
    if night:
        for _ in range(34):
            x, y = rnd.integers(0, w), rnd.integers(0, int(h * .38))
            c = (150, 220, 235) if rnd.random() < .7 else (255, 222, 160)
            d.point((int(x), int(y)), fill=c)
        d.ellipse((w - 61, 13, w - 43, 31), fill=(226, 242, 235))
        d.ellipse((w - 57, 9, w - 39, 27), fill=tuple(int(v) for v in img[18, max(0,w-48)]))
    else:
        d.ellipse((w - 64, 12, w - 34, 42), fill=(255, 244, 190))
        for cx, cy in [(55, 30), (166, 25), (248, 55)]:
            for k in range(3):
                d.ellipse((cx + k * 9 - 12, cy - 6 + (k % 2) * 2,
                           cx + k * 9 + 12, cy + 7), fill=(232, 246, 250))

    by = int(h * .49)
    # Campus foreground and wings
    wall = (20, 42, 58) if night else (76, 108, 124)
    face = (39, 76, 91) if night else (202, 220, 222)
    trim = (81, 170, 184) if night else (56, 125, 153)
    d.rectangle((13, by + 7, w - 13, h - 9), fill=wall, outline=(8, 26, 39))
    d.rectangle((18, by + 10, w - 18, h - 9), fill=face)
    # Central observatory / entrance block
    cx = w // 2
    d.rectangle((cx - 33, by - 24, cx + 33, h - 9), fill=wall)
    d.rectangle((cx - 28, by - 18, cx + 28, h - 9), fill=trim)
    d.polygon([(cx - 38, by - 24), (cx, by - 42), (cx + 38, by - 24)], fill=(14, 38, 54), outline=(116, 204, 210))
    d.rectangle((cx - 20, by - 13, cx + 20, by - 8), fill=(17, 49, 66), outline=(174, 220, 220))
    # Crest: open book + atom rings
    crest_y = by - 28
    d.ellipse((cx - 8, crest_y - 8, cx + 8, crest_y + 8), outline=(255, 215, 116), width=1)
    d.ellipse((cx - 8, crest_y - 3, cx + 8, crest_y + 3), outline=(108, 225, 230), width=1)
    d.ellipse((cx - 2, crest_y - 2, cx + 2, crest_y + 2), fill=(255, 230, 150))
    # Observatory dome
    d.rectangle((cx - 9, by - 52, cx + 9, by - 43), fill=(24, 54, 74), outline=(118, 205, 214))
    d.arc((cx - 13, by - 65, cx + 13, by - 39), 180, 360, fill=(152, 224, 226), width=2)
    d.line((cx, by - 58, cx + 8, by - 49), fill=(255, 218, 135), width=2)

    # Windows aligned as lab panels
    for row in range(4):
        for col in range(13):
            x = 27 + col * max(1, (w - 54) // 13)
            if abs(x - cx) < 36:
                continue
            y = by + 14 + row * 19
            lit = rnd.random() < (0.63 if night else 0.2)
            if lit:
                color = (255, 216, 130) if (row + col) % 3 else (112, 225, 229)
            else:
                color = (32, 74, 94) if night else (125, 177, 196)
            d.rectangle((x, y, x + 8, y + 10), fill=color, outline=(13, 39, 56))
            d.line((x + 4, y, x + 4, y + 10), fill=(22, 53, 67))
    # Entrance steps and path
    d.rectangle((cx - 13, by + 6, cx + 13, h - 10), fill=(16, 39, 54))
    d.rectangle((cx - 9, by + 10, cx + 9, h - 10), fill=(27, 65, 81))
    for yy in range(h - 24, h - 8, 4):
        d.line((cx - 13, yy, cx + 13, yy), fill=(82, 150, 164), width=1)
    ground = (13, 35, 46) if night else (74, 130, 102)
    d.rectangle((0, h - 9, w, h), fill=ground)
    d.line((0, h - 11, w, h - 11), fill=(96, 194, 183) if night else (180, 205, 143), width=1)
    return np.array(im)

def paste_rgba(dst, src, x, y):
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(float)
    a = s[..., 3:4] / 255
    dst[y0:y1, x0:x1] = (dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a).astype(np.uint8)


def centered(dst, src, y):
    paste_rgba(dst, src, (dst.shape[1] - src.shape[1]) // 2, y)


def logo_rgba(scale=1.0):
    big = text_rgba('교실 대소동', int(46 * scale), GOLD, FONT_HEAVY, stroke=1.4, outline='#102536', shadow=0, extrude=3)
    sub = text_rgba('과학 아카데미', int(10 * scale), ACADEMIC_CYAN, FONT_HEAVY, stroke=1, outline='#061a2a', shadow=1)
    w = max(big.shape[1], sub.shape[1])
    out = np.zeros((big.shape[0] + sub.shape[0] - 2, w, 4), np.uint8)
    out[:big.shape[0], (w - big.shape[1]) // 2:(w - big.shape[1]) // 2 + big.shape[1]] = big
    y = big.shape[0] - 2
    sl = out[y:y + sub.shape[0], (w - sub.shape[1]) // 2:(w - sub.shape[1]) // 2 + sub.shape[1]]
    m = sub[..., 3:4] > 0
    sl[:] = np.where(m, sub, sl)
    return out


def full_rgb_to_pic(pal, rgb):
    a = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
    return picture_from_rgba(pal, a, 0, 0)


def titlepic():
    bg = school_scene(320, 200, 'night', 17)
    # Subtle technical grid and warning strip
    im = Image.fromarray(bg); d = ImageDraw.Draw(im)
    for x in range(8, 320, 16):
        d.line((x, 0, x, 200), fill=(30, 78, 91), width=1)
    for y in range(8, 200, 16):
        d.line((0, y, 320, y), fill=(26, 65, 81), width=1)
    bg = np.array(im)
    lg = logo_rgba(0.9)
    centered(bg, lg, 17)
    tag = text_rgba('과학고 연구동 비상 경보 발생!', 10, [(0, '#ffffff'), (1, '#bdf7f0')], FONT_BOLD, stroke=1, outline='#061522', shadow=1)
    centered(bg, tag, 88)
    tag2 = text_rgba('과목별 연구 구역을 복구하고 출구를 확보하라', 8, GOLD, FONT_BOLD, stroke=0.7, outline='#061522', shadow=1)
    centered(bg, tag2, 109)
    im = Image.fromarray(bg); d = ImageDraw.Draw(im)
    d.rectangle((8, 178, 312, 192), fill=(8, 23, 35), outline=(74, 177, 186))
    d.text((14, 181), '과학고 연구동  /  교육 시뮬레이션  01', font=F(FONT_HEAVY, 7), fill=(143, 226, 229))
    return np.array(im)

def text_screen(title, lines, bgkind='board', seed=5, title_stops=GOLD):
    if bgkind == 'board':
        bg = np.zeros((200, 320, 3), float) + np.array([28, 64, 44])
        bg += _noise(200, 320, 6, 22, seed)[..., None]
        bg = np.clip(bg, 0, 255).astype(np.uint8)
        im = Image.fromarray(bg); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 319, 199), outline=(120, 80, 40), width=6)
        d.rectangle((6, 6, 313, 193), outline=(70, 46, 22), width=1)
        d.rectangle((40, 186, 120, 190), fill=(240, 240, 240))
        bg = np.array(im)
    else:
        bg = school_scene(320, 200, bgkind, seed)
        bg = (bg * 0.45).astype(np.uint8)
    t = text_rgba(title, 18, title_stops, FONT_HEAVY, stroke=1.2, outline='#102a3d', shadow=1)
    centered(bg, t, 12)
    y = 12 + t.shape[0] + 6
    for ln in lines:
        if not ln:
            y += 6; continue
        col = [(0, '#ffffff'), (1, '#e8e8e8')]
        if ln.startswith('*'):
            ln = ln[1:]; col = [(0, '#fff2a0'), (1, '#ffc040')]
        r = text_rgba(ln, 9, col, FONT_BOLD, stroke=0.7, outline='#061522', shadow=1)
        paste_rgba(bg, r, 22, y)
        y += r.shape[0] - 2
    return bg


def help_screen():
    # Compact Korean layout at native Doom resolution; every row stays inside its panel.
    im = Image.new('RGB', (320, 200), (8, 20, 31))
    px = im.load()
    for y in range(200):
        t = y / 199
        col = (int(8 + 7*t), int(23 + 25*t), int(36 + 34*t))
        for x in range(320):
            px[x, y] = col
    d = ImageDraw.Draw(im)
    d.rectangle((3, 3, 316, 196), outline=(76, 183, 194), width=2)
    d.rectangle((7, 7, 312, 30), fill=(14, 43, 59), outline=(48, 119, 138))
    title = text_rgba('작전 안내 · 조작법', 15, GOLD, FONT_HEAVY, stroke=1, outline='#061522', shadow=1)
    bg = np.array(im)
    centered(bg, title, 8)
    im = Image.fromarray(bg)
    d = ImageDraw.Draw(im)
    cards = [(10, 38, 154, 165), (166, 38, 310, 165)]
    for box in cards:
        d.rounded_rectangle(box, radius=3, fill=(12, 34, 48), outline=(50, 120, 139), width=1)

    heading = F(FONT_HEAVY, 8)
    body = F(FONT_BOLD, 7)
    sections = [
        (18, 44, '이동', ['W A S D  전진 · 후진 · 옆걸음', '↑ ↓  전진 · 후진', '← →  좌우 회전', 'Shift  달리기']),
        (18, 96, '시점 조작', ['화면 클릭 → 마우스 고정', '마우스 이동 → 시점 회전']),
        (18, 130, '행동', ['클릭 / Ctrl  도구 사용', 'Space / E  문 · 장치 조작']),
        (174, 44, '도구 선택', ['1  연필 · 분필 도구', '2  분필 발사기', '3  지우개 연사기', '4  형광펜 발사기', '5  종이비행기 발사기', '6  레이저 자', '7  최종 과제 장치']),
        (174, 115, '탐색 · 저장', ['Tab  자동 지도', 'F2 / F3  저장 / 불러오기', 'Esc  메뉴 · 마우스 해제']),
    ]
    for x, y, head, rows in sections:
        d.text((x, y), head, font=heading, fill=(255, 214, 112), stroke_width=1, stroke_fill=(34, 42, 43))
        yy = y + 11
        for row in rows:
            d.text((x, yy), row, font=body, fill=(223, 239, 239))
            yy += 9

    d.rectangle((10, 171, 310, 190), fill=(23, 53, 65), outline=(77, 164, 172))
    d.text((16, 174), '목표: 세 가지 열쇠 메달을 모아 출구 장치를 작동하라!', font=F(FONT_HEAVY, 7), fill=(255, 229, 151))
    d.text((16, 183), '교육용 비잔혹 그래픽 · 과목 마스코트는 종이 조각으로 흩어집니다.', font=F(FONT_BOLD, 6), fill=(155, 211, 211))
    return np.array(im)

def credit_screen():
    return text_screen('제작 · 라이선스 안내', [
        '*교실 대소동  /  CLASS BUSTER', '학생을 위한 비잔혹 교육용 FPS 프로젝트',
        '', '*엔진 및 코드', 'DOOM  ©1993 id Software — GNU GPL v2',
        'Chocolate Doom  ·  Simon Howard 외 기여자',
        'doomgeneric  ·  ozkl 및 기여자',
        '', '*게임 데이터 및 리소스', 'Freedoom 프로젝트 — BSD 라이선스 기반 데이터',
        '과목 마스코트 · 교내 배경 · 한글 메뉴 · 도구 스프라이트',
        '본 프로젝트에서 새로 제작하거나 교육용으로 재구성',
        '', '*라이선스', 'LICENSE 및 COPYING-FREEDOOM.txt를 함께 확인하세요.',
    ], 'night', 12)


def ending_screen(kind):
    if kind == 'VICTORY2':
        bg = school_scene(320, 200, 'day', 31)
        t = text_rgba('1학기 연구 완료!', 25, GOLD, FONT_HEAVY, stroke=1.2, outline='#16334a', extrude=2)
        centered(bg, t, 22)
        s = text_rgba('다음 목표: 과학관 연구 장비를 점검하라', 10, ACADEMIC_CYAN, FONT_BOLD, stroke=1, outline='#092438')
        centered(bg, s, 22 + t.shape[0] + 7)
        im = Image.fromarray(bg); d = ImageDraw.Draw(im)
        d.rounded_rectangle((82, 150, 238, 185), radius=4, fill=(13, 43, 60), outline=(72, 177, 190), width=2)
        d.ellipse((145, 153, 175, 183), fill=(238, 193, 74), outline=(255, 240, 184), width=2)
        d.text((151, 161), 'A+', font=F(FONT_HEAVY, 9), fill=(20, 50, 65))
        return np.array(im)
    bg = school_scene(320, 200, 'day', 33)
    t = text_rgba('연구동 복구 완료!', 25, GOLD, FONT_HEAVY, stroke=1.3, outline='#17344a', extrude=2)
    centered(bg, t, 20)
    s = text_rgba('모든 과목 구역을 정리했습니다. 수고했어요!', 10, ACADEMIC_CYAN, FONT_BOLD, outline='#092438')
    centered(bg, s, 20 + t.shape[0] + 6)
    im = Image.fromarray(bg); d = ImageDraw.Draw(im)
    d.rectangle((70, 145, 250, 187), fill=(12, 41, 60), outline=(76, 169, 184), width=2)
    d.text((119, 153), '과학 아카데미', font=F(FONT_HEAVY, 10), fill=(152, 233, 229))
    d.text((133, 169), '임무 완료', font=F(FONT_HEAVY, 8), fill=(255, 218, 125))
    return np.array(im)

def panorama(i):
    bg = school_scene(320, 200, 'day', 20 + i)
    if i == 0:
        t = text_rgba('시험 끝!', 30, GOLD, FONT_HEAVY, stroke=1.3, outline='#16344b', extrude=2)
        centered(bg, t, 24)
    return bg


# ---------------------------------------------------------------- status-bar face
def face_rgba(w, h, pain, look=0, mood='normal', turn=0):
    S = 8
    W, H = w * S, h * S
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = W // 2 + turn * 2 * S
    skin = (242, 200, 160) if mood != 'god' else (255, 220, 120)
    if pain >= 3:
        skin = (226, 186, 150)
    d.ellipse((cx - 10 * S, 3 * S, cx + 10 * S, H - 1 * S), fill=skin, outline=(60, 30, 20), width=S)
    d.ellipse((cx - 12 * S + turn * S, 11 * S, cx - 8 * S + turn * S, 18 * S), fill=skin, outline=(60, 30, 20), width=S // 2)
    d.ellipse((cx + 8 * S + turn * S, 11 * S, cx + 12 * S + turn * S, 18 * S), fill=skin, outline=(60, 30, 20), width=S // 2)
    hair = (30, 26, 30)
    d.chord((cx - 11 * S, 1 * S, cx + 11 * S, 17 * S), 180, 360, fill=hair)
    d.polygon([(cx - 10 * S, 9 * S), (cx - 4 * S, 6 * S), (cx + 2 * S, 9 * S), (cx + 8 * S, 6 * S), (cx + 10 * S, 9 * S), (cx + 10 * S, 6 * S), (cx - 10 * S, 6 * S)], fill=hair)
    if pain >= 2:
        for k in range(3):
            x = cx - 8 * S + k * 7 * S
            d.polygon([(x, 3 * S), (x + 2 * S, -1 * S + k * S), (x + 4 * S, 3 * S)], fill=hair)
    ey = 14 * S
    ex = [cx - 5 * S + turn * S, cx + 5 * S + turn * S]
    if mood == 'dead':
        for x in ex:
            d.line((x - 3 * S, ey, x + 3 * S, ey), fill=(20, 35, 48), width=S)
        d.arc((cx - 3 * S, 19 * S, cx + 3 * S, 24 * S), 200, 340, fill=(90, 40, 30), width=S)
        f = F(FONT_HEAVY, 7 * S)
        d.text((cx + 5 * S, 0), 'z', font=f, fill=(120, 180, 255, 255))
        d.text((cx + 8 * S, -4 * S), 'Z', font=f, fill=(160, 210, 255, 255))
    elif mood == 'god':
        d.rounded_rectangle((cx - 10 * S, ey - 3 * S, cx + 10 * S, ey + 3 * S), radius=2 * S, fill=(15, 15, 25))
        d.line((cx - 7 * S, ey - 2 * S, cx - 4 * S, ey - 2 * S), fill=(200, 220, 255), width=S)
        d.arc((cx - 5 * S, 18 * S, cx + 5 * S, 25 * S), 20, 160, fill=(90, 30, 20), width=S)
    else:
        er = 3 * S if mood != 'ouch' else 4 * S
        for i, x in enumerate(ex):
            d.ellipse((x - er, ey - er, x + er, ey + er), fill=(255, 255, 255), outline=(40, 30, 30), width=S // 2)
            if pain >= 4 and mood == 'normal':
                d.arc((x - 2 * S, ey - 2 * S, x + 2 * S, ey + 2 * S), 0, 300, fill=(40, 40, 120), width=S // 2 + 1)
            else:
                px = x + look * S + turn * S
                pr = S + S // 2 if mood != 'ouch' else S
                d.ellipse((px - pr, ey - pr, px + pr, ey + pr), fill=(30, 24, 20))
            if pain >= 3:
                d.arc((x - 3 * S, ey + 1 * S, x + 3 * S, ey + 5 * S), 20, 160, fill=(150, 110, 120), width=S // 2)
        if mood == 'kill':
            d.line((ex[0] - 4 * S, ey - 6 * S, ex[0] + 3 * S, ey - 3 * S), fill=hair, width=S + S // 2)
            d.line((ex[1] + 4 * S, ey - 6 * S, ex[1] - 3 * S, ey - 3 * S), fill=hair, width=S + S // 2)
        else:
            dy = 1 if pain >= 2 else 0
            d.line((ex[0] - 3 * S, ey - 5 * S + dy * S, ex[0] + 3 * S, ey - 5 * S - dy * S), fill=hair, width=S)
            d.line((ex[1] - 3 * S, ey - 5 * S - dy * S, ex[1] + 3 * S, ey - 5 * S + dy * S), fill=hair, width=S)
        my = 22 * S
        mx = cx + turn * S
        if mood == 'ouch':
            d.ellipse((mx - 3 * S, my - 3 * S, mx + 3 * S, my + 3 * S), fill=(110, 20, 20), outline=(60, 10, 10), width=S // 2)
        elif mood == 'evil':
            # Retain the engine mood state but render a puzzled student expression.
            d.arc((mx - 6 * S, my - 4 * S, mx + 6 * S, my + 5 * S), 20, 160, fill=(55, 100, 135), width=S)
            d.ellipse((mx - 2 * S, my - 1 * S, mx + 2 * S, my + 1 * S), fill=(255, 255, 255))
        elif mood == 'kill':
            d.rectangle((mx - 5 * S, my - 2 * S, mx + 5 * S, my + 2 * S), fill=(255, 255, 255), outline=(60, 10, 10), width=S // 2)
            for k in range(-3, 4, 2):
                d.line((mx + k * S, my - 2 * S, mx + k * S, my + 2 * S), fill=(120, 120, 120), width=S // 3)
        elif pain <= 1:
            d.arc((mx - 5 * S, my - 5 * S, mx + 5 * S, my + 2 * S), 20, 160, fill=(110, 30, 20), width=S)
        elif pain == 2:
            d.line((mx - 4 * S, my, mx + 4 * S, my), fill=(110, 30, 20), width=S)
        else:
            d.arc((mx - 5 * S, my - 1 * S, mx + 5 * S, my + 5 * S), 200, 340, fill=(110, 30, 20), width=S)
    # pain accessories (sweat, band-aids, dizzy) — never blood
    if pain >= 1 and mood != 'dead':
        x0 = cx + 9 * S
        d.ellipse((x0 - 1 * S, 8 * S, x0 + 2 * S, 12 * S), fill=(130, 200, 255), outline=(40, 90, 160), width=S // 2)
    if pain >= 2 and mood != 'dead':
        bx, by = cx - 6 * S + turn * S, 19 * S
        d.rounded_rectangle((bx - 4 * S, by - 1 * S, bx + 3 * S, by + 2 * S), radius=S, fill=(240, 200, 150), outline=(150, 110, 70), width=S // 2)
        d.line((bx - 1 * S, by - 1 * S, bx - 1 * S, by + 2 * S), fill=(150, 110, 70), width=S // 3)
    if pain >= 3 and mood != 'dead':
        bx, by = cx + 3 * S + turn * S, 7 * S
        d.rounded_rectangle((bx - 5 * S, by - 1 * S, bx + 4 * S, by + 2 * S), radius=S, fill=(250, 250, 250), outline=(160, 160, 170), width=S // 2)
        d.line((bx - 4 * S, by - 1 * S, bx + 3 * S, by + 2 * S), fill=(200, 60, 60), width=S // 2)
    if pain >= 4 and mood != 'dead':
        for k in range(3):
            a = k * 2.1
            x, y = cx + 9 * math.cos(a) * S, 1 * S + 2 * math.sin(a) * S
            d.ellipse((x - 1.5 * S, y - 1.5 * S + 2 * S, x + 1.5 * S, y + 1.5 * S + 2 * S), fill=(255, 230, 60))
    out = np.array(im.resize((w, h), Image.LANCZOS))
    return out


def build_faces(wad, pal):
    n = 0
    for li, (name, data) in enumerate(wad.lumps):
        if not name.startswith('STF') or name.startswith('STFB'):
            continue
        try:
            idx, m, lo, to = decode_picture(data)
        except Exception:
            continue
        h, w = idx.shape
        pain = int(name[-2]) if name[-2].isdigit() and not name.startswith('STFST') else 0
        if name.startswith('STFST'):
            pain = int(name[5]); look = [-1, 0, 1][int(name[6])]
            a = face_rgba(w, h, pain, look)
        elif name.startswith('STFTL'):
            a = face_rgba(w, h, int(name[5]), -1, turn=-1)
        elif name.startswith('STFTR'):
            a = face_rgba(w, h, int(name[5]), 1, turn=1)
        elif name.startswith('STFOUCH'):
            a = face_rgba(w, h, int(name[7]), 0, 'ouch')
        elif name.startswith('STFEVL'):
            a = face_rgba(w, h, int(name[6]), 0, 'evil')
        elif name.startswith('STFKILL'):
            a = face_rgba(w, h, int(name[7]), 0, 'kill')
        elif name.startswith('STFGOD'):
            a = face_rgba(w, h, 0, 0, 'god')
        elif name.startswith('STFDEAD'):
            a = face_rgba(w, h, 0, 0, 'dead')
        else:
            continue
        wad.lumps[li][1] = picture_from_rgba(pal, a, lo, to, alpha_thresh=100)
        n += 1
    return n


# ---------------------------------------------------------------- walls / flats
def pic_rgb(pal, data):
    idx, m, lo, to = decode_picture(data)
    return pal.rgb[idx].astype(np.uint8), m, lo, to


def red_to_ink(rgb):
    r, g, b = [rgb[..., i].astype(float) for i in range(3)]
    red = (r > g * 1.35 + 12) & (r > b * 1.35 + 12)
    v = r
    out = rgb.copy().astype(float)
    out[red] = np.stack([v[red] * 0.22, v[red] * 0.32, v[red] * 1.0], -1)
    return np.clip(out, 0, 255).astype(np.uint8)


def corkboard(w, h, seed):
    rnd = np.random.default_rng(seed)
    base = np.zeros((h, w, 3)) + np.array([176, 128, 78]) + _noise(h, w, 3, 40, seed)[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    cols = [(250, 250, 240), (255, 240, 140), (180, 220, 255), (255, 190, 200), (200, 255, 200)]
    for k in range(max(2, w * h // 900)):
        pw, ph = int(rnd.integers(12, 26)), int(rnd.integers(14, 30))
        x, y = int(rnd.integers(0, max(1, w - pw))), int(rnd.integers(0, max(1, h - ph)))
        c = cols[k % len(cols)]
        d.rectangle((x, y, x + pw, y + ph), fill=c, outline=(120, 100, 80))
        for ly in range(y + 4, y + ph - 2, 3):
            d.line((x + 2, ly, x + pw - 3 - (ly * 7) % 6, ly), fill=(90, 90, 130))
        d.ellipse((x + pw // 2 - 1, y - 1, x + pw // 2 + 1, y + 1), fill=(43, 184, 201))
    d.rectangle((0, 0, w - 1, h - 1), outline=(100, 60, 30), width=2)
    return np.array(im)


def switch_panel(w, h, on):
    base = np.zeros((h, w, 3)) + np.array([120, 120, 128]) + _noise(h, w, 2, 16, 4)[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rectangle((1, 1, w - 2, h - 2), outline=(60, 60, 66))
    cx, cy = w // 2, h // 2
    d.rectangle((cx - w // 4, cy - h // 4, cx + w // 4, cy + h // 4), fill=(70, 70, 76), outline=(30, 30, 34))
    ly = cy - h // 6 if on else cy + h // 6
    d.line((cx, cy, cx, ly), fill=(20, 35, 48), width=max(2, w // 12))
    d.ellipse((cx - w // 10, ly - w // 10, cx + w // 10, ly + w // 10), fill=(43, 184, 201))
    lc = (95, 255, 170) if on else (255, 196, 78)
    d.ellipse((cx - 3, 3, cx + 3, 9), fill=lc)
    return np.array(im)


def science_wall(w, h, seed=1, glow=False):
    """A repeatable school-lab wall panel to replace hell/skull/fire art."""
    rnd = np.random.default_rng(seed)
    base = np.zeros((h, w, 3), float) + np.array([24, 48, 64]) + _noise(h, w, max(2, min(8, min(w,h)//5 or 2)), 12, seed)[..., None]
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # tile grid and metal seams
    step_x, step_y = max(8, w // 4), max(8, h // 4)
    for x in range(0, w, step_x):
        d.line((x, 0, x, h), fill=(10, 27, 39), width=1)
        d.line((x+1, 0, x+1, h), fill=(65, 104, 119), width=1)
    for y in range(0, h, step_y):
        d.line((0, y, w, y), fill=(10, 27, 39), width=1)
    # central inset panel
    mx, my = w//2, h//2
    pw, ph = max(6, int(w*.46)), max(6, int(h*.42))
    d.rounded_rectangle((mx-pw//2, my-ph//2, mx+pw//2, my+ph//2),
                        radius=max(1,min(4,w//16)), fill=(10, 31, 48), outline=(74, 153, 168), width=1)
    if glow:
        c=(77, 216, 219)
        d.ellipse((mx-pw//4, my-ph//4, mx+pw//4, my+ph//4), outline=c, width=max(1,w//24))
        d.line((mx-pw//3, my, mx+pw//3, my), fill=(255, 210, 120), width=1)
        d.line((mx, my-ph//3, mx, my+ph//3), fill=c, width=1)
    else:
        # chalk diagram / notebook lines
        for j in range(3):
            yy=my-ph//3+j*max(2,ph//5)
            d.line((mx-pw//3, yy, mx+pw//3, yy), fill=(146, 194, 198), width=1)
        d.ellipse((mx-2, my-2, mx+2, my+2), fill=(255, 216, 118))
    # corner bolts
    for x in (2, max(2,w-4)):
        for y in (2, max(2,h-4)):
            d.rectangle((x,y,x+1,y+1), fill=(228, 190, 104))
    return np.array(im)


def build_walls(wad, pal, log=print):
    n = 0
    for li, (name, data) in enumerate(wad.lumps):
        try:
            if name.startswith('BLOD'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = red_to_ink(rgb)
            elif name in ('SPINE3_1', 'SPINE3_2', 'SPINE4_1', 'SKULFACE', 'BODY_1', 'BODY_2', 'BRNOPEN',
                          'SKULWALL', 'SKULWAL3', 'SLADSKUL', 'SKSPINE1', 'SKSPINE2'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = corkboard(rgb.shape[1], rgb.shape[0], li)
                m[:] = True
            elif name.startswith('FIRE') or name.startswith('HELL') or name.startswith('SKIN'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = science_wall(rgb.shape[1], rgb.shape[0], li, glow=name.startswith('FIRE'))
                m[:] = True
            elif name in ('SW1SKULL', 'SW2SKULL'):
                rgb, m, lo, to = pic_rgb(pal, data)
                rgb = switch_panel(rgb.shape[1], rgb.shape[0], name.startswith('SW2'))
                m[:] = True
            else:
                continue
        except Exception as e:
            log('skip', name, e); continue
        wad.lumps[li][1] = encode_picture(pal.quantize(rgb), m, lo, to)
        n += 1
    fi, fj = wad.index('F_START'), wad.index('F_END')
    for li in range(fi + 1, fj):
        name = wad.lumps[li][0]
        if len(wad.lumps[li][1]) != 4096:
            continue
        if name.startswith('BLOOD'):
            rgb = pal.rgb[np.frombuffer(wad.lumps[li][1], np.uint8).reshape(64, 64)].astype(np.uint8)
            wad.lumps[li][1] = pal.quantize(red_to_ink(rgb)).tobytes()
            n += 1
        elif name.startswith(('LAVA', 'NUKAGE')):
            # Convert gore/hell liquids into abstract classroom paint and lab gel.
            y, x = np.mgrid[0:64, 0:64]
            wave = (np.sin(x * .35 + np.cos(y*.21)) + np.cos(y*.27+x*.08)) * .5
            if name.startswith('LAVA'):
                rgb = np.stack([25 + 18*wave, 98 + 35*wave, 132 + 38*wave], -1)
            else:
                rgb = np.stack([46 + 14*wave, 146 + 38*wave, 110 + 24*wave], -1)
            rgb = np.clip(rgb, 0, 255).astype(np.uint8)
            wad.lumps[li][1] = pal.quantize(rgb).tobytes()
            n += 1
    return n


# ---------------------------------------------------------------- school-themed first-person tools and HUD panels
def _atom_icon(d, cx, cy, rx, ry, color):
    d.ellipse((cx-rx, cy-ry, cx+rx, cy+ry), outline=color, width=2)
    d.ellipse((cx-ry, cy-rx, cx+ry, cy+rx), outline=color, width=2)
    d.ellipse((cx-2, cy-2, cx+2, cy+2), fill=(255, 226, 125), outline=(8, 30, 42))


def _weapon_art(prefix, variant=0):
    """Pixel-art school gadget in first-person view; no firearms or blades."""
    im = Image.new('RGBA', (96, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink=(7,18,29,255); metal=(57,79,92,255); hi=(131,165,171,255)
    navy=(19,49,72,255); cyan=(52,201,210,255); gold=(245,194,80,255)
    white=(234,242,232,255); glove=(205,166,119,255)

    def poly(pts, fill, outline=ink, width=2):
        d.polygon(pts, fill=fill)
        if outline: d.line(pts+[pts[0]], fill=outline, width=width, joint='curve')
    def hand(x):
        poly([(x,128),(x-5,117),(x-3,108),(x+2,100),(x+9,102),(x+14,112),(x+16,128)], glove)
        d.line((x+1,111,x+8,115,x+11,122), fill=(104,75,54,255), width=2)
        d.rectangle((x+3,118,x+11,121), fill=(27,95,122,255), outline=ink)
    def grip(box=(37,94,59,128)):
        d.rounded_rectangle(box, radius=5, fill=navy, outline=ink, width=3)
        d.line((box[0]+4,box[1]+5,box[2]-4,box[1]+5), fill=hi, width=2)
        d.rectangle((box[0]+5,box[1]+17,box[2]-5,box[1]+19), fill=gold)

    if prefix == 'PISG':                 # 연필 / 분필 발사기
        hand(14); hand(67)
        poly([(39,112),(43,35),(48,17),(53,35),(57,112)], metal)
        poly([(43,37),(48,19),(53,37),(51,93),(45,93)], navy, hi)
        d.rectangle((44,50,52,56), fill=cyan, outline=ink)
        d.rectangle((44,66,52,73), fill=gold, outline=ink)
        d.polygon([(43,19),(48,8),(53,19)], fill=(231,220,180,255), outline=ink)
        d.ellipse((44,12,52,20), fill=gold, outline=ink)
        d.text((44,95),'A+',font=F(FONT_HEAVY,7),fill=white)
        grip((37,94,59,128))
    elif prefix == 'SHTG':               # 이중 지우개 발사기
        hand(12); hand(68)
        d.rounded_rectangle((22,47,74,116),radius=8,fill=navy,outline=ink,width=3)
        for x in (32,60):
            d.rounded_rectangle((x-9,22,x+9,73),radius=5,fill=metal,outline=ink,width=3)
            d.rectangle((x-6,27,x+6,37),fill=hi,outline=ink)
            d.ellipse((x-6,17,x+6,29),fill=(220,236,225,255),outline=ink,width=2)
            d.ellipse((x-3,20,x+3,26),fill=(25,57,72,255))
        d.rectangle((28,81,68,91),fill=(224,229,217,255),outline=ink)
        grip((34,100,62,128))
    elif prefix == 'CHGG':               # 삼색 형광펜 연사기
        hand(16); hand(64)
        d.rounded_rectangle((23,56,73,116),radius=8,fill=navy,outline=ink,width=3)
        for x,col in zip((33,48,63),((245,220,65,255),cyan,(237,116,164,255))):
            d.rounded_rectangle((x-5,18,x+5,82),radius=4,fill=col,outline=ink,width=2)
            d.rectangle((x-3,22,x+3,34),fill=white,outline=ink)
            d.line((x,37,x,71),fill=(40,68,79,255),width=1)
        d.rectangle((29,91,67,98),fill=gold,outline=ink)
        grip((36,102,60,128))
    elif prefix == 'MISG':               # 종이비행기 발사기
        hand(14); hand(67)
        d.rounded_rectangle((29,49,67,119),radius=8,fill=navy,outline=ink,width=3)
        d.rectangle((36,62,60,92),fill=metal,outline=ink,width=2)
        d.line((39,68,57,86),fill=hi,width=2)
        poly([(48,14),(78,43),(51,36),(25,47)],(238,239,222,255),metal)
        d.line((48,14,49,36),fill=cyan,width=2)
        d.line((48,14,25,47),fill=(169,195,195,255),width=1)
        d.rectangle((41,96,57,102),fill=gold,outline=ink)
        grip((35,104,62,128))
    elif prefix == 'PLSG':               # 레이저 자 / 광학 장치
        hand(11); hand(69)
        d.rounded_rectangle((22,57,75,116),radius=7,fill=navy,outline=ink,width=3)
        d.rounded_rectangle((34,17,64,74),radius=6,fill=metal,outline=ink,width=3)
        d.rectangle((39,25,59,45),fill=(15,35,52,255),outline=hi)
        d.ellipse((42,28,56,42),fill=cyan,outline=white,width=2)
        d.line((49,43,49,10),fill=(133,245,247,255),width=2)
        d.line((28,85,69,85),fill=gold,width=3)
        for x in range(32,68,6): d.line((x,89,x,95),fill=white,width=1)
        grip((36,101,62,128))
    elif prefix == 'BFGG':               # 원자 모형 에너지 시연기
        hand(10); hand(70)
        d.rounded_rectangle((15,58,81,120),radius=12,fill=navy,outline=ink,width=4)
        d.rounded_rectangle((24,67,72,108),radius=8,fill=metal,outline=hi,width=2)
        d.ellipse((30,68,66,104),fill=(10,33,48,255),outline=gold,width=3)
        _atom_icon(d,48,86,14,6,cyan)
        d.ellipse((43,81,53,91),fill=white,outline=ink,width=1)
        d.rectangle((34,111,62,120),fill=gold,outline=ink)
    elif prefix == 'SAWG':               # 안전한 연필깎이 장치
        hand(10); hand(69)
        d.rounded_rectangle((16,63,82,119),radius=11,fill=navy,outline=ink,width=4)
        d.rounded_rectangle((27,43,69,84),radius=8,fill=metal,outline=ink,width=3)
        d.ellipse((34,49,62,77),fill=(16,36,51,255),outline=cyan,width=3)
        d.ellipse((41,56,55,70),fill=(218,231,213,255),outline=gold,width=2)
        poly([(7,47),(34,57),(35,64),(7,56)],(244,216,136,255))
        poly([(7,47),(2,45),(8,53)],(49,65,77,255))
        d.rectangle((27,92,71,100),fill=cyan,outline=ink)
        d.text((40,104),'연구',font=F(FONT_HEAVY,6),fill=white)
    elif prefix == 'PUNG':               # 보호 패딩 장갑
        poly([(20,128),(13,113),(12,96),(19,87),(25,92),(29,77),(38,75),(42,86),
              (48,71),(58,73),(61,87),(70,80),(79,88),(75,104),(66,118),(58,128)],glove)
        d.line((20,101,31,108,42,109),fill=(108,78,57,255),width=3)
        d.ellipse((39,91,58,108),fill=(25,92,122,255),outline=ink,width=2)
        d.text((43,96),'A+',font=F(FONT_HEAVY,7),fill=white)
        d.rectangle((24,116,63,127),fill=navy,outline=ink,width=2)
    else:
        return None
    if variant % 2: d.line((8,122,88,122),fill=(52,201,210,120),width=1)
    return im


def _flash_art(w, h, color_idx=0):
    im=Image.new('RGBA',(max(8,w),max(8,h)),(0,0,0,0)); d=ImageDraw.Draw(im)
    cols=[(99,242,240,245),(255,221,127,245),(190,224,255,245)]
    col=cols[color_idx%len(cols)]; cx,cy=im.width//2,im.height//2
    rx,ry=max(3,im.width*.43),max(3,im.height*.42); pts=[]
    for i in range(16):
        a=-math.pi/2+i*math.pi/8; r=1 if i%2==0 else .42
        pts.append((cx+math.cos(a)*rx*r,cy+math.sin(a)*ry*r))
    d.polygon(pts,fill=col,outline=(9,39,56,255))
    d.ellipse((cx-rx*.23,cy-ry*.23,cx+rx*.23,cy+ry*.23),fill=(245,250,229,255),outline=(27,98,126,255))
    return im


def build_weapon_sprites(wad, pal, log=print):
    prefixes={'PISG','PISF','PUNG','SHTG','SHTF','CHGG','CHGF','MISG','MISF','PLSG','PLSF','BFGG','BFGF','SAWG','CSAW'}
    count=0
    for li,(name,data) in enumerate(wad.lumps):
        pre=name[:4]
        if pre not in prefixes: continue
        try:
            idx,mask,left,top=decode_picture(data); h,w=idx.shape
            variant=ord(name[4]) if len(name)>4 else 0
            if pre in {'PISF','SHTF','CHGF','MISF','PLSF','BFGF'}:
                rgba=np.array(_flash_art(w,h,variant%3))
            elif pre=='CSAW':
                icon=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(icon)
                d.rounded_rectangle((2,2,w-3,h-3),radius=3,fill=(23,55,76,255),outline=(7,18,29,255),width=1)
                d.ellipse((w*.35,h*.18,w*.67,h*.82),fill=(58,188,199,255),outline=(234,242,232,255),width=1)
                d.line((3,h*.68,w-4,h*.68),fill=(245,194,80,255),width=1)
                rgba=np.array(icon)
            else:
                art=_weapon_art(pre,variant)
                if art is None: continue
                rgba=np.array(art.resize((w,h),Image.Resampling.NEAREST))
            wad.lumps[li][1]=picture_from_rgba(pal,rgba,left,top,alpha_thresh=80); count+=1
        except Exception as e:
            log('weapon sprite skip',name,e)
    log(f'school tools sprites replaced: {count}')
    return count


def statusbar_art(pal):
    im=Image.new('RGBA',(320,32),(10,25,38,255)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,319,31),fill=(12,30,44,255),outline=(74,165,180,255),width=1)
    d.line((0,3,319,3),fill=(143,218,218,255),width=1)
    for box in [(2,6,45,29),(48,6,91,29),(94,5,225,30),(228,6,272,29),(275,6,317,29)]:
        d.rounded_rectangle(box,radius=2,fill=(17,43,58,255),outline=(48,113,135,255),width=1)
    for x in (5,42,51,88,97,222,231,268,278,313):
        d.rectangle((x,7,x+1,8),fill=(245,203,105,255)); d.rectangle((x,27,x+1,28),fill=(70,160,171,255))
    d.line((8,11,39,11),fill=(64,174,183,255),width=1)
    d.line((51,11,88,11),fill=(64,174,183,255),width=1)
    d.line((232,11,268,11),fill=(64,174,183,255),width=1)
    d.line((279,11,312,11),fill=(64,174,183,255),width=1)
    d.rounded_rectangle((145,3,175,31),radius=3,fill=(8,22,34,255),outline=(211,177,94,255),width=2)
    d.line((102,29,141,29),fill=(55,125,144,255),width=1); d.line((179,29,218,29),fill=(55,125,144,255),width=1)
    d.ellipse((13,15,25,25),outline=(62,178,191,255),width=1); d.line((16,20,22,20),fill=(255,211,117,255),width=1)
    _atom_icon(d,298,20,7,3,(66,187,194,255))
    return picture_from_rgba(pal,np.array(im),0,0,alpha_thresh=100)


def statusbar_side_art(pal, name='STARMS', width=7, height=7):
    if name=='STARMS':
        im=Image.new('RGBA',(38,32),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.rounded_rectangle((1,1,36,30),radius=3,fill=(14,37,53,255),outline=(66,155,174,255),width=2)
        for x in (7,18,29): d.line((x,6,x,25),fill=(47,104,128,255),width=1)
        d.rectangle((5,26,32,28),fill=(238,190,89,255))
        return picture_from_rgba(pal,np.array(im),0,0,alpha_thresh=100)
    colors=[(64,168,220,255),(242,190,72,255),(222,116,115,255)]
    width=max(5,int(width)); height=max(5,int(height))
    im=Image.new('RGBA',(width,height),(0,0,0,0)); d=ImageDraw.Draw(im)
    i=int(name[-1]) if name[-1].isdigit() else 0; col=colors[i%3]
    d.polygon([(width//2,0),(width-1,max(1,height//3)),(width-2,height-2),
               (width//2,height-1),(1,height-2),(0,max(1,height//3))],
              fill=col,outline=(8,26,40,255))
    d.point((width//2,height//2),fill=(255,246,194,255))
    return picture_from_rgba(pal,np.array(im),0,0,alpha_thresh=100)



# ---------------------------------------------------------------- sounds
SR = 11025


def _t(d):
    return np.arange(int(SR * d)) / SR


def _env(n, a=0.005, r=0.1):
    e = np.ones(n); ai, ri = min(int(a * SR), n // 4), min(int(r * SR), n // 2)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e


def sweep(f0, f1, d, wave='sine', vib=0.0):
    t = _t(d); f = f0 * (f1 / f0) ** (t / d)
    if vib: f = f * (1 + vib * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave == 'square': s = np.sign(np.sin(ph)) * 0.6
    elif wave == 'saw': s = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif wave == 'tri': s = 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    else: s = np.sin(ph)
    return s * _env(len(t))


def noise(d, lp=0.5, seed=0):
    r = np.random.default_rng(seed).uniform(-1, 1, int(SR * d))
    out = np.zeros_like(r); acc = 0
    for i, v in enumerate(r):
        acc += lp * (v - acc); out[i] = acc
    return out / (np.abs(out).max() + 1e-9)


def cat(*xs):
    return np.concatenate(xs)


def mix(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o


def norm(x, g=0.9):
    return x / (np.abs(x).max() + 1e-9) * g


def sounds():
    s = {}
    faint = lambda f0, w, sd: norm(cat(sweep(f0, f0 * 0.3, 0.45, w, 0.04), mix(sweep(140, 90, 0.12, 'sine') * _env(int(0.12 * SR), 0.001, 0.1), noise(0.08, 0.3, sd) * 0.3)))
    s['DSPODTH1'] = faint(900, 'square', 1)
    s['DSPODTH2'] = faint(760, 'tri', 2)
    s['DSPODTH3'] = faint(1100, 'square', 3)
    bub = lambda sd: norm(cat(*[sweep(300 + 120 * k, 900 + 200 * k, 0.05, 'sine') for k in range(4)], sweep(700, 160, 0.35, 'tri')))
    s['DSBGDTH1'] = bub(1)
    s['DSBGDTH2'] = norm(cat(sweep(500, 1500, 0.08), sweep(1200, 200, 0.4, 'tri', 0.05)))
    s['DSSGTDTH'] = norm(mix(noise(0.6, 0.6, 5) * np.linspace(0.8, 0, int(0.6 * SR)) * 0.6, sweep(400, 80, 0.6, 'square', 0.08) * 0.6))
    s['DSCACDTH'] = norm(sweep(600, 120, 0.8, 'sine', 0.15))
    s['DSBRSDTH'] = norm(mix(noise(0.9, 0.08, 7) * np.linspace(1, 0, int(0.9 * SR)), sweep(110, 50, 0.9, 'sine') * 0.5))
    pd = lambda d: norm(mix(sweep(900, 40, d, 'saw', 0.03) * 0.7, noise(d, 0.15, 9) * np.linspace(0, 0.5, int(d * SR))))
    s['DSCYBDTH'] = pd(1.6)
    s['DSSPIDTH'] = pd(2.0)
    s['DSSKLDTH'] = norm(cat(*[sweep(f, f * 1.01, 0.06, 'tri') for f in (880, 1108, 1318, 1760)]))
    tromb = lambda base: norm(cat(*[sweep(base * r, base * r * 0.97, d, 'saw', 0.03 if d > 0.3 else 0) * 0.6 for r, d in [(1, 0.25), (0.94, 0.25), (0.89, 0.25), (0.84, 0.7)]]))
    s['DSPLDETH'] = tromb(392)
    s['DSPDIEHI'] = tromb(523)
    s['DSSLOP'] = norm(cat(noise(0.05, 0.9, 11), mix(noise(0.35, 0.95, 12) * np.exp(-_t(0.35) * 12), sweep(1500, 600, 0.2, 'tri') * 0.3)))
    return {k: dmx_sound(v) for k, v in s.items()}
