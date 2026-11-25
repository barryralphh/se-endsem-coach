import re, sys, os, glob, subprocess, asyncio, math, runpy, time
from PIL import Image, ImageDraw, ImageFont

NL = chr(10)
W, H = 1280, 720
FD = '/usr/share/fonts/truetype/dejavu/'
C = dict(bg=(15,23,42), bar=(2,6,23), panel=(30,41,59), paper=(255,250,235), ink=(25,25,40), white=(241,245,249), yel=(250,204,21), grn=(34,197,94), red=(239,68,68), blu=(56,189,248), org=(251,146,60), dim=(148,163,184))
PAL = [(37,99,235),(5,150,105),(217,119,6),(147,51,234),(220,38,38),(8,145,178)]
_fc = {}

def F(sz, b=False, m=False):
    k = (sz, b, m)
    if k not in _fc:
        n = ('DejaVuSansMono' if m else 'DejaVuSans') + ('-Bold' if b else '') + '.ttf'
        _fc[k] = ImageFont.truetype(FD + n, sz)
    return _fc[k]

def S(say, cap, left=None, right=None, title=None, full=False):
    return dict(say=say, cap=cap, left=left or [], right=right or [], title=title, full=full)

def wrap(text, font, maxw):
    out = []
    for para in text.split(NL):
        ind = len(para) - len(para.lstrip(' '))
        pre = ' ' * ind
        pw = font.getlength(pre)
        line = ''
        for w in para.strip().split(' '):
            t = (line + ' ' + w) if line else w
            if font.getlength(t) + pw <= maxw:
                line = t
            else:
                if line:
                    out.append(pre + line)
                line = w
                while len(line) > 1 and font.getlength(line) + pw > maxw:
                    k = len(line) - 1
                    while k > 1 and font.getlength(line[:k]) + pw > maxw:
                        k -= 1
                    out.append(pre + line[:k])
                    line = line[k:]
        out.append(pre + line)
    return out

def draw_plot(d, x, y, w, h, pts, opt):
    ox, oy = x + 46, y + h - 34
    pw, ph = w - 62, h - 52
    xmax = max(p[0] for p in pts)
    ymax = max([p[1] for p in pts] + [l[0] for l in opt.get('lines', [])]) * 1.1
    d.line([ox, oy, ox + pw, oy], fill=C['dim'], width=2)
    d.line([ox, oy, ox, oy - ph], fill=C['dim'], width=2)
    def P(px, py):
        return (ox + px / xmax * pw, oy - py / ymax * ph)
    for yv, lab in opt.get('lines', []):
        a = P(0, yv)
        xx = a[0]
        while xx < ox + pw:
            d.line([xx, a[1], min(xx + 8, ox + pw), a[1]], fill=C['org'], width=2)
            xx += 14
        d.text((ox + pw, a[1] - 18), lab, font=F(15), fill=C['org'], anchor='ra')
    d.line([P(*p) for p in pts], fill=C['grn'], width=3)
    for p in pts:
        q = P(*p)
        d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=C['yel'])
    d.text((ox + pw, oy + 8), opt.get('xl', 'x'), font=F(15), fill=C['dim'], anchor='ra')
    d.text((ox - 6, oy - ph), opt.get('yl', 'y'), font=F(15), fill=C['dim'], anchor='ra')
    for a in opt.get('marks', []):
        q = P(a[0], a[1])
        d.text((q[0] + 6, q[1] - 22), a[2], font=F(15, True), fill=C['red'])

