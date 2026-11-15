"""
Maakt naadloze wandtegeltexturen uit productfoto's van echte tegels (tegels/kandidaten/).

Per foto worden de losse tegels uit het tegelveld geknipt (de voegen worden opgezocht), daarna
wordt een veld van N x N tegels opnieuw gelegd met willekeurige keuze en draaiing per tegel,
zodat de kleurvariatie van de echte tegel terugkomt zonder herhalend patroon.
Uitvoer in textures/: <naam>_kleur.png en <naam>_data.png (R = hoogte, G = voeg), zoals tegeltexturen.py.

Draaien in Blender (numpy zit erin): Scripting > Run Script.
"""

import bpy
import numpy as np

PX_PER_MM = 2
N = 8   # tegels per richting in de textuur

TEGELS = {
    # naam: foto, kolommen, rijen, welke cellen gebruiken (None = alle), tegelmaat mm, voeg mm, voegkleur
    "tegel_echt_steenbok": dict(foto="//tegels/kandidaten/Steenbok_Rustic_GlossyOliveGreen.jpg", cols=3, rows=3,
                                cellen=[(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)],   # bovenste rij heeft glansplekken
                                maat=130, voeg=2, voegkleur=(0.83, 0.82, 0.79)),
    "tegel_echt_hanoi": dict(foto="//tegels/kandidaten/Equipe_Hanoi_WildOlive.png", cols=4, rows=3, cellen=None,
                             maat=100, voeg=2, voegkleur=(0.86, 0.85, 0.82)),
    "tegel_echt_marazzi": dict(foto="//tegels/kandidaten/Marazzi_Zellige_Salvia.jpg", cols=3, rows=3, cellen=None,
                               maat=100, voeg=2, voegkleur=(0.74, 0.73, 0.70)),
}


def laad(pad):
    im = bpy.data.images.load(bpy.path.abspath(pad))
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1].copy()   # rij 0 = boven
    bpy.data.images.remove(im)
    return a


def tegelvlak(a):
    """Begrenzing van het tegelveld: alles wat niet (bijna) wit/transparant is."""
    lum = a[..., :3].mean(-1)
    vol = (a[..., 3] > 0.5) & (lum < 0.93)
    rijen, kols = np.where(vol.mean(1) > 0.3)[0], np.where(vol.mean(0) > 0.3)[0]
    return rijen[0], rijen[-1] + 1, kols[0], kols[-1] + 1


def voegen(profiel, n):
    """Zoek n-1 voegen (lichte lijnen) in een helderheidsprofiel, elk rond de verwachte positie."""
    L = len(profiel)
    sm = np.convolve(profiel, np.ones(5) / 5, mode="same")
    pos = []
    for k in range(1, n):
        c = int(L * k / n)
        r = max(3, L // (4 * n))
        pos.append(c - r + int(np.argmax(sm[c - r:c + r])))
    return [0] + pos + [L]


def knip(cfg):
    a = laad(cfg["foto"])
    y0, y1, x0, x1 = tegelvlak(a)
    a = a[y0:y1, x0:x1]
    lum = a[..., :3].mean(-1)
    ys = voegen(lum.mean(1), cfg["rows"])
    xs = voegen(lum.mean(0), cfg["cols"])
    t = int(cfg["maat"] * PX_PER_MM)
    stukken = []
    for r in range(cfg["rows"]):
        for c in range(cfg["cols"]):
            if cfg["cellen"] and (r, c) not in cfg["cellen"]:
                continue
            ya, yb, xa, xb = ys[r], ys[r + 1], xs[c], xs[c + 1]
            m = int(0.035 * (yb - ya))                          # voeg en rand eraf
            cel = a[ya + m:yb - m, xa + m:xb - m, :3]
            yi = np.linspace(0, cel.shape[0] - 1, t).astype(int)
            xi = np.linspace(0, cel.shape[1] - 1, t).astype(int)
            stukken.append(cel[yi][:, xi])
    return stukken


def blur(a, r):
    for ax in (0, 1):
        acc = np.zeros_like(a)
        for d in range(-r, r + 1):
            acc += np.roll(a, d, axis=ax)
        a = acc / (2 * r + 1)
    return a


def leg(naam, cfg, seed=4):
    rng = np.random.default_rng(seed)
    stukken = knip(cfg)
    t = stukken[0].shape[0]
    g = max(1, int(round(cfg["voeg"] * PX_PER_MM)))
    p = t + g
    W = N * p
    kleur = np.empty((W, W, 3), np.float32)
    kleur[:] = cfg["voegkleur"]
    hoogte = np.zeros((W, W), np.float32)
    # randprofiel van een tegel: afgeronde rand (1,5 mm) + lichte bolling
    yy, xx = np.mgrid[0:t, 0:t].astype(np.float32)
    rand = np.minimum.reduce([xx, t - 1 - xx, yy, t - 1 - yy]) / PX_PER_MM
    profiel = np.clip(rand / 1.5, 0, 1) ** 0.5
    vorige = -1
    for r in range(N):
        for c in range(N):
            k = rng.integers(len(stukken))
            if k == vorige and len(stukken) > 1:
                k = (k + 1) % len(stukken)
            vorige = k
            s = np.rot90(stukken[k], rng.integers(4))
            if rng.random() < 0.5:
                s = s[:, ::-1]
            y, x = r * p + g // 2, c * p + g // 2
            kleur[y:y + t, x:x + t] = s
            l = s.mean(-1)
            golf = blur(l - l.mean(), 6)                       # golving van het glazuur uit de foto
            hoogte[y:y + t, x:x + t] = profiel * (0.7 + 0.6 * golf)
    voeg = (hoogte <= 0).astype(np.float32)
    data = np.stack([np.clip(hoogte, 0, 1), voeg, np.zeros_like(voeg)], -1)
    for achter, arr, is_data in (("kleur", kleur, False), ("data", data, True)):
        rgba = np.ones((W, W, 4), np.float32)
        rgba[..., :3] = np.clip(arr, 0, 1)
        im = bpy.data.images.new(f"tmp_{naam}_{achter}", W, W)
        if is_data:
            im.colorspace_settings.is_data = True
        im.pixels[:] = rgba[::-1].ravel()
        im.filepath_raw = bpy.path.abspath(f"//textures/{naam}_{achter}.png")
        im.file_format = "PNG"
        im.save()
        bpy.data.images.remove(im)
    return N * (cfg["maat"] + cfg["voeg"]), len(stukken)


if __name__ == "__main__":
    for naam, cfg in TEGELS.items():
        print(naam, leg(naam, cfg))
