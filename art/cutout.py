# Removes the flat dark background from fighter art (flood fill from the edges) and writes an RGBA PNG.
# Run: python cutout.py boxer-blue-src.png boxer-blue.png
import struct, zlib, sys
from collections import deque


def read_png(path):
    d = open(path, 'rb').read()
    pos, idat = 8, b''
    while pos < len(d):
        n, = struct.unpack('>I', d[pos:pos + 4]); kind = d[pos + 4:pos + 8]; body = d[pos + 8:pos + 8 + n]
        if kind == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', body[:10])
            assert bd == 8 and ct in (2, 6), 'expects 8-bit RGB or RGBA'
        if kind == b'IDAT':
            idat += body
        pos += 12 + n
    bpp = 3 if ct == 2 else 4
    raw = zlib.decompress(idat); stride = w * bpp; rows = []; prev = bytearray(stride); i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([list(line[x * bpp:x * bpp + 3]) for x in range(w)]); prev = line
    return w, h, rows


def write_rgba(path, w, h, rows, alpha):
    raw = b''.join(b'\0' + bytes(v for x in range(w) for v in (*rows[y][x], alpha[y][x])) for y in range(h))
    ch = lambda k, b: struct.pack('>I', len(b)) + k + b + struct.pack('>I', zlib.crc32(k + b) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
                           + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))


w, h, px = read_png(sys.argv[1])
bg = px[2][2]
dist = lambda p: sum(abs(p[i] - bg[i]) for i in range(3))
alpha = [[255] * w for _ in range(h)]
q = deque((x, y) for x in range(w) for y in (0, h - 1)); q.extend((x, y) for y in range(h) for x in (0, w - 1))
while q:
    x, y = q.popleft()
    if alpha[y][x] == 0 or dist(px[y][x]) > 24:
        continue
    alpha[y][x] = 0
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < w and 0 <= ny < h and alpha[ny][nx]:
            q.append((nx, ny))
# soften the one-pixel fringe that still carries background colour
for y in range(1, h - 1):
    for x in range(1, w - 1):
        if alpha[y][x] and dist(px[y][x]) < 45 and not all(alpha[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            alpha[y][x] = 120
write_rgba(sys.argv[2], w, h, px, alpha)
print('transparent pixels:', sum(r.count(0) for r in alpha), 'of', w * h)
