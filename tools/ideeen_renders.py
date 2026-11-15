"""
Renders voor het gespreksdocument (ideeen/ -> Keuken ideeën.pdf).

In de open Blender (via MCP of Scripting):
    ns = {"__name__": "ideeen"}; exec(open("tools/ideeen_renders.py").read(), ns)
    ns["render"]()                         # alles, naar renders/ideeen/
    ns["render"](["raam"], proef=True, map_="/tmp/proef")   # snel proefbeeld op halve grootte

Daarna: jpg's maken voor ideeen/img (zie BEELDEN onderaan).
Niet opnieuw gerenderd (camera niet bewaard, maten niet in beeld): img-005 greep, img-015 uitsparing,
img-017 vensterbank_hoek, img-018 vensterbank_boven. img-007 is een productfoto.
"""

import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else bpy.path.abspath("//")
_r = {"__name__": "render"}
exec(open(os.path.join(ROOT, "tools", "render.py")).read(), _r)

# naam: (variant, camera, breedte, hoogte, extra) — camera: vaste naam of (positie, richtpunt, lens) in m
SHOTS = {
    "overzicht":          ("bmn", "Overzicht", 1600, 900, {}),
    "muur6":              ("bmn", "Muur 6", 1600, 900, {}),
    "aanzicht_muur6":     ("bmn", ((1.22, -1.25, 1.25), (2.14, -1.25, 1.25), 50), 1600, 1600, dict(ortho=2.6)),
    "aanzicht_muur5":     ("bmn", ((1.07, -1.1, 1.25), (1.07, 0, 1.25), 50), 1380, 1600, dict(ortho=2.62)),
    "aanzicht_muur4_nis": ("bmn", ((0.5, -1.27, 1.25), (0, -1.27, 1.25), 50), 1600, 1560, dict(ortho=2.7)),
    "bovenkast_greeploos": ("bmn", ((1.15, -1.75, 1.2), (2.14, -0.75, 1.75), 20), 1200, 900, {}),
    "tegels_kookwand":    ("bmn", ((0.25, -1.3, 1.3), (2.14, -1.3, 1.3), 21), 1600, 700, {}),
    "langs_werkblad":     ("bmn", "Langs werkblad", 1600, 900, {}),
    "raam":               ("bmn", "Raam", 1600, 900, {}),
    "hoek_muur7":         ("bmn", "Hoek Muur 7", 1600, 900, {}),
    "wandtegel_detail":   ("bmn", ((0.75, -0.8, 1.35), (0.05, -0.05, 1.15), 30), 1600, 900, {}),
    "koelkast_wit":       ("bmn", ((1.55, -1.2, 1.45), (0.0, -1.85, 1.3), 16), 1600, 900, {}),
    "koelkast_eiken":     ("bmn eiken", ((1.55, -1.2, 1.45), (0.0, -1.85, 1.3), 16), 1600, 900, {}),
    "spoelbak":           ("bmn", "Spoelbak", 1600, 900, {}),
}

# render -> beeld in ideeen/img (zelfde bestandsnamen als in index.html)
BEELDEN = {
    "overzicht": "img-000", "muur6": "img-001", "aanzicht_muur6": "img-002", "aanzicht_muur5": "img-003",
    "aanzicht_muur4_nis": "img-004", "bovenkast_greeploos": "img-006", "tegels_kookwand": "img-008",
    "langs_werkblad": "img-009", "raam": "img-010", "hoek_muur7": "img-011", "wandtegel_detail": "img-012",
    "koelkast_wit": "img-013", "koelkast_eiken": "img-014", "spoelbak": "img-016",
}


def render(namen=None, proef=False, map_="renders/ideeen"):
    huidig = None
    for naam in namen or SHOTS:
        variant, cam, w, h, extra = SHOTS[naam]
        if variant != huidig:
            _r["toon"](variant)
            huidig = variant
        if proef:
            print(_r["shot"](os.path.join(map_, naam), cam, w // 2, h // 2, samples=16, **extra))
        else:
            print(_r["shot"](os.path.join(map_, naam), cam, w, h, **extra))
