"""
Dagverloop-video: één zomerdag (21 juni) in Amersfoort, keuken op het noorden.

De zon loopt van noordoost via het zuiden naar noordwest. Door het raam op het noorden valt
alleen 's ochtends vroeg en 's avonds laat direct zonlicht naar binnen; overdag is het
indirect daglicht. Als het donker wordt gaan de lampen aan.

Draaien (Keuken.blend wordt niet aangepast of opgeslagen):
    Blender -b Keuken.blend --python dagverloop.py                 -> renders/dagverloop.mp4
    Blender -b Keuken.blend --python dagverloop.py -- 1 200 350    -> losse proefbeelden van die frames
"""

import math
import sys
import bpy
from mathutils import Vector

# ---------------------------------------------------------------- instellingen
BREEDTEGRAAD = 52.15      # Amersfoort
DECLINATIE = 23.44        # 21 juni (winter: -23.44)
TIJDVERSCHIL = 1.63       # zomertijd minus zonnetijd in Amersfoort (uur)
VAN, TOT = 4.5, 23.5      # kloktijd begin en eind van de video
SECONDEN, FPS = 16, 25
CAMERA = "Camera - Doorkijk woonkamer"
NOORDEN = 0.0             # hoek (graden) van het noorden t.o.v. de +y-as; +y = buiten het raam
LAMPEN_AAN = (21.3, 22.0) # kloktijd waarin de lampen aangaan (van, tot volledig aan)
UITVOER = "//renders/dagverloop.mp4"

NACHT = (0.010, 0.014, 0.030)
SCHEMER = (0.95, 0.55, 0.35)
DAG = (0.75, 0.82, 0.92)
DAG_STERKTE = 0.06        # wereld: alleen nog wat opvullicht; het daglicht komt via het raam
RAAMLICHT = 220           # W: diffuus hemellicht door het raam bij volle dag
ZON_STERKTE = 4.0
LAMPEN_FACTOR = 3.0       # lampen 's avonds sterker dan in de stilstaande renders (daar helpt daglicht mee)


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def zonnestand(klok):
    """Hoogte en azimut (graden, azimut vanaf noord met de klok mee) voor een kloktijd."""
    phi, dlt = math.radians(BREEDTEGRAAD), math.radians(DECLINATIE)
    H = math.radians(15 * (klok - TIJDVERSCHIL - 12))
    sin_h = math.sin(phi) * math.sin(dlt) + math.cos(phi) * math.cos(dlt) * math.cos(H)
    h = math.asin(sin_h)
    A = math.atan2(-math.cos(dlt) * math.sin(H), math.cos(phi) * math.sin(dlt) - math.sin(phi) * math.cos(dlt) * math.cos(H))
    return math.degrees(h), math.degrees(A)


def woonkamer_dichtmaken():
    """Tijdelijke muren om de woonkamer: in het model is die open, waardoor daglicht van alle kanten binnenkomt."""
    import bmesh
    muur = bpy.data.materials["Muur"]
    for naam, (x0, y0, x1, y1) in {
        "zuid": (-1.56, -4.60, 2.39, -4.50),
        "west": (-1.56, -4.60, -1.46, -2.48),
        "west noord": (-1.56, -2.63, -0.46, -2.48),
        "oost": (2.29, -4.60, 2.39, -2.50),
    }.items():
        me = bpy.data.meshes.new("Woonkamer " + naam)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            v.co.y = y0 + (v.co.y + 0.5) * (y1 - y0)
            v.co.z = -0.02 + (v.co.z + 0.5) * 2.57
        bm.to_mesh(me)
        bm.free()
        me.materials.append(muur)
        bpy.context.scene.collection.objects.link(bpy.data.objects.new("Woonkamer " + naam, me))