def left_layout(d, items, x, y, w, sz):
    for it in items:
        k = it[0]
        if k == 'h':
            f = F(sz + 6, True)
            for ln in wrap(it[1], f, w):
                d.text((x, y), ln, font=f, fill=C['yel'])
                y += sz + 12
            y += 4
        elif k == 't':
            f = F(sz)
            for ln in wrap(it[1], f, w):
                d.text((x, y), ln, font=f, fill=C['white'])
                y += sz + 8
            y += 6
        elif k == 'b':
            f = F(sz)
            for p in it[1]:
                d.text((x, y), '\u2022', font=f, fill=C['org'])
                for ln in wrap(p, f, w - 28):
                    d.text((x + 28, y), ln, font=f, fill=C['white'])
                    y += sz + 7
                y += 3
            y += 4
        elif k == 'b2':
            cw = (w - 24) / 2
            f = F(sz)
            half = (len(it[1]) + 1) // 2
            ends = []
            for ci in range(2):
                yy = y
                for j, p in enumerate(it[1][ci * half:(ci + 1) * half]):
                    num = ci * half + j + 1
                    d.text((x + ci * (cw + 24), yy), str(num) + '.', font=F(sz, True), fill=C['org'])
                    for ln in wrap(p, f, cw - 40):
                        d.text((x + ci * (cw + 24) + 40, yy), ln, font=f, fill=C['white'])
                        yy += sz + 7
                    yy += 9
                ends.append(yy)
            y = max(ends)
        elif k == 'row':
            labs = it[1]
            n = len(labs)
            gap = 30 if n <= 4 else 14
            bw = (w - (n - 1) * gap) / n
            fs = min(sz, 22)
            while fs > 11 and any(F(fs, True).getlength(wd) > bw - 10 for l in labs for wd in l.split()):
                fs -= 1
            f = F(fs, True)
            ls = [wrap(l, f, bw - 10) for l in labs]
            mh = max(len(a) for a in ls) * (fs + 4) + 14
            for i, l in enumerate(ls):
                bx = x + i * (bw + gap)
                d.rounded_rectangle([bx, y, bx + bw, y + mh], 8, fill=PAL[i % 6])
                ty = y + 7
                for ln in l:
                    d.text((bx + bw / 2, ty), ln, font=f, fill=(255, 255, 255), anchor='ma')
                    ty += fs + 4
                if i < n - 1:
                    ax = bx + bw + 2
                    ay = y + mh / 2
                    d.line([ax, ay, ax + gap - 8, ay], fill=C['yel'], width=3)
                    d.polygon([(ax + gap - 8, ay - 6), (ax + gap - 8, ay + 6), (ax + gap, ay)], fill=C['yel'])
            y += mh + 14
        elif k == 'col':
            labs = it[1]
            fs = min(sz, 22)
            f = F(fs, True)
            bw = w * 0.86
            bx = x + (w - bw) / 2
            for i, l in enumerate(labs):
                ls = wrap(l, f, bw - 16)
                mh = len(ls) * (fs + 4) + 12
                d.rounded_rectangle([bx, y, bx + bw, y + mh], 8, fill=PAL[i % 6])
                ty = y + 6
                for ln in ls:
                    d.text((bx + bw / 2, ty), ln, font=f, fill=(255, 255, 255), anchor='ma')
                    ty += fs + 4
                y += mh
                if i < len(labs) - 1:
                    d.polygon([(x + w / 2 - 8, y + 2), (x + w / 2 + 8, y + 2), (x + w / 2, y + 16)], fill=C['yel'])
                    y += 18
            y += 12
        elif k == 'tbl':
            rows = it[1]
            nc = max(len(r) for r in rows)
            fs = max(12, sz - 5)
            f = F(fs)
            fb = F(fs, True)
            cw = [max(f.getlength(str(r[c])) if c < len(r) else 0 for r in rows) + 16 for c in range(nc)]
            tot = sum(cw)
            if tot > w:
                cw = [c * w / tot for c in cw]
            else:
                cw = [c + (w - tot) / nc for c in cw]
            for ri, r in enumerate(rows):
                ff = fb if ri == 0 else f
                cells = [wrap(str(r[c]) if c < len(r) else '', ff, cw[c] - 12) for c in range(nc)]
                rh = max(len(c) for c in cells) * (fs + 4) + 10
                cx = x
                for c in range(nc):
                    fill = (30, 64, 175) if ri == 0 else ((51, 65, 85) if ri % 2 else (71, 85, 105))
                    d.rectangle([cx, y, cx + cw[c], y + rh], fill=fill, outline=(15, 23, 42))
                    ty = y + 5
                    for ln in cells[c]:
                        d.text((cx + 6, ty), ln, font=ff, fill=C['white'])
                        ty += fs + 4
                    cx += cw[c]
                y += rh
            y += 12
        elif k == 'bits':
            s = it[1]
            labs = it[2] if len(it) > 2 else None
            n = len(s.replace(' ', ''))
            cs = min(46, int((w - 12) / (n + 0.5 * s.count(' '))))
            f = F(max(10, int(cs * 0.6)), True, True)
            cx = x
            i = 0
            for ch in s:
                if ch == ' ':
                    cx += cs * 0.5
                    continue
                d.rectangle([cx, y, cx + cs - 3, y + cs], fill=(51, 65, 85), outline=C['yel'])
                d.text((cx + (cs - 3) / 2, y + cs / 2), ch, font=f, fill=C['yel'], anchor='mm')
                if labs and i < len(labs):
                    d.text((cx + (cs - 3) / 2, y + cs + 4), labs[i], font=F(13), fill=C['dim'], anchor='ma')
                cx += cs
                i += 1
            y += cs + (22 if labs else 0) + 14
        elif k == 'graph':
            gh = it[3] if len(it) > 3 else 300
            draw_graph(d, x, y, w, gh, it[1], it[2])
            y += gh + 10
        elif k == 'mind':
            draw_mind(d, x, y, w, it[1], it[2])
            y += 310
        elif k == 'plot':
            draw_plot(d, x, y, w, 290, it[1], it[2] if len(it) > 2 else {})
            y += 300
    return y

