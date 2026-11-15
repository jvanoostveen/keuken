"""
Maakt naadloze tegeltexturen voor de variaties (draaien in Blender: numpy zit erin).
Tegelsoorten: zellige 10x10, visgraat 7,5x30 en effen 12,5x12,5 in een paar kleuren.
Per tegelsoort twee bestanden in textures/:
    <naam>_kleur.png   kleur (sRGB)
    <naam>_data.png    R = hoogte (bolling, randen), G = voeg (1 = voeg)
De textuur beslaat precies een geheel aantal herhalingen, dus hij sluit naadloos aan.
"""

import math
import bpy
import numpy as np

PX_PER_MM = 2
UIT = bpy.path.abspath("//textures/")


def periodiek_blur(a, r):
    """Box-blur met wrap-around (blijft naadloos)."""
    for ax in (0, 1):
        acc = np.zeros_like(a)
        for d in range(-r, r + 1):
            acc += np.roll(a, d, axis=ax)
        a = acc / (2 * r + 1)
    return a


def ruis(h, w, schaal_px, rng, lagen=3):
    """Zachte, naadloze ruis (0..1) met een paar octaven."""
    tot = np.zeros((h, w), np.float32)
    amp, s = 1.0, schaal_px
    for _ in range(lagen):
        r = max(1, int(s))
        n = rng.random((h, w)).astype(np.float32)
        n = periodiek_blur(periodiek_blur(n, r), r)
        n = (n - n.mean()) / (n.std() + 1e-6)
        tot += amp * n
        amp *= 0.5
        s /= 2.5
    return 0.5 + 0.18 * tot


def satureer(c, f):
    c = np.array(c, np.float32)
    l = c.mean()
    return np.clip(l + (c - l) * f, 0, 1)


def opslaan(naam, kleur, data):
    h, w = kleur.shape[:2]
    for achtervoegsel, arr, data_kanaal in (("kleur", kleur, False), ("data", data, True)):
        rgba = np.ones((h, w, 4), np.float32)
        rgba[..., :3] = arr
        im = bpy.data.images.new(f"tmp_{naam}_{achtervoegsel}", w, h)
        if data_kanaal:
            im.colorspace_settings.is_data = True
        im.pixels[:] = rgba[::-1].ravel()
        im.filepath_raw = UIT + f"{naam}_{achtervoegsel}.png"
        im.file_format = "PNG"
        im.save()
        bpy.data.images.remove(im)


# ------------------------------------------------------------------ zellige (vierkant)

def zellige(naam="tegel_zellige", maat=100, voeg=1.5, n=10, palet=None, voegkleur=(0.80, 0.79, 0.75), seed=3):
    """Handgemaakte vierkante tegels: per tegel een kleur uit het palet, glazuur dat aan de randen
    dikker/donkerder is, en een licht golvend oppervlak (de typische zellige-reflecties)."""
    rng = np.random.default_rng(seed)
    pitch = maat + voeg
    W = int(round(n * pitch * PX_PER_MM))
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32) / PX_PER_MM          # mm
    ix, iy = np.floor(xx / pitch).astype(int) % n, np.floor(yy / pitch).astype(int) % n
    fx, fy = xx - np.floor(xx / pitch) * pitch, yy - np.floor(yy / pitch) * pitch
    rand = np.minimum.reduce([fx, pitch - fx, fy, pitch - fy]) - voeg / 2  # mm tot de rand
    voeg_m = rand < 0

    kleuren = np.array([satureer(c, 1.45) for c in palet], np.float32)
    keuze = rng.integers(0, len(kleuren), (n, n))
    helder = rng.normal(1.0, 0.06, (n, n)).astype(np.float32)
    basis = kleuren[keuze[iy, ix]] * helder[iy, ix][..., None]

    vlek = ruis(W, W, 40 * PX_PER_MM, rng)
    fijn = ruis(W, W, 4 * PX_PER_MM, rng, lagen=2)
    randdonker = np.clip(1 - rand / 9.0, 0, 1) ** 2
    kleur = basis * (0.88 + 0.24 * vlek[..., None]) * (1 - 0.22 * randdonker[..., None]) * (0.97 + 0.06 * fijn[..., None])
    kleur[voeg_m] = voegkleur

    # hoogte: per tegel een kleine kanteling + golving, randen afgerond, voeg diep
    kant_x = rng.normal(0, 0.4, (n, n)).astype(np.float32)
    kant_y = rng.normal(0, 0.4, (n, n)).astype(np.float32)
    golf = ruis(W, W, 25 * PX_PER_MM, rng, lagen=2)
    hoogte = 0.55 + 0.25 * (golf - 0.5) + (kant_x[iy, ix] * (fx / pitch - 0.5) + kant_y[iy, ix] * (fy / pitch - 0.5)) * 0.25
    hoogte *= np.clip(rand / 3.0, 0, 1) ** 0.5
    hoogte[voeg_m] = 0.0
    data = np.stack([np.clip(hoogte, 0, 1), voeg_m.astype(np.float32), np.zeros_like(hoogte)], -1)
    opslaan(naam, np.clip(kleur, 0, 1), data)
    return n * pitch   # textuurmaat in mm


