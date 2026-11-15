"""
Variaties op de keuken, afgeleid van het moodboard (fotos/mood).

Gebruik: zet VARIANT hieronder en draai dit script in Blender (Scripting > Run Script).
Voor de tegelvarianten moeten eerst de texturen bestaan: draai daarvoor eenmalig tegeltexturen.py.
Het script bouwt eerst de basis opnieuw op met keuken.py en voegt daarna de onderdelen
van de gekozen variant toe in de collectie "Keuken > Variatie". Opnieuw keuken.py draaien
haalt alles van de variatie weer weg.

    "huidig"                  het huidige ontwerp
    "zellige"                 vierkante zellige 10x10 in gemengd zeegroen + muur Tranquil Dawn
    "visgraat"                saliegroene visgraat 7,5x30 + muur Simply Bread
    "effen <kleur>"           effen vierkant 12,5x12,5: mint, zeegroen, creme, duifblauw, olijf, eucalyptus
    "staafjes <muurverf>"     huidig staafjesmozaïek met een andere muurkleur (zie VARIANTEN)
    eerdere voorstellen: "groen", "hout", "accenten", "combinatie"
"""

import math
import bpy
import bmesh
from mathutils import Vector

VARIANT = "zellige"

# Muurverven (Flexa Creations "Sustainable Future" van het moodboard, waarden van verf-plaza.nl)
MUURVERF = {
    "Denim Drift": "#7C8D95",      # ligt dicht bij het huidige grijsblauw
    "Serene Lagoon": "#627775",
    "Tranquil Dawn": "#BEC2BA",
    "Simply Bread": "#E7E6DD",
    "Cornflower Field": "#D1BE8E",
    "Sturdy Leaf": "#858A77",
    "Frosted Sky": "#CBDDE8",      # Flexa Creations 3006, lichtblauw (verfkleuren.nl)
    # dieper dan Frosted Sky (hex = schatting via pontata.com, geen fabriekswaarde)
    "LG Pleat": "#5F7A75",         # Little Greene Pleat No. 280, gedempt petrol
    "FB India Yellow": "#CB9E59",  # Farrow & Ball India Yellow No. 66, warme oker
    "FB Inchyra Blue": "#586768",  # Farrow & Ball Inchyra Blue No. 289, diep grijsblauw-groen
    "FB Red Earth": "#C57B67",     # Farrow & Ball Red Earth No. 64, terracotta
    "FB Bancha": "#686A47",        # Farrow & Ball Bancha No. 298, diep olijf
    "FB Green Smoke": "#737C70",   # Farrow & Ball Green Smoke No. 47, rokerig blauwgroen
}