def right_layout(d, lines, x, y, w, sz, spans=None):
    f = F(sz, False, True)
    fb = F(sz, True, True)
    lh = sz + 7
    for ln in lines:
        y0 = y
        if ln.startswith('## '):
            y += 4
            for t in wrap(ln[3:], fb, w):
                d.text((x, y), t, font=fb, fill=(185, 28, 28))
                y += lh
            d.line([x, y - 3, x + w, y - 3], fill=(185, 28, 28), width=2)
            y += 6
        elif ln.startswith('! '):
            ls = wrap(ln[2:], fb, w - 20)
            h = len(ls) * lh + 10
            d.rounded_rectangle([x - 4, y, x + w, y + h], 8, fill=(187, 247, 208), outline=(22, 101, 52), width=2)
            ty = y + 5
            for t in ls:
                d.text((x + 6, ty), t, font=fb, fill=(20, 83, 45))
                ty += lh
            y += h + 8
        elif ln.startswith('? '):
            for t in wrap(ln[2:], fb, w):
                d.text((x, y), t, font=fb, fill=(30, 64, 175))
                y += lh
            y += 2
        elif ln.startswith('~ '):
            for t in wrap(ln[2:], f, w):
                d.text((x, y), t, font=f, fill=(100, 100, 120))
                y += lh
        else:
            for t in wrap(ln, f, w):
                d.text((x, y), t, font=f, fill=C['ink'])
                y += lh
        if spans is not None:
            spans.append((y0, y))
    return y


def _bounds(sh, hw, hh, dx, dy):
    ax, ay = abs(dx) + 1e-9, abs(dy) + 1e-9
    if sh == 'd':
        t = 1 / (ax / hw + ay / hh)
    elif sh == 'o':
        t = 1 / ((ax / hw) ** 2 + (ay / hh) ** 2) ** 0.5
    else:
        t = min(hw / ax, hh / ay)
    return t