def opzetten():
    sc = bpy.context.scene
    woonkamer_dichtmaken()
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, SECONDEN * FPS
    sc.camera = bpy.data.objects[CAMERA]

    zon = bpy.data.objects["Zon"]
    zon.animation_data_clear()
    zon.data.animation_data_clear()
    bg = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND")
    uitzicht = bpy.data.materials["Uitzicht"].node_tree
    em = next(n for n in uitzicht.nodes if n.type == "EMISSION")
    tex = next(n for n in uitzicht.nodes if n.type == "TEX_IMAGE")
    tint = uitzicht.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    uitzicht.links.new(tex.outputs["Color"], tint.inputs["A"])
    uitzicht.links.new(tint.outputs["Result"], em.inputs["Color"])
    lampen = [(o.data, o.data.energy * LAMPEN_FACTOR) for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SPOT"]
    # hemellicht door het raam: vlakke lichtbron in de raamopening die de keuken in schijnt
    glas = bpy.data.objects["Glas"]
    rl = bpy.data.lights.new("Daglicht raam", "AREA")
    rl.shape = "RECTANGLE"
    rl.size, rl.size_y = glas.dimensions.x, glas.dimensions.z
    rl.spread = math.radians(160)
    raamlicht = bpy.data.objects.new("Daglicht raam", rl)
    sc.collection.objects.link(raamlicht)
    c = sum((glas.matrix_world @ v.co for v in glas.data.vertices), Vector()) / len(glas.data.vertices)
    raamlicht.location = (c.x, 0.02, c.z)
    raamlicht.rotation_euler = (math.radians(-90), 0, 0)
    raamlicht.visible_camera = False
    lenzen = [m for m in bpy.data.materials if m.name == "Spot lens"]

    def klok(f):
        return VAN + (TOT - VAN) * (f - 1) / (sc.frame_end - 1)

    for f in range(1, sc.frame_end + 1, 2):
        t = klok(f)
        h, A = zonnestand(t)
        dag = smooth(-6, 16, h)
        warm = 1 - smooth(1, 20, h)

        # zon: richting, sterkte en kleur
        A_r, h_r = math.radians(A + NOORDEN), math.radians(max(h, -2))
        naar_zon = (math.sin(A_r) * math.cos(h_r), math.cos(A_r) * math.cos(h_r), math.sin(h_r))
        zon.rotation_euler = Vector(naar_zon).to_track_quat("Z", "Y").to_euler()
        zon.keyframe_insert("rotation_euler", frame=f)
        zon.data.energy = ZON_STERKTE * smooth(-1, 6, h)
        zon.data.color = mix((1.0, 0.96, 0.90), (1.0, 0.50, 0.25), warm)
        zon.data.keyframe_insert("energy", frame=f)
        zon.data.keyframe_insert("color", frame=f)

        # lucht en uitzicht
        lucht = mix(NACHT, mix(DAG, SCHEMER, warm * 0.6), dag)
        bg.inputs["Color"].default_value = (*lucht, 1.0)
        bg.inputs["Strength"].default_value = 0.02 + (DAG_STERKTE - 0.02) * dag
        bg.inputs["Color"].keyframe_insert("default_value", frame=f)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
        tint.inputs["B"].default_value = (*mix((0.25, 0.32, 0.55), mix((1, 1, 1), (1.0, 0.78, 0.6), warm), dag), 1.0)
        tint.inputs["B"].keyframe_insert("default_value", frame=f)
        em.inputs["Strength"].default_value = 0.015 + 0.985 * dag
        em.inputs["Strength"].keyframe_insert("default_value", frame=f)
        rl.energy = RAAMLICHT * dag
        rl.color = mix((0.9, 0.95, 1.0), (1.0, 0.75, 0.55), warm)
        rl.keyframe_insert("energy", frame=f)
        rl.keyframe_insert("color", frame=f)

        # lampen
        aan = smooth(LAMPEN_AAN[0], LAMPEN_AAN[1], t)
        for ld, e in lampen:
            ld.energy = e * aan
            ld.keyframe_insert("energy", frame=f)
        for m in lenzen:
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Emission Strength"].default_value = 8.0 * aan
            b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

    # tijd in beeld
    sc.render.use_stamp = True
    for attr in [a for a in dir(sc.render) if a.startswith("use_stamp_")]:
        try:
            setattr(sc.render, attr, attr == "use_stamp_note")
        except (AttributeError, TypeError):
            pass
    sc.render.stamp_font_size = 44
    sc.render.stamp_background = (0, 0, 0, 0.6)

    def tijd_label(scene, *_):
        t = klok(scene.frame_current)
        scene.render.stamp_note_text = f"21 juni {int(t):02d}:{int(round((t % 1) * 60)) % 60:02d}"
    bpy.app.handlers.frame_change_pre.append(tijd_label)
    tijd_label(sc)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opzetten()
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.eevee.taa_render_samples = 64
    if argv:   # proefbeelden
        sc.render.image_settings.file_format = "PNG"
        for f in map(int, argv):
            sc.frame_set(f)
            sc.render.filepath = bpy.path.abspath(f"//renders/dagverloop_{f:03d}.png")
            bpy.ops.render.render(write_still=True)
        return
    im = sc.render.image_settings
    if hasattr(im, "media_type"):
        im.media_type = "VIDEO"
    im.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.audio_codec = "NONE"
    sc.render.filepath = bpy.path.abspath(UITVOER)
    bpy.ops.render.render(animation=True)


main()