# Elke variant: lijst van onderdelen; een tuple is (onderdeel, argument).
# De decortegel achter de kookplaat blijft in alle tegelvarianten.
VARIANTEN = {
    "huidig": [],
    "zellige": [("wandtegel", "zellige"), ("muurkleur", "Tranquil Dawn")],
    "visgraat": [("wandtegel", "visgraat"), ("muurkleur", "Simply Bread")],
    "zellige Denim Drift": [("wandtegel", "zellige"), ("muurkleur", "Denim Drift")],
    "effen mint": [("wandtegel", "effen mint"), ("muurkleur", "Simply Bread")],
    "effen zeegroen": [("wandtegel", "effen zeegroen"), ("muurkleur", "Denim Drift")],
    "effen creme": [("wandtegel", "effen creme"), ("muurkleur", "Serene Lagoon")],
    "effen duifblauw": [("wandtegel", "effen duifblauw"), ("muurkleur", "Tranquil Dawn")],
    "effen olijf": [("wandtegel", "effen olijf"), ("muurkleur", "Simply Bread")],
    "effen olijf Frosted Sky": [("wandtegel", "effen olijf"), ("muurkleur", "Frosted Sky")],
    # huidige stand (document voor BMN): olijf + Frosted Sky, vakkenkast wit of eiken
    "bmn": [("wandtegel", "effen olijf"), ("muurkleur", "Frosted Sky")],
    "bmn eiken": [("wandtegel", "effen olijf"), ("muurkleur", "Frosted Sky"), ("eiken_vakkenkast", False)],
    # echte tegels x muurkleuren: VARIANT = "echt <tegelnaam> | <muurverf>", bv. "echt Steenbok Rustic Olive 13x13 | LG Pleat"

    "effen olijf Denim Drift": [("wandtegel", "effen olijf"), ("muurkleur", "Denim Drift")],
    "effen eucalyptus": [("wandtegel", "effen eucalyptus"), ("muurkleur", "Simply Bread")],
    "effen eucalyptus Frosted Sky": [("wandtegel", "effen eucalyptus"), ("muurkleur", "Frosted Sky")],
    "visgraat Tranquil Dawn": [("wandtegel", "visgraat"), ("muurkleur", "Tranquil Dawn")],
    "staafjes Denim Drift": [("muurkleur", "Denim Drift")],
    "staafjes Serene Lagoon": [("muurkleur", "Serene Lagoon")],
    "staafjes Tranquil Dawn": [("muurkleur", "Tranquil Dawn")],
    "staafjes Cornflower Field": [("muurkleur", "Cornflower Field")],
    # eerdere voorstellen (8 oktober)
    "groen": ["onder_groen"],
    "hout": ["open_planken", "eiken_vakkenkast"],
    "accenten": ["hanglamp", "kookgerei", "planten"],
    "combinatie": ["onder_groen", "open_planken", "eiken_vakkenkast", "hanglamp", "kookgerei", "planten"],
}

# Wandtegels (texturen gemaakt met tegeltexturen.py). maat = textuurmaat in mm (breedte, hoogte).
WANDTEGELS = {
    "zellige": dict(textuur="tegel_zellige", maat=(1015, 1015), glans=0.06, reliëf=0.35),   # 10 x 10 cm, voeg 1,5 mm
    "visgraat": dict(textuur="tegel_visgraat", maat=(1272.79, 1272.79), glans=0.08, reliëf=0.3),  # 7,5 x 30 cm, voeg 2 mm
}
# echte tegels (texturen uit productfoto's, gemaakt met echte_tegels.py)
WANDTEGELS["Steenbok Rustic Olive 13x13"] = dict(textuur="tegel_echt_steenbok", maat=(1056, 1056), glans=0.1, reliëf=0.35)
WANDTEGELS["Equipe Hanoi Wild Olive 10x10"] = dict(textuur="tegel_echt_hanoi", maat=(816, 816), glans=0.08, reliëf=0.45)
WANDTEGELS["Marazzi Zellige Salvia 10x10"] = dict(textuur="tegel_echt_marazzi", maat=(816, 816), glans=0.06, reliëf=0.45)
for _kleur in ("mint", "zeegroen", "creme", "duifblauw", "olijf", "eucalyptus"):   # effen 12,5 x 12,5 cm, voeg 2 mm
    WANDTEGELS["effen " + _kleur] = dict(textuur="tegel_effen_" + _kleur, maat=(1016, 1016), glans=0.12, reliëf=0.15)

KLEUREN = {
    "Early Dew": (0.663, 0.706, 0.671),   # Flexa Creations Early Dew (#A9B4AB)
    "Eiken": (0.70, 0.52, 0.34),
    "Oranje": (0.88, 0.36, 0.10),         # zoals de oranje lamp en Le Creuset-pannen op het moodboard
    "Messing": (0.80, 0.60, 0.32),
    "Terracotta": (0.70, 0.38, 0.24),
    "Blad": (0.16, 0.36, 0.10),
    "Blad licht": (0.32, 0.52, 0.18),
    "Salie keramiek": (0.60, 0.68, 0.60),
    "Room keramiek": (0.92, 0.89, 0.82),
    "Amber": (0.85, 0.52, 0.10),
}

K = {}   # namespace van keuken.py (box, cylinder, make_mat, ...)