def draw_graph(d, x, y, w, h, nodes, edges):
    geo = {}
    for i, (k, v) in enumerate(nodes.items()):
        fx, fy, lab, sh = v[0], v[1], v[2], v[3]
        fs = 15
        f = F(fs, True)
        while f.getlength(lab) > 210 and fs > 11:
            fs -= 1
            f = F(fs, True)
        tw = f.getlength(lab)
        if sh == 'd':
            hw, hh = tw / 2 + 26, 25
        elif sh == 'o':
            hw, hh = tw / 2 + 18, 20
        else:
            hw, hh = tw / 2 + 12, 17
        cx = min(max(x + fx * w, x + hw + 4), x + w - hw - 4)
        cy = y + hh + 4 + fy * (h - 2 * hh - 8)
        geo[k] = (cx, cy, hw, hh, sh, lab, f, i)
    for e in edges:
        a, b = geo[e[0]], geo[e[1]]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ta, tb = _bounds(a[4], a[2], a[3], dx, dy), _bounds(b[4], b[2], b[3], dx, dy)
        p1 = (a[0] + dx * ta, a[1] + dy * ta)
        p2 = (b[0] - dx * tb, b[1] - dy * tb)
        d.line([p1, p2], fill=C['yel'], width=3)
        ln = (dx * dx + dy * dy) ** 0.5 + 1e-9
        ux, uy = (p2[0] - p1[0]) / ln, (p2[1] - p1[1]) / ln
        d.polygon([p2, (p2[0] - 13 * ux + 6 * uy, p2[1] - 13 * uy - 6 * ux), (p2[0] - 13 * ux - 6 * uy, p2[1] - 13 * uy + 6 * ux)], fill=C['yel'])
    for e in edges:
        if len(e) > 2 and e[2]:
            a, b = geo[e[0]], geo[e[1]]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            f = F(14, True)
            lw = f.getlength(e[2])
            d.rounded_rectangle([mx - lw / 2 - 4, my - 11, mx + lw / 2 + 4, my + 11], 6, fill=C['bg'])
            d.text((mx, my), e[2], font=f, fill=C['grn'], anchor='mm')
    for k, (cx, cy, hw, hh, sh, lab, f, i) in geo.items():
        col = (180, 83, 9) if sh == 'd' else ((4, 120, 87) if sh == 'o' else PAL[i % 6])
        if sh == 'd':
            d.polygon([(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)], fill=col, outline=C['yel'])
        elif sh == 'o':
            d.ellipse([cx - hw, cy - hh, cx + hw, cy + hh], fill=col, outline=C['yel'], width=2)
        else:
            d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], 8, fill=col, outline=(255, 255, 255), width=1)
        d.text((cx, cy), lab, font=f, fill=(255, 255, 255), anchor='mm')

def draw_mind(d, x, y, w, center, spokes, h=300):
    import math as _m
    cx, cy = x + w / 2, y + h / 2
    n = len(spokes)
    pos = []
    for i, s in enumerate(spokes):
        ang = -_m.pi / 2 + 2 * _m.pi * i / n
        px, py = cx + _m.cos(ang) * (w / 2 - 150), cy + _m.sin(ang) * (h / 2 - 28)
        pos.append((px, py, s))
        d.line([cx, cy, px, py], fill=C['dim'], width=3)
    f = F(20, True)
    cw = f.getlength(center) / 2 + 20
    d.ellipse([cx - cw, cy - 30, cx + cw, cy + 30], fill=(180, 83, 9), outline=C['yel'], width=3)
    d.text((cx, cy), center, font=f, fill=(255, 255, 255), anchor='mm')
    for i, (px, py, s) in enumerate(pos):
        fs = 15
        fb = F(fs, True)
        while fb.getlength(s) > 270 and fs > 11:
            fs -= 1
            fb = F(fs, True)
        hw = fb.getlength(s) / 2 + 12
        d.rounded_rectangle([px - hw, py - 18, px + hw, py + 18], 10, fill=PAL[i % 6])
        d.text((px, py), s, font=fb, fill=(255, 255, 255), anchor='mm')

_scr = Image.new('RGB', (W, H))