# ------------------------------------------------------------------ effen vierkant

def effen(naam, kleur, maat=125, voeg=2, n=8, voegkleur=(0.84, 0.84, 0.82), seed=7):
    """Effen vierkante wandtegel: één kleur, alleen een heel kleine variatie per tegel (baksel),
    glad glazuur met licht afgeronde randen."""
    rng = np.random.default_rng(seed)
    pitch = maat + voeg
    W = int(round(n * pitch * PX_PER_MM))
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32) / PX_PER_MM
    ix, iy = np.floor(xx / pitch).astype(int) % n, np.floor(yy / pitch).astype(int) % n
    fx, fy = xx - np.floor(xx / pitch) * pitch, yy - np.floor(yy / pitch) * pitch
    rand = np.minimum.reduce([fx, pitch - fx, fy, pitch - fy]) - voeg / 2
    voeg_m = rand < 0
    helder = rng.normal(1.0, 0.018, (n, n)).astype(np.float32)
    vlek = ruis(W, W, 60 * PX_PER_MM, rng, lagen=2)
    k = np.array(kleur, np.float32)[None, None] * helder[iy, ix][..., None] * (0.985 + 0.03 * vlek[..., None])
    k *= (1 - 0.06 * np.clip(1 - rand / 4.0, 0, 1)[..., None] ** 2)
    k[voeg_m] = voegkleur
    hoogte = (0.7 + 0.04 * (vlek - 0.5)) * np.clip(rand / 1.5, 0, 1) ** 0.5
    hoogte[voeg_m] = 0.0
    data = np.stack([hoogte, voeg_m.astype(np.float32), np.zeros_like(hoogte)], -1)
    opslaan(naam, np.clip(k, 0, 1), data)
    return n * pitch


EFFEN = {   # sRGB; mint gemeten op het moodboard (foto met de oranje ketel), iets verzadigd
    "mint": ((0.670, 0.780, 0.712), (0.84, 0.84, 0.82)),
    "zeegroen": ((0.498, 0.686, 0.659), (0.84, 0.84, 0.82)),
    "creme": ((0.902, 0.878, 0.824), (0.78, 0.77, 0.74)),
    "duifblauw": ((0.576, 0.663, 0.710), (0.84, 0.84, 0.82)),
    "olijf": ((0.557, 0.584, 0.478), (0.80, 0.79, 0.75)),
    "eucalyptus": ((0.561, 0.659, 0.620), (0.84, 0.84, 0.82)),   # grijs blauwgroen, als eucalyptusblad
}


# ------------------------------------------------------------------ visgraat