# ------------------------------------------------------------------ hulpfuncties

def basis():
    path = bpy.path.abspath("//keuken.py")
    K.clear()
    K["__name__"] = "keuken"
    exec(compile(open(path).read(), path, "exec"), K)
    coll = K["get_coll"]("Variatie", bpy.data.collections["Keuken"])
    return coll


def mat(naam, kleur=None, rough=0.5, metal=0.0, alpha=1.0, emissie=0.0):
    m = K["make_mat"](naam, kleur or KLEUREN[naam], rough=rough, metal=metal, alpha=alpha)
    if alpha < 1 and hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    if emissie:
        b = K["principled"](m)
        b.inputs["Emission Color"].default_value = K["lin"](kleur or KLEUREN[naam])
        b.inputs["Emission Strength"].default_value = emissie
    return m


def eiken_mat():
    """Geolied eiken: lichte banen met nerf langs de lengte (lokale x of z)."""
    m = mat("Eiken", rough=0.55)
    nt = m.node_tree
    co = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 60.0, 1.0)
    nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Distortion"].default_value = 1.5
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = K["lin"](tuple(v * 0.78 for v in KLEUREN["Eiken"]))
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = K["lin"](tuple(min(1, v * 1.08) for v in KLEUREN["Eiken"]))
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], K["principled"](m).inputs["Base Color"])
    return m


def mesh_obj(naam, bm, materiaal, coll, parent=None, loc=(0, 0, 0), glad=True):
    me = bpy.data.meshes.new(naam)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(materiaal if not isinstance(materiaal, str) else K["MATS"][materiaal])
    for p in me.polygons:
        p.use_smooth = glad
    return K["new_obj"](naam, me, coll, parent, loc)


def bol(naam, r, loc, materiaal, coll, parent=None, schaal=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * schaal[0], v.co.y * schaal[1], v.co.z * schaal[2]))
    return mesh_obj(naam, bm, materiaal, coll, parent, loc)


def kegel(naam, r1, r2, h, loc, materiaal, coll, parent=None, open_onder=False):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r1, radius2=r2, depth=h)
    if open_onder:
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9], context="FACES")
    ob = mesh_obj(naam, bm, materiaal, coll, parent, loc)
    for p in ob.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return ob