def fit(fn, maxh, sizes):
    d = ImageDraw.Draw(_scr)
    for sz in sizes:
        if fn(d, sz) <= maxh:
            return sz
    return sizes[-1]

def bird(d, cx, cy, r, mouth):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 38, 38), outline=(120, 20, 20), width=4)
    d.ellipse([cx - r * 0.6, cy + r * 0.05, cx + r * 0.6, cy + r * 0.95], fill=(253, 224, 200))
    d.polygon([(cx - 10, cy - r), (cx, cy - r - 26), (cx + 10, cy - r)], fill=(150, 20, 20))
    d.polygon([(cx + 8, cy - r + 2), (cx + 22, cy - r - 22), (cx + 26, cy - r + 6)], fill=(150, 20, 20))
    for ex in (-0.3, 0.3):
        ecx = cx + ex * r
        ecy = cy - 0.2 * r
        d.ellipse([ecx - r * 0.2, ecy - r * 0.2, ecx + r * 0.2, ecy + r * 0.2], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        d.ellipse([ecx + r * 0.02, ecy - r * 0.06, ecx + r * 0.12, ecy + r * 0.06], fill=(0, 0, 0))
    d.line([(cx - 0.55 * r, cy - 0.62 * r), (cx - 0.08 * r, cy - 0.36 * r)], fill=(20, 0, 0), width=7)
    d.line([(cx + 0.55 * r, cy - 0.62 * r), (cx + 0.08 * r, cy - 0.36 * r)], fill=(20, 0, 0), width=7)
    by = cy + 0.08 * r
    d.polygon([(cx, by - 0.1 * r), (cx + 0.62 * r, by + 0.05 * r), (cx, by + 0.18 * r)], fill=(250, 204, 21), outline=(120, 80, 0))
    if mouth:
        d.polygon([(cx + 0.02 * r, by + 0.2 * r), (cx + 0.5 * r, by + 0.28 * r), (cx + 0.02 * r, by + 0.42 * r)], fill=(234, 179, 8), outline=(120, 80, 0))

def frame(sc, idx, total, ltitle, nl, nr, lsz, rsz, mouth, full, has_r):
    im = Image.new('RGB', (W, H), C['bg'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=C['bar'])
    d.text((24, 14), sc.get('title') or ltitle, font=F(30, True), fill=C['yel'])
    d.text((W - 24, 22), 'Gussa Guru SE Dojo  |  %d/%d' % (idx, total), font=F(20), fill=C['dim'], anchor='ra')
    bottom = 700 if full else 530
    lx1 = 632 if has_r else W - 24
    d.rounded_rectangle([16, 76, lx1 + 8, bottom], 14, fill=C['panel'])
    left_layout(d, sc['left'][:nl], 36, 90, lx1 - 36 - 12, lsz)
    if has_r:
        d.rounded_rectangle([648, 76, W - 16, bottom], 14, fill=C['paper'])
        d.text((664, 82), 'CALCULATION / WORKING', font=F(16, True), fill=(120, 53, 15))
        right_layout(d, sc['right'][:nr], 664, 108, 584, rsz)
    if not full:
        by = 618 + (-4 if mouth else 0)
        bird(d, 84, by, 58, mouth)
        d.polygon([(142, 600), (166, 584), (166, 620)], fill=(255, 255, 255))
        d.rounded_rectangle([160, 548, W - 16, 704], 18, fill=(255, 255, 255))
        cf = F(26, True)
        cap = wrap(sc['cap'], cf, W - 16 - 160 - 36)[:3]
        ty = 626 - len(cap) * 17
        for ln in cap:
            d.text((180, ty), ln, font=cf, fill=(30, 30, 50))
            ty += 34
    return im


CONN = ['Pehle', 'Ab agla step', 'Phir', 'Iske baad', 'Ab dekho', 'Chalo aage']

def words(t):
    t = t.replace('0x', 'hex ')
    t = re.sub(r'\d+\.\d+\.\d+\.\d+', lambda m: m.group(0).replace('.', ' dot '), t)
    t = re.sub(r'(?<=\d)\.(?=\d)', ' point ', t)
    t = t.replace('->', ' matlab ').replace('=>', ' matlab ').replace('\u2192', ' matlab ')
    t = t.replace('\u00d7', ' into ').replace('\u00f7', ' divided by ')
    t = re.sub(r'(?<=[\d)])\s*[x*]\s*(?=[\d(])', ' into ', t)
    t = re.sub(r'\s[x*]\s', ' into ', t)
    t = re.sub(r'(?<=[\w)])\s*/\s*(?=[\w(])', ' divided by ', t)
    t = re.sub(r'(?<![\w)])/(?=\d)', ' slash ', t)
    t = t.replace('^', ' power ').replace('=', ' barabar ').replace('+', ' plus ')
    t = re.sub(r'\s-\s', ' minus ', t)
    t = t.replace('%', ' percent').replace('(', ' ').replace(')', ' ')
    t = re.sub(r'\b(?=[0-9A-F]*\d)(?=[0-9A-F]*[A-F])[0-9A-F]{2,}\b', lambda m: ' '.join(m.group(0)), t)
    return re.sub(r'\s+', ' ', t).strip()

def spoken(ln, g):
    if ln.startswith('## '):
        return 'Ab dekhte hain, ' + words(ln[3:]) + '.'
    if ln.startswith('! '):
        return 'Yeh hamara answer hai. ' + words(ln[2:]) + '. Isko box kar do.'
    if ln.startswith('? '):
        return 'Sawal yeh hai. ' + words(ln[2:]) + '.'
    if ln.startswith('~ '):
        return 'Dhyan rakho. ' + words(ln[2:]) + '.'
    return CONN[g % len(CONN)] + '. ' + words(ln) + '.'

def calc_frame(lines, vis_to, a, b, idx, total, ltitle, rsz, mouth, cap, gi, gn):
    im = Image.new('RGB', (W, H), C['bg'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=C['bar'])
    d.text((24, 14), ltitle + '  |  CALCULATION', font=F(30, True), fill=C['yel'])
    d.text((W - 24, 22), 'Gussa Guru SE Dojo  |  %d/%d' % (idx, total), font=F(20), fill=C['dim'], anchor='ra')
    d.rounded_rectangle([16, 76, W - 16, 530], 14, fill=C['paper'])
    d.text((36, 84), 'CALCULATION / WORKING   step %d of %d' % (gi, gn), font=F(16, True), fill=(120, 53, 15))
    vis = lines[:vis_to + 1]
    sp = []
    right_layout(ImageDraw.Draw(_scr), vis, 36, 112, 1176, rsz, sp)
    d.rounded_rectangle([28, sp[a][0] - 3, W - 28, sp[b][1] + 3], 8, fill=(254, 240, 138), outline=(202, 138, 4), width=2)
    right_layout(d, vis, 36, 112, 1176, rsz)
    by = 618 + (-4 if mouth else 0)
    bird(d, 84, by, 58, mouth)
    d.polygon([(142, 600), (166, 584), (166, 620)], fill=(255, 255, 255))
    d.rounded_rectangle([160, 548, W - 16, 704], 18, fill=(255, 255, 255))
    cf = F(26, True)
    cp = wrap(cap, cf, W - 16 - 160 - 36)[:3]
    ty = 626 - len(cp) * 17
    for ln in cp:
        d.text((180, ty), ln, font=cf, fill=(30, 30, 50))
        ty += 34
    return im

def probe(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return float(r.stdout.strip())

async def _edge(text, out):
    import edge_tts
    await edge_tts.Communicate(text, 'en-IN-PrabhatNeural', rate='-6%').save(out)

def tts(text, wav, mode):
    mp3 = wav[:-4] + '.mp3'
    ok = False
    if mode != 'none':
        for a in range(6):
            try:
                asyncio.run(_edge(text, mp3))
                ok = os.path.getsize(mp3) > 1000
                if ok:
                    break
            except Exception as e:
                print('tts retry', a, e)
                time.sleep(2 + 3 * a)
    if ok:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-ar', '24000', '-ac', '1', '-af', 'apad=pad_dur=0.6', wav], check=True)
        return
    if mode != 'none':
        print('FALLBACK espeak')
        tmp = wav[:-4] + '_e.wav'
        subprocess.run(['espeak-ng', '-v', 'en-in', '-s', '150', '-w', tmp, text])
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-ar', '24000', '-ac', '1', '-af', 'apad=pad_dur=0.6', wav], check=True)
        return
    secs = max(3.0, len(text.split()) / 2.4)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', str(secs), wav], check=True)

def load(n):
    path = glob.glob('lessons/L%s_*.py' % n)[0]
    L = runpy.run_path(path, init_globals={'S': S})['L']
    scenes = list(L['scenes'])
    pts = L['points']
    say = 'Ab final recap. Yeh dus points bas rat lo. ' + ' '.join('Point %d. %s.' % (i + 1, p) for i, p in enumerate(pts)) + ' Bas, ab tum is topic ke boss ho. Gussa mat karna, bas practice karna. Milte hain agle video mein!'
    scenes.append(dict(say=say, cap='10 golden points: yaad kar lo!', left=[['b2', pts]], right=[], title='10 Golden Points', full=True))
    return L, scenes

def sizes_for(sc):
    full = sc.get('full', False)
    has_r = bool(sc['right']) and not full
    lw = (632 - 36 - 12) if has_r else (W - 24 - 36 - 12)
    bottom = 700 if full else 530
    lsz = fit(lambda d, sz: left_layout(d, sc['left'], 0, 0, lw, sz), bottom - 90 - 16, (28, 26, 24, 22, 20, 18, 17, 16, 15, 14))
    rsz = fit(lambda d, sz: right_layout(d, sc['right'], 0, 0, 584, sz), bottom - 108 - 16, (24, 22, 20, 18, 17, 16, 15, 14))
    return full, has_r, lsz, rsz

def preview(n):
    L, scenes = load(n)
    os.makedirs('out/prev', exist_ok=True)
    for i, sc in enumerate(scenes, 1):
        full, has_r, lsz, rsz = sizes_for(sc)
        frame(sc, i, len(scenes), L['title'], len(sc['left']), len(sc['right']), lsz, rsz, 1, full, has_r).save('out/prev/%s_%02d.png' % (n, i))
    print('preview done', len(scenes))

def build(n, mode, part=0, parts=1):
    L, scenes = load(n)
    sfx = ('_p%d' % part) if part else ''
    lo, hi = 0, len(scenes)
    if part:
        sz = -(-len(scenes) // parts)
        lo, hi = (part - 1) * sz, min(len(scenes), part * sz)
        if lo >= hi:
            print('empty part, nothing to do')
            return
    work = 'work/' + n + sfx
    os.makedirs(work, exist_ok=True)
    os.makedirs('out', exist_ok=True)
    entries = []
    wavs = []
    total = len(scenes)
    cnt = [0]

    def newwav(say):
        cnt[0] += 1
        wav = '%s/a%03d.wav' % (work, cnt[0])
        tts(say, wav, mode)
        wavs.append(wav)
        return wav, probe(wav)

    def hold(imgs, sd):
        t = 0.0
        j = 0
        while t < sd - 1e-6:
            c = min(0.5, sd - t)
            entries.append((imgs[j % len(imgs)], c))
            t += c
            j += 1

    def emit_plain(sc, i, say):
        wav, D = newwav(say)
        full, has_r, lsz, rsz = sizes_for(sc)
        left, right = sc['left'], sc['right']
        steps = max(len(left), len(right), 1)
        for s in range(steps):
            nl = math.ceil((s + 1) * len(left) / steps)
            nr = math.ceil((s + 1) * len(right) / steps)
            imgs = []
            for mouth in ((0, 1) if not full else (0,)):
                p = '%s/f%03d_%02d_%d.png' % (work, cnt[0], s, mouth)
                frame(sc, i, total, L['title'], nl, nr, lsz, rsz, mouth, full, has_r).save(p)
                imgs.append(p)
            hold(imgs, D / steps)

    def emit_calc(sc, i):
        lines = sc['right']
        groups = []
        j = 0
        while j < len(lines):
            if lines[j].startswith('## ') and j + 1 < len(lines) and not lines[j + 1].startswith('## '):
                groups.append((j, j + 1))
                j += 2
            else:
                groups.append((j, j))
                j += 1
        rsz = fit(lambda d, sz: right_layout(d, lines, 0, 0, 1176, sz), 396, (30, 28, 26, 24, 22, 20, 18, 16, 14))
        for g, (a, b) in enumerate(groups):
            say = ' '.join(spoken(lines[t], g) for t in range(a, b + 1))
            if g == 0:
                say = 'Ab calculation karte hain, dhyan se dekho. ' + say
            wav, D = newwav(say)
            cap = ' '.join(re.sub(r'^(##|[!?~]) ', '', lines[t]) for t in range(a, b + 1))
            imgs = []
            for mouth in (0, 1):
                p = '%s/c%03d_%d.png' % (work, cnt[0], mouth)
                calc_frame(lines, b, a, b, i, total, L['title'], rsz, mouth, cap, g + 1, len(groups)).save(p)
                imgs.append(p)
            hold(imgs, D)

    for i, sc in enumerate(scenes, 1):
        if not (lo < i <= hi):
            continue
        if sc['right'] and not sc.get('full'):
            if sc['left']:
                emit_plain(dict(sc, right=[]), i, sc['say'])
            emit_calc(sc, i)
        else:
            emit_plain(sc, i, sc['say'])
        print('scene', i, 'of', total)
    with open(work + '/frames.txt', 'w') as fh:
        for p, c in entries:
            fh.write('file ' + chr(39) + os.path.abspath(p) + chr(39) + NL + 'duration %.3f' % c + NL)
        fh.write('file ' + chr(39) + os.path.abspath(entries[-1][0]) + chr(39) + NL)
    with open(work + '/wavs.txt', 'w') as fh:
        for w in wavs:
            fh.write('file ' + chr(39) + os.path.abspath(w) + chr(39) + NL)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', work + '/wavs.txt', '-c', 'copy', work + '/all.wav'], check=True)
    out = 'out/%s%s.mp4' % (n, sfx)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', work + '/frames.txt', '-i', work + '/all.wav', '-vf', 'fps=10,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '64k', '-shortest', out], check=True)
    with open('out/%s%s.md' % (n, sfx), 'w') as fh:
        fh.write('# ' + L['title'] + NL + NL + '## 10 Golden Points' + NL)
        for i, p in enumerate(L['points'], 1):
            fh.write('%d. %s' % (i, p) + NL)
        fh.write(NL + '## Worked calculations' + NL)
        for i, sc in enumerate(L['scenes'], 1):
            if sc['right']:
                fh.write(NL + '### Scene %d: %s' % (i, sc['cap']) + NL)
                for r in sc['right']:
                    fh.write('    ' + r + NL)
    print('built', out, round(sum(c for _, c in entries)), 'sec')

if __name__ == '__main__':
    a = sys.argv[1:]
    mode = 'edge'
    if '--notts' in a:
        mode = 'none'
        a.remove('--notts')
    part, parts = 0, 1
    if '--part' in a:
        i = a.index('--part'); part = int(a[i + 1]); del a[i:i + 2]
    if '--parts' in a:
        i = a.index('--parts'); parts = int(a[i + 1]); del a[i:i + 2]
    if a[0] == 'preview':
        preview(a[1])
    else:
        build(a[1], mode, part, parts)
