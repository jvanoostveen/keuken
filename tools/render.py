"""
Renderhulp: bouw een variant op en render vaste of eigen camerastandpunten.

In de open Blender (via MCP of Scripting):
    ns = {"__name__": "render"}; exec(open("tools/render.py").read(), ns)
    ns["toon"]("echt Steenbok Rustic Olive 13x13 | LG Pleat")
    ns["shot"]("renders/test/raam", "Raam")
    ns["shot"]("renders/test/kraan", ((1.25, -0.6, 1.4), (0.9, -0.02, 1.08), 30))

Vanaf de terminal (Blender op de achtergrond, bestand wordt niet opgeslagen):
    Blender -b "Keuken - variaties.blend" --python tools/render.py -- "<variant>" renders/test Raam Overzicht

Camera: de naam van een vaste camera zonder "Camera - " (Overzicht, Muur 6, Raam, Koelkast,
Doorkijk woonkamer, Hoek Muur 7, Langs werkblad, Spoelbak) of een tuple (positie, richtpunt, lens)
in meters; voeg ortho=<breedte in m> toe voor een recht aanzicht.
"""

import os
import sys
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else bpy.path.abspath("//")
_ns = {}


def toon(variant=None):
    """Bouw de keuken opnieuw op; met variant via variaties.py, anders alleen keuken.py."""
    path = os.path.join(ROOT, "variaties.py" if variant else "keuken.py")
    _ns.clear()
    _ns["__name__"] = "variaties" if variant else "__main__"
    exec(compile(open(path).read(), path, "exec"), _ns)
    if variant:
        _ns["toon"](variant)


def shot(uit, camera, w=1600, h=900, samples=96, ortho=None, clip=0.02):
    """Render naar <uit>.png (pad relatief aan de repo)."""
    sc = bpy.context.scene
    tijdelijk = None
    if isinstance(camera, str):
        sc.camera = bpy.data.objects["Camera - " + camera]
    else:
        loc, tgt, lens = camera
        cd = bpy.data.cameras.new("tmp")
        tijdelijk = bpy.data.objects.new("tmp", cd)
        sc.collection.objects.link(tijdelijk)
        cd.lens, cd.clip_start = lens, clip
        if ortho:
            cd.type, cd.ortho_scale = "ORTHO", ortho
        tijdelijk.location = loc
        tijdelijk.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.camera = tijdelijk
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.eevee.taa_render_samples = samples
    pad = os.path.join(ROOT, uit) + ".png"
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = pad
    bpy.ops.render.render(write_still=True)
    if tijdelijk:
        bpy.data.objects.remove(tijdelijk)
        bpy.data.cameras.remove(cd)
    sc.camera = bpy.data.objects.get("Camera - Overzicht")
    return pad


if __name__ == "__main__" and "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    variant, map_ = args[0] or None, args[1]
    toon(variant)
    for cam in args[2:] or ["Overzicht"]:
        print(shot(os.path.join(map_, cam.lower().replace(" ", "_")), cam))