def buis(naam, punten, r, materiaal, coll, parent=None):
    cu = bpy.data.curves.new(naam, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    sp = cu.splines.new("NURBS")
    sp.points.add(len(punten) - 1)
    for p, co in zip(sp.points, punten):
        p.co = (*co, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(punten))
    cu.materials.append(materiaal if not isinstance(materiaal, str) else K["MATS"][materiaal])
    return K["new_obj"](naam, cu, coll, parent)


def blad(naam, loc, r, richting, materiaal, coll, parent=None, vorm="rond"):
    """Blad met een lichte bolling, gericht langs 'richting'. vorm 'hart' = langwerpig met punt (scindapsus)."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=r)
    for v in bm.verts:
        if vorm == "hart":
            x, y = v.co.x, v.co.y
            punt = max(0.0, y / r) ** 2
            v.co.x = x * 0.62 * (1 - 0.7 * punt)
            v.co.y = y * 1.35 + 0.25 * r
        v.co.z = -0.25 * (v.co.x ** 2 + v.co.y ** 2) / r
    ob = mesh_obj(naam, bm, materiaal, coll, parent, loc)
    ob.rotation_euler = Vector(richting).to_track_quat("Z", "Y").to_euler()
    ob.visible_shadow = True
    return ob


def cyl(naam, r, h, loc, materiaal, coll, parent=None, axis="Z"):
    m = materiaal if isinstance(materiaal, str) else materiaal.name
    return K["cylinder"](naam, r, h, loc, m, coll, parent, axis=axis)


def verberg(ob):
    for o in [ob] + list(ob.children_recursive):
        o.hide_render = True
        o.hide_viewport = True


def hex_srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def muurkleur(coll, naam):
    """Muurverf voor Muur 4 (boven het tegelwerk), Muur 5 rond het raam en de koof."""
    m = bpy.data.materials["Muur accent"]
    K["principled"](m).inputs["Base Color"].default_value = K["lin"](hex_srgb(MUURVERF[naam]))
    m.diffuse_color = K["lin"](hex_srgb(MUURVERF[naam]))


def wandtegel(coll, soort):
    """Vervangt het staafjesmozaïek op Muur 4, 5 en 7 door een andere wandtegel (zelfde vlakken)."""
    T = WANDTEGELS[soort]
    m = bpy.data.materials.get("Wandtegel " + soort) or bpy.data.materials.new("Wandtegel " + soort)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1000 / T["maat"][0], 1000 / T["maat"][1], 1)
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])

    def beeld(achtervoegsel, data):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(bpy.path.abspath(f"//textures/{T['textuur']}_{achtervoegsel}.png"), check_existing=True)
        tex.image.reload()
        if data:
            tex.image.colorspace_settings.is_data = True
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        return tex
    kleur, data = beeld("kleur", False), beeld("data", True)
    nt.links.new(kleur.outputs["Color"], bsdf.inputs["Base Color"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(data.outputs["Color"], sep.inputs["Color"])
    ruw = nt.nodes.new("ShaderNodeMapRange")       # glazuur glanzend, voeg mat
    ruw.inputs["To Min"].default_value = T["glans"]
    ruw.inputs["To Max"].default_value = 0.85
    nt.links.new(sep.outputs["Green"], ruw.inputs["Value"])
    nt.links.new(ruw.outputs["Result"], bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = T["reliëf"]
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(sep.outputs["Red"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    for ob in bpy.data.objects:
        if ob.name.startswith("Mozaiek ") and ob.type == "MESH":
            ob.data.materials[0] = m


def run6():
    return bpy.data.objects["Onderkasten Muur 6"]


ZB = None   # werkbladhoogte (boven), gezet in toon()


# ------------------------------------------------------------------ onderdelen

def onder_groen(coll):
    """Voorstel 1: alle fronten en plinten van de onderkasten in Early Dew; boven en hoge kast blijven crèmewit."""
    groen = K["make_mat"]("Front Early Dew", KLEUREN["Early Dew"], rough=0.35)
    for ob in bpy.data.collections["Onderkasten"].all_objects:
        if ob.type == "MESH" and ob.data.materials and ob.data.materials[0].name == "Front":
            ob.data.materials[0] = groen


def open_planken(coll):
    """Voorstel 2: bovenkasten tussen raam en wasemkap (passtuk + 2x 40) vervangen door twee eiken planken
    op zwarte dragers, zoals de wandplank in de woonkamer."""
    bk = bpy.data.objects["Bovenkasten Muur 6"]
    for c in list(bk.children):
        if c.name.startswith("Bovenkast 40") or (c.name.startswith("Passtuk") and c.matrix_world.translation.y > -0.05):
            verberg(c)
    eiken = eiken_mat()
    r = empty("Open planken", coll, bk)
    zwart = K["MATS"]["Greep"]
    lengte, diepte, dikte = 0.88, 0.25, 0.03
    hoogtes = (1.62, 1.95)
    for i, z in enumerate(hoogtes):
        K["box"](f"Eiken plank {i + 1}", 0.01, 0, z, 0.01 + lengte, -diepte, z + dikte, eiken, coll, r, bevel=0.003)
        for xd in (0.14, 0.76):   # zwarte drager: wandstrip + arm onder de plank
            K["box"](f"Drager {i + 1}", xd, 0, z - 0.14, xd + 0.025, -0.004, z, zwart, coll, r)
            K["box"](f"Drager arm {i + 1}", xd, 0, z - 0.004, xd + 0.025, -0.22, z, zwart, coll, r)
    # zijwand van de naastgelegen bovenkast in frontkleur, want die wordt nu zichtbaar
    K["box"]("Zijwand bovenkast 45", 0.881, 0, 1.43, 0.9, -0.339, 2.21, "Front", coll, r)
    # LED-strip onder de onderste plank
    led = bpy.data.lights.new("LED onder plank", "AREA")
    led.shape, led.size, led.size_y = "RECTANGLE", 0.8, 0.02
    led.energy, led.color = 2.5, (1.0, 0.82, 0.62)
    K["new_obj"]("LED onder plank", led, coll, r, (0.45, -0.12, hoogtes[0] - 0.003))
    styling_planken(coll, r, [h + dikte for h in hoogtes])


def styling_planken(coll, r, tops):
    glas = mat("Glaspot", (0.9, 0.95, 0.95), rough=0.05, alpha=0.22)
    eiken = K["MATS"]["Eiken"]
    inhoud = [("Pasta", (0.93, 0.80, 0.48)), ("Linzen", (0.78, 0.36, 0.14)), ("Koffiebonen", (0.24, 0.14, 0.07))]
    z = tops[0]
    for i, (x, h, (n, c)) in enumerate(zip((0.08, 0.18, 0.28), (0.20, 0.16, 0.13), inhoud)):
        cyl(f"Voorraadpot {i}", 0.045, h, (x, -0.12, z + h / 2), glas, coll, r)
        cyl(f"Voorraadpot {i} inhoud", 0.041, h * 0.7, (x, -0.12, z + h * 0.35 + 0.003), mat(n, c, rough=0.8), coll, r)
        cyl(f"Voorraadpot {i} deksel", 0.047, 0.02, (x, -0.12, z + h + 0.01), eiken, coll, r)
    for i, (x, kl) in enumerate(((0.42, "Salie keramiek"), (0.50, "Oranje"))):
        mok(f"Mok {i}", (x, -0.10, z), mat(kl, rough=0.3), coll, r)
    pilea("Pilea plank", (0.64, -0.12, z), coll, r, schaal=0.9)
    cyl("Amber vaas", 0.04, 0.15, (0.80, -0.11, z + 0.075), mat("Amber", rough=0.08, alpha=0.6), coll, r)
    z = tops[1]
    for i in range(3):
        kegel(f"Kom {i}", 0.055, 0.085, 0.05, (0.10, -0.12, z + 0.025 + i * 0.03), K["MATS"].get("Room keramiek") or mat("Room keramiek", rough=0.3), coll, r)
    for i, (w, h, c) in enumerate(((0.032, 0.25, (0.18, 0.40, 0.42)), (0.026, 0.23, (0.85, 0.66, 0.22)), (0.04, 0.26, (0.90, 0.88, 0.80)), (0.03, 0.22, (0.80, 0.40, 0.20)))):
        x0 = 0.26 + sum(v[0] for v in ((0.032,), (0.026,), (0.04,), (0.03,))[:i])
        K["box"](f"Kookboek {i}", x0, -0.03, z, x0 + w, -0.21, z + h, mat(f"Boek {i}", c, rough=0.7), coll, r)
    pothos("Pothos plank", (0.66, -0.13, z), coll, r, lengte=0.55)


def eiken_vakkenkast(coll, spullen=True):
    """Voorstel 2b: de open vakkenkast naast de koelkast in eiken in plaats van wit."""
    eiken = K["MATS"].get("Eiken") or eiken_mat()
    kast = bpy.data.objects["Open kast"]
    for c in kast.children:
        if c.type == "MESH" and c.data.materials[0].name == "Front":
            c.data.materials[0] = eiken
    if not spullen:
        return
    # wat spullen in de vakken: kookboeken, voorraadpotten en een plantje
    planken = sorted(c.location.z for c in kast.children if "plank" in c.name)
    z_boek, z_pot, z_plant = (planken[3] + 0.018, planken[4] + 0.018, planken[5] + 0.018)
    x = 0.022
    for i, (w, h, c) in enumerate(((0.03, 0.24, (0.85, 0.66, 0.22)), (0.025, 0.22, (0.18, 0.40, 0.42)), (0.035, 0.26, (0.80, 0.40, 0.20)), (0.028, 0.23, (0.90, 0.88, 0.80)))):
        K["box"](f"Vak boek {i}", x, -0.04, z_boek, x + w, -0.22, z_boek + h, mat(f"Boek {i}", c, rough=0.7), coll, kast)
        x += w + 0.002
    glas = mat("Glaspot", (0.9, 0.95, 0.95), rough=0.05, alpha=0.22)
    for i, (y, h, (n, c)) in enumerate(zip((-0.08, -0.19), (0.18, 0.14), (("Pasta", (0.93, 0.80, 0.48)), ("Linzen", (0.78, 0.36, 0.14))))):
        cyl(f"Vak pot {i}", 0.045, h, (0.10, y, z_pot + h / 2), glas, coll, kast)
        cyl(f"Vak pot {i} inhoud", 0.041, h * 0.7, (0.10, y, z_pot + h * 0.35 + 0.003), mat(n, c, rough=0.8), coll, kast)
        cyl(f"Vak pot {i} deksel", 0.047, 0.02, (0.10, y, z_pot + h + 0.01), eiken, coll, kast)
    pilea("Pilea vak", (0.10, -0.14, z_plant), coll, kast, schaal=0.75)


def hanglamp(coll):
    """Voorstel 3: messing koepellamp boven de spoelbak, zoals de messing hanglampen op het moodboard."""
    x, y = 0.94, -0.45
    top, onder = 2.50, 1.80
    lamp = empty("Hanglamp messing", coll, None, (x, y, 0))
    cyl("Hanglamp snoer", 0.003, top - onder - 0.15, (0, 0, (top + onder + 0.15) / 2), "Zwart kunststof", coll, lamp)
    cyl("Hanglamp rozet", 0.05, 0.02, (0, 0, top - 0.01), mat("Messing", rough=0.3, metal=1.0), coll, lamp)
    bm = bmesh.new()   # koepel: halve bol, onder open
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.15)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.001], context="VERTS")
    for v in bm.verts:
        v.co.z *= 0.8
    kap = mesh_obj("Hanglamp kap", bm, "Messing", coll, lamp, (0, 0, onder))
    kap.modifiers.new("Dikte", "SOLIDIFY").thickness = 0.0015
    cyl("Hanglamp kapje", 0.025, 0.04, (0, 0, onder + 0.135), "Messing", coll, lamp)
    bol("Hanglamp lamp", 0.035, (0, 0, onder + 0.05), mat("Gloeilamp", (1.0, 0.85, 0.6), emissie=6.0), coll, lamp)
    ld = bpy.data.lights.new("Hanglamp licht", "POINT")
    ld.energy, ld.color, ld.shadow_soft_size = 30, (1.0, 0.78, 0.55), 0.03
    K["new_obj"]("Hanglamp licht", ld, coll, lamp, (0, 0, onder + 0.03))


def mok(naam, loc, materiaal, coll, parent):
    x, y, z = loc
    cyl(naam, 0.038, 0.09, (x, y, z + 0.045), materiaal, coll, parent)
    buis(naam + " oor", [(x + 0.035, y, z + 0.07), (x + 0.065, y, z + 0.065), (x + 0.065, y, z + 0.03), (x + 0.035, y, z + 0.025)], 0.006, materiaal, coll, parent)


def kookgerei(coll):
    """Voorstel 3: oranje fluitketel en braadpan op de kookplaat, eiken snijplanken, pot met houten lepels."""
    oranje = mat("Oranje", rough=0.22)
    zwart = K["MATS"]["Zwart kunststof"]
    eiken = K["MATS"].get("Eiken") or eiken_mat()
    # fluitketel (voorste kookzone, richting Muur 7)
    k = empty("Fluitketel", coll, None, (1.72, -1.80, ZB + 0.005), rot_z=math.radians(-60))
    bol("Fluitketel body", 0.10, (0, 0, 0.078), oranje, coll, k, schaal=(1, 1, 0.78))
    cyl("Fluitketel voet", 0.085, 0.01, (0, 0, 0.005), zwart, coll, k)
    bol("Fluitketel knop", 0.014, (0, 0, 0.162), zwart, coll, k)
    buis("Fluitketel tuit", [(0.07, 0, 0.07), (0.11, 0, 0.10), (0.145, 0, 0.135)], 0.013, oranje, coll, k)
    buis("Fluitketel hengsel", [(-0.07, 0, 0.13), (-0.04, 0, 0.215), (0.04, 0, 0.215), (0.07, 0, 0.13)], 0.008, zwart, coll, k)
    # braadpan (achterste zone, richting het raam)
    p = empty("Braadpan", coll, None, (1.97, -1.52, ZB + 0.005))
    cyl("Braadpan body", 0.11, 0.085, (0, 0, 0.0425), oranje, coll, p)
    cyl("Braadpan deksel", 0.113, 0.012, (0, 0, 0.091), oranje, coll, p)
    bol("Braadpan knop", 0.02, (0, 0, 0.102), zwart, coll, p, schaal=(1, 1, 0.6))
    for s in (-1, 1):
        K["box"]("Braadpan oor", -0.025, s * 0.105, 0.06, 0.025, s * 0.135, 0.075, oranje, coll, p, bevel=0.005)
    # snijplanken tegen de tegels, rechts van de kookplaat
    for i, (lx, w, h, a, dy) in enumerate(((2.30, 0.28, 0.40, -12, -0.10), (2.20, 0.22, 0.30, -9, -0.13))):
        e = empty(f"Snijplank {i + 1}", coll, run6(), (lx, dy, ZB))
        e.rotation_euler.x = math.radians(a)
        K["box"](f"Snijplank {i + 1}", -w / 2, 0, 0, w / 2, 0.022, h, eiken, coll, e, bevel=0.004)
        cyl(f"Snijplank {i + 1} gat", 0.012, 0.03, (0, 0.011, h - 0.04), zwart, coll, e, axis="Y")
    # pot met houten lepels, links van de kookplaat
    s = empty("Lepelpot", coll, run6(), (1.15, -0.10, ZB))
    cyl("Lepelpot", 0.055, 0.14, (0, 0, 0.07), mat("Salie keramiek", rough=0.3), coll, s)
    for i, (dx, dy, l) in enumerate(((0.012, 0.0, 0.32), (-0.015, 0.01, 0.30), (0.0, -0.015, 0.34), (-0.005, 0.018, 0.28))):
        top = (dx * 4, dy * 4, l)
        buis(f"Lepel {i}", [(dx, dy, 0.02), (dx * 2.5, dy * 2.5, l * 0.6), top], 0.005, eiken, coll, s)
        bol(f"Lepel {i} kop", 0.022, top, eiken, coll, s, schaal=(0.75, 0.35, 1.2))


def pilea(naam, loc, coll, parent=None, schaal=1.0):
    """Pannenkoekplant (zoals in de woonkamer): terracotta pot, steeltjes met ronde bladeren."""
    e = empty(naam, coll, parent, loc)
    s = schaal
    cyl(naam + " pot", 0.05 * s, 0.09 * s, (0, 0, 0.045 * s), mat("Terracotta", rough=0.85), coll, e)
    cyl(naam + " aarde", 0.046 * s, 0.005, (0, 0, 0.088 * s), mat("Aarde", (0.12, 0.08, 0.05), rough=1.0), coll, e)
    groen = mat("Blad", rough=0.45)
    for i in range(11):
        a = i * 2.4
        rr = (0.03 + 0.07 * ((i * 37) % 10) / 10) * s
        h = (0.13 + 0.12 * ((i * 53) % 10) / 10) * s
        tip = (rr * math.cos(a), rr * math.sin(a), h)
        buis(f"{naam} steel {i}", [(0, 0, 0.085 * s), (tip[0] * 0.5, tip[1] * 0.5, h * 0.8), tip], 0.0018, groen, coll, e)
        blad(f"{naam} blad {i}", tip, (0.022 + 0.012 * ((i * 17) % 5) / 5) * s, (math.cos(a) * 0.5, math.sin(a) * 0.5, 1), groen, coll, e)


def pothos(naam, loc, coll, parent=None, lengte=0.6):
    """Hangende scindapsus: pot met ranken die over de rand naar beneden hangen (richting voorkant, -y lokaal)."""
    e = empty(naam, coll, parent, loc)
    cyl(naam + " pot", 0.065, 0.10, (0, 0, 0.05), mat("Room keramiek", rough=0.3), coll, e)
    blad_m = mat("Blad licht", rough=0.4)
    for i in range(6):
        a = math.radians(-150 + i * 22)
        dx, dy = math.cos(a), math.sin(a)
        L = lengte * (0.6 + 0.4 * ((i * 7) % 5) / 5)
        pts = [(0, 0, 0.09), (dx * 0.07, dy * 0.07, 0.13), (dx * 0.13, dy * 0.15 - 0.05, 0.06), (dx * 0.15, dy * 0.18 - 0.10, -L * 0.5), (dx * 0.16 + 0.01 * i, dy * 0.18 - 0.11, -L)]
        buis(f"{naam} rank {i}", pts, 0.0022, mat("Blad", rough=0.45), coll, e)
        for j in range(int(L / 0.045)):
            t = j / max(1, int(L / 0.045) - 1)
            p = Vector(pts[2]).lerp(Vector(pts[4]), t) if t > 0.15 else Vector(pts[1]).lerp(Vector(pts[2]), t / 0.15)
            zij = 1 if j % 2 else -1
            b = blad(f"{naam} blad {i}.{j}", (p.x + zij * 0.018, p.y - 0.012, p.z), 0.028 - 0.008 * t, (zij * 0.5, -1, 0.25), blad_m, coll, e, vorm="hart")
            b.rotation_euler.rotate_axis("Z", math.radians(180 + zij * 35))


def kruiden(naam, loc, coll, parent=None):
    e = empty(naam, coll, parent, loc)
    cyl(naam + " pot", 0.05, 0.08, (0, 0, 0.04), mat("Terracotta", rough=0.85), coll, e)
    groen = mat("Blad licht", rough=0.45)
    for i in range(16):
        a = i * 2.4
        rr = 0.04 * ((i * 31) % 10) / 10
        bol(f"{naam} toef {i}", 0.022, (rr * math.cos(a), rr * math.sin(a), 0.10 + 0.05 * ((i * 13) % 10) / 10), groen, coll, e, schaal=(1, 1, 0.8))


def planten(coll):
    """Voorstel 3: pilea en kruiden op de vensterbank."""
    pilea("Pilea vensterbank", (0.42, 0.035, 1.092), coll, schaal=0.8)
    kruiden("Basilicum vensterbank", (1.52, 0.04, 1.092), coll)


def empty(*a, **kw):
    return K["empty"](*a, **kw)


# ------------------------------------------------------------------ hoofdprogramma

def toon(naam):
    global ZB
    if naam.startswith("echt ") and naam not in VARIANTEN:
        tegel, verf = [d.strip() for d in naam[5:].split("|")]
        VARIANTEN[naam] = [("wandtegel", tegel), ("muurkleur", verf)]
    coll = basis()
    ZB = (K["PLINT"] + K["ONDERKAST_H"] + K["WERKBLAD_DIKTE"]) * K["M"]
    for onderdeel in VARIANTEN[naam]:
        if isinstance(onderdeel, tuple):
            globals()[onderdeel[0]](coll, *onderdeel[1:])
        else:
            globals()[onderdeel](coll)
    print(f"Variant '{naam}' opgebouwd.")


if __name__ == "__main__":
    toon(VARIANT)