def visgraat(naam="tegel_visgraat", b=75, l=300, voeg=2, perioden=(3, 12), palet=None,
             voegkleur=(0.93, 0.92, 0.89), seed=5):
    """Klassieke visgraat (90 graden), 45 graden gedraaid zodat de 'V' rechtop staat.
    Stenen van 1 x k (in breedte-eenheden). Eén strook = trap van liggende en staande stenen langs (1,1);
    stroken herhalen met vector (k, -k). Na draaien zijn de perioden as-parallel: sqrt(2)*k*b breed, sqrt(2)*b hoog."""
    rng = np.random.default_rng(seed)
    k = l / b
    pu, pv = perioden
    Wmm, Hmm = math.sqrt(2) * k * b * pu, math.sqrt(2) * b * pv
    W, H = int(round(Wmm * PX_PER_MM)), int(round(Hmm * PX_PER_MM))
    vv, uu = np.mgrid[0:H, 0:W].astype(np.float64)
    uu, vv = uu / PX_PER_MM / b, vv / PX_PER_MM / b                          # in steenbreedtes
    s2 = math.sqrt(2)
    # terug naar het onverdraaide visgraatraster: (1,1)-richting wordt verticaal
    x = (vv / s2 * 1.0 + uu / s2)
    y = (vv / s2 - uu / s2)

    beste_rand = np.full(x.shape, -1.0)
    steen_id = np.zeros(x.shape, np.int64)
    s0 = np.floor((x - y) / (2 * k)).astype(np.int64)
    for ds in (-1, 0, 1):
        s = s0 + ds
        xs, ys = x - s * k, y + s * k
        # liggende steen t: [t, t+k] x [t, t+1]
        t = np.floor(ys)
        bin_h = (xs >= t) & (xs <= t + k)
        rand_h = np.minimum.reduce([xs - t, t + k - xs, ys - t, t + 1 - ys])
        # staande steen t: [t, t+1] x [t+1, t+1+k]
        t2 = np.floor(xs)
        bin_v = (ys >= t2 + 1) & (ys <= t2 + 1 + k)
        rand_v = np.minimum.reduce([xs - t2, t2 + 1 - xs, ys - t2 - 1, t2 + 1 + k - ys])
        for binnen, rand, tt, soort in ((bin_h, rand_h, t, 0), (bin_v, rand_v, t2, 1)):
            beter = binnen & (rand > beste_rand)
            beste_rand[beter] = rand[beter]
            # id periodiek in de textuur: strook mod pu, trede mod pv
            steen_id[beter] = ((s[beter] % pu) * 10000 + (tt[beter].astype(np.int64) % pv) * 2 + soort)
    rand_mm = beste_rand * b - voeg / 2
    voeg_m = rand_mm < 0

    ids, inv = np.unique(steen_id, return_inverse=True)
    inv = inv.reshape(steen_id.shape)
    kleuren = np.array([satureer(c, 1.3) for c in palet], np.float32)
    keuze = kleuren[rng.integers(0, len(kleuren), len(ids))] * rng.normal(1.0, 0.05, (len(ids), 1)).astype(np.float32)
    basis = keuze[inv]
    vlek = ruis(H, W, 30 * PX_PER_MM, rng)
    randdonker = np.clip(1 - rand_mm / 7.0, 0, 1) ** 2
    kleur = basis * (0.92 + 0.16 * vlek[..., None]) * (1 - 0.15 * randdonker[..., None])
    kleur[voeg_m] = voegkleur
    golf = ruis(H, W, 30 * PX_PER_MM, rng, lagen=2)
    hoogte = (0.6 + 0.2 * (golf - 0.5)) * np.clip(rand_mm / 2.5, 0, 1) ** 0.5
    hoogte[voeg_m] = 0.0
    data = np.stack([hoogte.astype(np.float32), voeg_m.astype(np.float32), np.zeros_like(hoogte, np.float32)], -1)
    opslaan(naam, np.clip(kleur, 0, 1).astype(np.float32), data)
    return Wmm, Hmm


ZELLIGE_ZEEGROEN = [   # gemeten in de zellige-foto's op het moodboard, aangevuld met zeegroen
    (0.648, 0.701, 0.718), (0.566, 0.630, 0.645), (0.468, 0.527, 0.544), (0.727, 0.769, 0.790),
    (0.540, 0.660, 0.620), (0.420, 0.560, 0.540), (0.600, 0.700, 0.680),
]
VISGRAAT_SALIE = [     # lichte saliegroene visgraat van het moodboard (Flexa-strip)
    (0.660, 0.750, 0.650), (0.620, 0.720, 0.620), (0.700, 0.780, 0.690), (0.640, 0.735, 0.660),
]

if __name__ == "__main__":
    print("zellige", zellige(palet=ZELLIGE_ZEEGROEN))
    print("visgraat", visgraat(palet=VISGRAAT_SALIE))
    for naam, (kleur, voegkleur) in EFFEN.items():
        print("effen", naam, effen("tegel_effen_" + naam, kleur, voegkleur=voegkleur))
