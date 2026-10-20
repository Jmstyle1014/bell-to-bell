# Draws the Bell to Bell app icons (a ring bell on the dark arena colour) without any image libraries.
# Run: python make_icons.py  -> icon-192.png, icon-512.png, icon-maskable-512.png
import struct, zlib, os

BG = (12, 14, 19)
BELL = (255, 90, 54)
GOLD = (242, 182, 50)
HERE = os.path.dirname(os.path.abspath(__file__))


def shape(u, v):
    """Colour of the bell drawing at normalised point (u, v), or None for background."""
    if (u - .5) ** 2 + (v - .75) ** 2 < .055 ** 2:
        return GOLD                                        # clapper
    if .25 <= u <= .75 and .63 <= v <= .70:
        return GOLD                                        # rim
    if (u - .5) ** 2 + (v - .14) ** 2 < .045 ** 2 or (abs(u - .5) < .02 and .14 <= v <= .2):
        return GOLD                                        # hanging knob
    if (u - .5) ** 2 + (v - .34) ** 2 < .16 ** 2 and v <= .34:
        return BELL                                        # dome
    if .34 <= v <= .64:
        t = (v - .34) / .30
        if abs(u - .5) < .16 + .08 * t ** 1.8:
            return BELL                                    # flared body
    return None


def render(size, scale):
    ss = 3
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            acc = [0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    u = ((x + (sx + .5) / ss) / size - .5) / scale + .5
                    v = ((y + (sy + .5) / ss) / size - .5) / scale + .5 + .03
                    c = shape(u, v) or BG
                    for i in range(3):
                        acc[i] += c[i]
            row += bytes(a // (ss * ss) for a in acc)
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


for name, size, scale in [('icon-192.png', 192, 1.0), ('icon-512.png', 512, 1.0), ('icon-maskable-512.png', 512, .72)]:
    with open(os.path.join(HERE, name), 'wb') as f:
        f.write(render(size, scale))
    print('wrote', name)
