"""
Keuken Amelisweerd 15 — parametrisch Blender-model (eerste versie)

Gebruik
-------
1. Open Keuken.blend, ga naar de werkruimte "Scripting" en open deze tekst (keuken.py).
2. Pas hieronder bij INSTELLINGEN maten, kasten, kleuren of de variant aan.
3. Klik op "Run Script" (Alt+P). Alles in de collectie "Keuken" wordt opnieuw opgebouwd;
   andere objecten die je zelf toevoegt (buiten "Keuken") blijven staan.

Je kunt ook direct in Blender schuiven: elke kast is een Empty met de onderdelen eronder,
dus het Empty verplaatsen verplaatst de hele kast. Let op: opnieuw draaien van het script
zet alles terug naar wat hier staat.

Alle maten in millimeters. Bronnen: BMN offerte 298533 (v1, tekeningen p.9-13) en de
BMN v2-afbeeldingen (koelkast weg van Muur 6, Muur 6 helemaal met onderkasten).

Assenstelsel: x langs Muur 5 (raam) vanaf Muur 4, y = 0 is Muur 5 en de keuken ligt bij
negatieve y, Muur 6 ligt op x = 2140.
"""

import bpy
import bmesh
import math
from mathutils import Matrix, Vector

# =====================================================================
# INSTELLINGEN
# =====================================================================

# Welke BMN v2-indeling van Muur 6: "45-60-50" of "50-60-45"
VARIANT = "45-60-50"

# Kleuren (sRGB 0-1). Front = Keller "Lente groen" (LNT1), benadering.
KLEUREN = {
    "Front":    (0.914, 0.878, 0.824),  # RAL 9001 crèmewit (RAL 9003: 0.925, 0.925, 0.906; Lente groen: 0.66, 0.73, 0.60)
    "Korpus":   (0.86, 0.86, 0.84),   # Mist
    "Muur":     (0.94, 0.93, 0.91),
    "Muur accent": (0.50, 0.59, 0.65),  # gedempt grijsblauw, tintje lichter dan eerder (0.43, 0.52, 0.58); Shallow Pool was (0.569, 0.718, 0.714)
    "Plafond":  (0.97, 0.97, 0.96),
    "Kozijn":   (0.945, 0.925, 0.882),  # RAL 9010 zuiverwit
    "Greep":    (0.06, 0.06, 0.06),   # zwarte greeplijst
}

# Vloer: eiken laminaat zoals nu (kleuren gemeten in fotos/IMG_4040.jpeg).
# richting = hoek van de planken in graden: 90 = lange kant richting het raam (y), 0 = links-rechts.
VLOER = dict(
    donker=(0.42, 0.29, 0.19),   # donkerste nerf (foto 10%, iets warmer)
    midden=(0.57, 0.42, 0.30),
    licht=(0.71, 0.55, 0.41),    # lichtste delen (foto 90%)
    voeg=(0.20, 0.13, 0.08),
    plank_lengte=1380,
    plank_breedte=195,
    richting=90,
)

# Algemene kastmaten
PLAFOND = 2500
PLINT = 130
ONDERKAST_H = 780            # werkblad komt daarmee op 130 + 780 + 32 = 942
ONDERKAST_DIEPTE = 566
WERKBLAD_DIKTE = 32
WERKBLAD_DIEPTE = 600
FRONT_DIKTE = 19
NAAD = 3                     # naad tussen fronten
BOVENKAST_ONDERKANT = 1542   # 942 + 600: een hele decortegel (60 hoog) tussen werkblad en bovenkast
BOVENKAST_H = 780            # bovenkant op 2322, daarboven 40 montageruimte tot de koof
BOVENKAST_DIEPTE = 320       # korpus, + front = 340
BOVENKAST_GREPEN = False     # False = greeploos (push-to-open)
HOGEKAST_H = 2080            # bovenkant op 130 + 2080 = 2210

# Ruimte
RUIMTE = dict(
    muur5_lengte=2140,     # raammuur, van Muur 4 tot Muur 6
    muur6_lengte=2500,     # van Muur 5 tot Muur 7
    muur4_lengte=1680,     # 566 + 1114
    muur3_lengte=310,      # sprongetje naar de nis
    muur2_lengte=800,      # nis waar nu de voorraadkast staat (171 + 628)
    muur1_lengte=600,      # was ~300; verlengd zodat de koelkastkast netjes in de nis valt
    muur7_lengte=666,      # 100 + 566
    muur5_dikte=300,
    muur_dikte=150,
    raam_van=140,          # vanaf Muur 4
    raam_breedte=1570,
    raam_onder=1092,
    binnenframe=18,        # houten binnenkozijn: bekleedt de dagkanten (zijkanten en bovenkant) van de raamopening
    vensterbank_uitsteek=80,  # losse plank: steekt zoveel voor de tegels uit
    vensterbank_dikte=22,
    vensterbank_hoek=30,      # afgeronde hoek (straal) rechtsvoor
    onderdorpel_hoogte=25,    # witte lat van het binnenkozijn onder de plank; daaronder beginnen de tegels
    raam_boven=2280,
    raam_rechterdeel=520,  # breedte van het rechter deel met bovenlicht + draaikiepraam
    raam_bovenlicht=380,
    koof_hoogte=138,       # koof boven het raam langs Muur 5; was 200, verlaagd voor de hogere bovenkasten
    koof_diepte=200,
)

# Onderkasten langs Muur 5, vanaf Muur 4 richting de hoek met Muur 6.
# fronts: lijst van (soort, hoogte) van boven naar beneden; soort = deur / lade / oven
# Let op: deze breedtes + b_muur5 van de hoekkast moeten samen muur5_lengte (2140) zijn.
ONDER_MUUR5 = [
    dict(naam="Passtuk", b=40, type="passtuk"),
    dict(naam="Vaatwasser", b=600, fronts=[("deur", 780)]),
    dict(naam="Spoelkast", b=600, fronts=[("deur", 780)], spoelbak=True),
]

# L-vormige hoekkast zoals bij de buren: twee deuren die in de hoek samenkomen.
# b = maat langs Muur 6, b_muur5 = maat langs Muur 5.
HOEKKAST = dict(naam="Hoekkast", b=900, b_muur5=900, type="hoek", fronts=[("deur", 780)])

# Muur 6, vanaf de hoek met Muur 5 richting Muur 7 (twee BMN v2-varianten)
VARIANTEN = {
    "45-60-50": dict(
        onder=[
            HOEKKAST,
            dict(naam="Deurkast 45", b=450, fronts=[("lade", 120), ("deur", 660)]),   # bovenste lade gelijk met de ovenkast
            dict(naam="Ovenkast 60", b=600, fronts=[("lade", 120), ("oven", 470), ("lade", 190)], kookplaat=True),
            dict(naam="Ladekast 50", b=500, fronts=[("lade", 120), ("lade", 330), ("lade", 330)]),
            dict(naam="Passtuk", b=50, type="passtuk"),
        ],
        boven=[
            dict(naam="Bovenkast 45", b=450),   # 45 + 45 = hoekkast 90 eronder, geen passtuk bij het raam
            dict(naam="Bovenkast 45", b=450),
            dict(naam="Bovenkast 45", b=450),
            dict(naam="Wasemkapkast 60", b=600, afzuigkap=True),
            dict(naam="Bovenkast 50", b=500),
            dict(naam="Passtuk", b=50, type="passtuk"),
        ],
    ),
    "50-60-45": dict(
        onder=[
            HOEKKAST,
            dict(naam="Deurkast 50", b=500, fronts=[("lade", 120), ("deur", 660)]),   # bovenste lade gelijk met de ovenkast
            dict(naam="Ovenkast 60", b=600, fronts=[("lade", 120), ("oven", 470), ("lade", 190)], kookplaat=True),
            dict(naam="Ladekast 45", b=450, fronts=[("lade", 120), ("lade", 330), ("lade", 330)]),
            dict(naam="Passtuk", b=50, type="passtuk"),
        ],
        boven=[
            dict(naam="Bovenkast 45", b=450),   # 45 + 45 = hoekkast 90 eronder, geen passtuk bij het raam
            dict(naam="Bovenkast 45", b=450),
            dict(naam="Bovenkast 50", b=500),
            dict(naam="Wasemkapkast 60", b=600, afzuigkap=True),
            dict(naam="Bovenkast 45", b=450),
            dict(naam="Passtuk", b=50, type="passtuk"),
        ],
    ),
}

# Hoge kasten in de nis bij Muur 2 (waar nu de voorraadkast staat), vanaf Muur 1
# richting Muur 3 — zoals bij de buren, maar gespiegeld.
HOGE_KASTEN = [
    dict(naam="Koelkastkast", b=600, type="hoog", fronts=[("deur", 1300), ("deur", 780)], zijbekleding=True),
    # open vakkenkast: voorkant gelijk met Muur 4 (diepte = muur3_lengte), van vloer tot plafond
    dict(naam="Open kast", b=200, type="open", planken=7, diepte=310, tot_plafond=True),
]

# Verlichting (vermogens in Blender-watt)
SPOT_ONDER_BOVENKAST_W = 6        # inbouwspot onder elke bovenkast, behalve de wasemkapkast
PLAFONDLAMP = dict(
    positie=(1070, -1250),        # x, y in mm (midden van de keuken)
    spot_w=30,
    spots={                       # naam: richtpunt (x, y, z in mm); verschuif het Empty om te richten
        "Spot verwarming": (60, -825, 1930),
        "Spot hoek rechts van raam": (2000, -150, 1000),
        "Spot verre hoek": (2000, -2400, 1000),
    },
)
WARM_LICHT = (1.0, 0.80, 0.60)    # ca. 2700-3000 K

# Video: camera op een vaste plek die langzaam draait (pan), van de koelkast via het raam
# naar de kookplaat. Hoeken in graden: 0 = recht naar het raam, positief = naar links (Muur 4).
PAN = dict(positie=(1050, -2400, 1600), van=52, tot=-52, kantel=-10, lens=16, seconden=12, fps=25)

# Spoelbak: BMN v1 pos. SDE-0047 "RVS vlakinbouwspoelbak", één bak met ronde hoeken.
# Opgegeven maten: binnenbak 500 x 400 mm, buitenmaat ca. 539 x 439 x 200 mm (dus flens 19,5 mm rondom).
# Hoekradii geschat. afvoer_y = afstand van het midden richting de muur. Overloop midden in de achterwand.
SPOELBAK = dict(b=500, d=400, h=200, r=55, r_bodem=45, flens=19.5, afvoer_y=25, midden_vanaf_muur=329)   # 2 cm naar voren t.o.v. BMN (309), voor lucht rond de kraan
# Kraan: Quooker Classic Fusion Square (maten uit de Quooker-maattekening, mm):
# hoogte 291, uitloop 220 (hart tot hart), uitloopopening op 214, buis Ø23, voet Ø50, hendel ±70 opzij.
# hart_vanaf_muur = hart van de voet, gemeten vanaf de muur (achter de tegels).
KRAAN = dict(hart_vanaf_muur=59, hoogte=291, uitloop=220, opening=214, buis=23, voet=50, hendel=70, draai=0)
# Uitsparing in de vensterbank boven de spoelbak, zodat de kraan vrij staat en te bedienen is:
# vanaf de buitenranden van de spoelbak loopt de voorkant geleidelijk terug ("overgang" = deel van de
# spoelbakbreedte per kant); in het midden ligt de voorkant "voor_tegels" mm voor de tegels
# (0 = terug tot de voorkant van het kozijn). In de raamopening blijft de plank op volle diepte.
# None = geen uitsparing.
UITSPARING = dict(overgang=1 / 3, voor_tegels=0)

# Glazen theepot op de vensterbank (positie = midden, x vanaf Muur 4, y vanaf Muur 5; mm). None = weglaten.
THEEPOT = dict(positie=(470, 10), diameter=150, hoogte=135)

# Oude radiator op Muur 4 (staat er nu; zet op False om weg te laten)
RADIATOR = True

# Limoengroen rolgordijn in de raamopening (in de dag, voor het kozijn), zoals fotos/rolgordijn:
# open rol stof op witte steunen, geen cassette. Kleur gemeten (sRGB) op die foto's: opgerold
# olijfachtig, uitgerold met tegenlicht lichter limoengroen.
# omlaag = hoe ver hij uitgerold is (0 = helemaal op, 1 = helemaal dicht). Zet op None om weg te laten.
# tegenlicht = gloed van het daglicht dat door de stof valt (het uitzicht is een foto, geen lichtbron).
ROLGORDIJN = dict(kleur=(0.58, 0.62, 0.22), omlaag=0.30, doorschijnend=0.40, tegenlicht=0.15)

# Koffiezetapparaat (Russell Hobbs filter, zoals nu) in de hoek Muur 4 / Muur 5.
# positie = midden van de voet in mm (x vanaf Muur 4, y vanaf Muur 5), draai in graden.
# Zet op None om weg te laten.
KOFFIEZET = dict(positie=(140, -230), draai=10)   # voor de vensterbank langs

# Aankleding Muur 4 onder de radiator, zoals nu: doeken aan haakjes en de twee
# wandafvalbakjes (Brabantia Sort & Go). y = afstand vanaf Muur 5 (negatief), z = hoogte, in mm.
# Zet op None om weg te laten.
AANKLEDING = dict(
    # doeken hangen aan een lusje midden op de korte kant; de plooien komen uit een stofsimulatie
    doeken=[
        dict(naam="Handdoek", y=-800, z=1270, b=400, l=560, dikte=5, kleur=(0.86, 0.87, 0.84), streep=(0.62, 0.74, 0.66)),
        dict(naam="Theedoek", y=-1060, z=1270, b=450, l=500, dikte=2, kleur=(0.52, 0.66, 0.24), streep=(0.44, 0.57, 0.19)),
    ],
    # y = midden van de bak, b x d x h = breedte langs de muur, diepte van de muur af, hoogte; z = onderkant.
    # Gemeten: 65 cm van de onderkasten (voorkant op y = -585) tot het groene bakje, beide 18 cm breed,
    # blauw 36 cm hoog, groen 18 cm. Bovenkanten gelijk op 68 cm boven de vloer.
    afvalbakken=[
        dict(naam="Afvalbak groen", y=-585 - 650 - 90, z=680 - 180, b=180, d=230, h=180, kleur=(0.22, 0.36, 0.31)),
        dict(naam="Afvalbak blauw", y=-585 - 650 - 180 - 10 - 90, z=680 - 360, b=180, d=250, h=360, kleur=(0.50, 0.71, 0.77)),
    ],
)

# Werkblad: Dekker TopCore "Sparrow". Paneelfoto (4150 x 1500 mm) voor kleur en vlekken,
# monsterfoto (300 x 200 mm) als fijne korrel eroverheen.
WERKBLAD = dict(
    paneel="//blad/Z1-629-SPARROW-01-V0760-054-TopCore-Sparrow-panel-4150-x-1500-mm-_1.jpg",
    paneel_mm=(4150, 1500),
    detail="//textures/sparrow_detail.png",   # hoogdoorlaat van de monsterfoto
    detail_mm=(300, 200),
    detail_sterkte=0.7,
)

UITZICHT_FOTO = "//textures/uitzicht.jpg"   # relatief t.o.v. Keuken.blend
UITZICHT_AFSTAND = 1200   # foto-vlak, gemeten vanaf de buitenkant van Muur 5
UITZICHT_BREEDTE = 4200

# Tegels op de kookplaatwand (Muur 6), tussen werkblad en bovenkasten.
# Liggend 120 x 60 cm, vanaf de hoek met Muur 5; het restant komt rechts bij Muur 7.
# Dezelfde tegel herhaalt zich; het bladpatroon loopt over de voeg door.
TEGEL = dict(b=1200, h=600, voeg=2, foto="//textures/tegel_bladeren_zonder_label.jpg")   # prijskaartje rechtsboven weggeretoucheerd

# Staafjesmozaiek (2 x 15 cm, matten van 30 x 30 cm) op Muur 4, Muur 5 en Muur 7,
# tot de onderkant van de bovenkasten. Kleuren gemiddeld uit de twee mozaiekfoto's.
MOZAIEK = dict(
    staaf_b=20, staaf_h=150, voeg=2,
    licht=(0.68, 0.75, 0.74),
    midden=(0.56, 0.63, 0.62),
    rand=(0.20, 0.25, 0.27),     # donkerder glazuur langs de randjes
    voegkleur=(0.86, 0.82, 0.76),
    tot=1542,                    # bovenkant in mm (= onderkant bovenkasten)
)
MOZAIEK_DIKTE = 0.008         # tegel + lijm, in meters

# =====================================================================
# Hieronder hoef je normaal niets aan te passen
# =====================================================================

M = 0.001  # mm -> m

def lin(c):
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


# ---------- collecties ----------

def get_coll(name, parent):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if c.name not in parent.children:
        parent.children.link(c)
    return c


def clear_keuken():
    root = bpy.data.collections.get("Keuken")
    if root is None:
        return
    def all_colls(c):
        yield c
        for ch in c.children:
            yield from all_colls(ch)
    for c in list(all_colls(root)):
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras):
        for b in list(blocks):
            if b.users == 0:
                blocks.remove(b)


# ---------- materialen ----------

MATS = {}

def principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")

def make_mat(name, color, rough=0.5, metal=0.0, alpha=1.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
            nt.nodes.remove(n)
    bsdf = principled(mat)
    bsdf.inputs["Base Color"].default_value = lin(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Alpha"].default_value = alpha
    mat.diffuse_color = lin(color)
    MATS[name] = mat
    return mat

def make_materials():
    make_mat("Front", KLEUREN["Front"], rough=0.35)
    make_mat("Korpus", KLEUREN["Korpus"], rough=0.5)
    make_mat("Muur", KLEUREN["Muur"], rough=0.9)
    make_mat("Muur accent", KLEUREN["Muur accent"], rough=0.9)
    make_mat("Plafond", KLEUREN["Plafond"], rough=0.9)
    make_mat("Kozijn", KLEUREN["Kozijn"], rough=0.4)
    make_mat("RVS", (0.62, 0.62, 0.61), rough=0.3, metal=1.0)
    make_mat("Greep", KLEUREN["Greep"], rough=0.28, metal=0.5)   # zwart geanodiseerd aluminium, zijdeglans
    make_mat("Quooker rood", (0.78, 0.06, 0.12), rough=0.3)
    tg = make_mat("Theepot glas", (0.92, 0.95, 0.95), rough=0.02, alpha=0.22)
    if hasattr(tg, "surface_render_method"):
        tg.surface_render_method = "BLENDED"
    thee = make_mat("Thee", (0.55, 0.20, 0.05), rough=0.05, alpha=0.8)
    if hasattr(thee, "surface_render_method"):
        thee.surface_render_method = "BLENDED"
    vb = make_mat("Vensterbank", KLEUREN["Kozijn"], rough=0.45)   # wit gelakt hout met fijne nerf (fotos/kozijn)
    nt = vb.node_tree
    nerf = nt.nodes.new("ShaderNodeTexNoise")
    nerf.inputs["Detail"].default_value = 6.0
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (8.0, 400.0, 400.0)       # lange vezels langs de plank (x)
    co = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nerf.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(nerf.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], principled(vb).inputs["Normal"])
    kartel = make_mat("RVS kartel", (0.62, 0.62, 0.61), rough=0.35, metal=1.0)
    nt = kartel.node_tree
    golf = nt.nodes.new("ShaderNodeTexWave")
    golf.wave_type = "BANDS"
    golf.bands_direction = "X"
    golf.inputs["Scale"].default_value = 160.0               # fijne staande ribbels (kartel)
    co = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(co.outputs["Object"], golf.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(golf.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], principled(kartel).inputs["Normal"])
    make_mat("RVS spoelbak", (0.78, 0.77, 0.75), rough=0.32, metal=0.55)   # half metallic: diepe bak spiegelt anders zwart
    make_mat("Zwart glas", (0.01, 0.01, 0.01), rough=0.05)
    g = make_mat("Glas", (0.95, 0.97, 0.97), rough=0.0, alpha=0.08)
    if hasattr(g, "surface_render_method"):
        g.surface_render_method = "BLENDED"
    make_mat("Radiator", (0.93, 0.92, 0.88), rough=0.4)
    if ROLGORDIJN:
        rg = make_mat("Rolgordijn", ROLGORDIJN["kleur"], rough=0.9)
        nt = rg.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
        tr.inputs["Color"].default_value = lin(ROLGORDIJN["kleur"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs["Fac"].default_value = ROLGORDIJN["doorschijnend"]
        nt.links.new(principled(rg).outputs["BSDF"], mx.inputs[1])
        nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
        gloed = nt.nodes.new("ShaderNodeEmission")
        gloed.inputs["Color"].default_value = lin(ROLGORDIJN["kleur"])
        gloed.inputs["Strength"].default_value = ROLGORDIJN["tegenlicht"]
        som = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(mx.outputs["Shader"], som.inputs[0])
        nt.links.new(gloed.outputs["Emission"], som.inputs[1])
        nt.links.new(som.outputs["Shader"], out.inputs["Surface"])
        weefsel = nt.nodes.new("ShaderNodeTexWave")
        weefsel.wave_type = "BANDS"
        weefsel.bands_direction = "Z"
        weefsel.inputs["Scale"].default_value = 400.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.08
        nt.links.new(weefsel.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], principled(rg).inputs["Normal"])
    make_mat("Zwart kunststof", (0.03, 0.03, 0.03), rough=0.35)
    make_mat("Wit kunststof", (0.92, 0.92, 0.90), rough=0.4)
    make_mat("Koffie", (0.06, 0.03, 0.015), rough=0.1)
    lens = make_mat("Spot lens", (1.0, 0.9, 0.8), rough=0.3)
    bsdf = principled(lens)
    bsdf.inputs["Emission Color"].default_value = WARM_LICHT + (1.0,)
    bsdf.inputs["Emission Strength"].default_value = 8.0

    make_mozaiek_mat()

    t = make_mat("Tegel", (0.6, 0.55, 0.48), rough=0.45)
    nt = t.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.extension = "EXTEND"
    try:
        tex.image = bpy.data.images.load(TEGEL["foto"], check_existing=True)
        tex.image.reload()
        nt.links.new(tex.outputs["Color"], principled(t).inputs["Base Color"])
    except RuntimeError as e:
        print("Tegelfoto niet gevonden:", e)

    # Werkblad: foto's van Dekker op (x, y - z) in objectruimte: bovenblad gewoon plat,
    # en op de voor- en kopse kanten loopt het patroon met de hoogte mee in plaats van te strepen
    w = make_mat("Werkblad", (0.50, 0.48, 0.44), rough=0.55)
    nt = w.node_tree
    bsdf = principled(w)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    ymz = nt.nodes.new("ShaderNodeMath")
    ymz.operation = "SUBTRACT"
    nt.links.new(sep.outputs["Y"], ymz.inputs[0])
    nt.links.new(sep.outputs["Z"], ymz.inputs[1])
    vec = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], vec.inputs["X"])
    nt.links.new(ymz.outputs[0], vec.inputs["Y"])

    def foto(pad, mm, kleur=True):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / (mm[0] * M), 1 / (mm[1] * M), 1 / (mm[1] * M))
        nt.links.new(vec.outputs[0], mp.inputs["Vector"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        try:
            tex.image = bpy.data.images.load(pad, check_existing=True)
            tex.image.reload()
            if not kleur:
                tex.image.colorspace_settings.is_data = True
        except RuntimeError as e:
            print("Werkbladfoto niet gevonden:", e)
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        return tex.outputs["Color"]

    kleur = foto(WERKBLAD["paneel"], WERKBLAD["paneel_mm"])
    korrel = foto(WERKBLAD["detail"], WERKBLAD["detail_mm"], kleur=False)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "LINEAR_LIGHT"
    mix.inputs["Factor"].default_value = WERKBLAD["detail_sterkte"]
    nt.links.new(kleur, mix.inputs["A"])
    nt.links.new(korrel, mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.0003
    nt.links.new(korrel, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # Vloer: planken (brick texture) met houtnerf (ruis, uitgerekt langs de plank), per plank verschoven
    f = make_mat("Vloer", VLOER["midden"], rough=0.5)
    nt = f.node_tree
    bsdf = principled(f)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0, 0, math.radians(-VLOER["richting"]))
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.37
    # Color1/Color2: per plank een willekeurige tint tussen deze twee
    brick.inputs["Color1"].default_value = lin(tuple(v * 0.92 for v in VLOER["midden"]))
    brick.inputs["Color2"].default_value = lin(tuple(min(1, v * 1.08) for v in VLOER["midden"]))
    brick.inputs["Mortar"].default_value = (0, 0, 0, 1)
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.0012
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Brick Width"].default_value = VLOER["plank_lengte"] * M
    brick.inputs["Row Height"].default_value = VLOER["plank_breedte"] * M
    nt.links.new(mapping.outputs["Vector"], brick.inputs["Vector"])

    shift = nt.nodes.new("ShaderNodeVectorMath")
    shift.operation = "SCALE"
    shift.inputs["Scale"].default_value = 41.0
    nt.links.new(brick.outputs["Color"], shift.inputs[0])
    plankco = nt.nodes.new("ShaderNodeVectorMath")
    plankco.operation = "ADD"
    nt.links.new(mapping.outputs["Vector"], plankco.inputs[0])
    nt.links.new(shift.outputs["Vector"], plankco.inputs[1])

    def ruis(schaal, detail, rough):
        mul = nt.nodes.new("ShaderNodeVectorMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = schaal
        nt.links.new(plankco.outputs["Vector"], mul.inputs[0])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = detail
        nz.inputs["Roughness"].default_value = rough
        nt.links.new(mul.outputs["Vector"], nz.inputs["Vector"])
        return nz
    vezel = ruis((1.5, 60.0, 1.0), 8.0, 0.6)    # fijne vezels langs de plank
    vlam = ruis((0.6, 7.0, 1.0), 3.0, 0.5)      # grotere nerfvlammen
    som = nt.nodes.new("ShaderNodeMath")
    som.operation = "MULTIPLY_ADD"
    som.inputs[1].default_value = 0.55
    nt.links.new(vlam.outputs["Fac"], som.inputs[0])
    nt.links.new(vezel.outputs["Fac"], som.inputs[2])
    som2 = nt.nodes.new("ShaderNodeMath")
    som2.operation = "MULTIPLY_ADD"
    som2.inputs[1].default_value = 0.6
    som2.inputs[2].default_value = 0.0
    nt.links.new(som.outputs["Value"], som2.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = lin(VLOER["donker"])
    ramp.color_ramp.elements[1].position = 0.66
    ramp.color_ramp.elements[1].color = lin(VLOER["licht"])
    nt.links.new(som2.outputs["Value"], ramp.inputs["Fac"])

    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MIX"
    tint.inputs["Factor"].default_value = 0.35
    nt.links.new(ramp.outputs["Color"], tint.inputs["A"])
    nt.links.new(brick.outputs["Color"], tint.inputs["B"])
    voeg = nt.nodes.new("ShaderNodeMix")
    voeg.data_type = "RGBA"
    voeg.inputs["B"].default_value = lin(VLOER["voeg"])
    nt.links.new(brick.outputs["Fac"], voeg.inputs["Factor"])
    nt.links.new(tint.outputs["Result"], voeg.inputs["A"])
    nt.links.new(voeg.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.0005
    bump.invert = True   # voegen liggen iets lager
    nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # Uitzicht: foto als lichtgevend vlak achter het raam
    u = bpy.data.materials.get("Uitzicht") or bpy.data.materials.new("Uitzicht")
    u.use_nodes = True
    nt = u.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    try:
        tex.image = bpy.data.images.load(UITZICHT_FOTO, check_existing=True)
        tex.image.reload()
    except RuntimeError as e:
        print("Uitzicht-foto niet gevonden:", e)
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    MATS["Uitzicht"] = u


def make_mozaiek_mat():
    """Glanzende staafjestegels met donkere randjes en voegen, uitgerekend op UV in meters."""
    Z = MOZAIEK
    mat = make_mat("Mozaiek", Z["midden"], rough=0.06)
    nt = mat.node_tree
    bsdf = principled(mat)

    def m(op, a, b=0.0, c=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, val in enumerate((a, b) if c is None else (a, b, c)):
            if isinstance(val, (int, float)):
                n.inputs[i].default_value = val
            else:
                nt.links.new(val, n.inputs[i])
        return n.outputs[0]

    def mix(fac, a, b, blend="MIX"):
        n = nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        for name, val in (("Factor", fac), ("A", a), ("B", b)):
            if isinstance(val, tuple):
                n.inputs[name].default_value = val
            elif isinstance(val, (int, float)):
                n.inputs[name].default_value = val
            else:
                nt.links.new(val, n.inputs[name])
        return n.outputs["Result"]

    pitch, row, g = (Z["staaf_b"] + Z["voeg"]) * M, (Z["staaf_h"] + Z["voeg"]) * M, Z["voeg"] * M
    uv = nt.nodes.new("ShaderNodeTexCoord").outputs["UV"]
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv, sep.inputs[0])
    u, v = sep.outputs["X"], sep.outputs["Y"]

    def rand_afstand(c, p):   # afstand tot de rand van het staafje (negatief = in de voeg)
        cc = m("MULTIPLY", m("FRACT", m("DIVIDE", c, p)), p)
        return m("SUBTRACT", m("MINIMUM", cc, m("SUBTRACT", p, cc)), g / 2)
    d = m("MINIMUM", rand_afstand(u, pitch), rand_afstand(v, row))
    rand = m("SUBTRACT", 1.0, m("DIVIDE", d, 0.004), clamp=True)
    voeg = m("LESS_THAN", d, 0.0)

    # per staafje een eigen tint
    cel = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(m("FLOOR", m("DIVIDE", u, pitch)), cel.inputs["X"])
    nt.links.new(m("FLOOR", m("DIVIDE", v, row)), cel.inputs["Y"])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    nt.links.new(cel.outputs[0], wn.inputs["Vector"])
    kleur = mix(wn.outputs["Value"], lin(Z["midden"]), lin(Z["licht"]))
    # glazuur-vlekjes
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 250.0
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(uv, nz.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(kleur, hsv.inputs["Color"])
    nt.links.new(m("MULTIPLY_ADD", nz.outputs["Fac"], 0.2, 0.9), hsv.inputs["Value"])
    kleur = mix(m("MULTIPLY", m("POWER", rand, 1.5), 0.85), hsv.outputs["Color"], lin(Z["rand"]))
    kleur = mix(voeg, kleur, lin(Z["voegkleur"]))
    nt.links.new(kleur, bsdf.inputs["Base Color"])
    nt.links.new(m("MULTIPLY_ADD", voeg, 0.79, 0.06), bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.0015
    nt.links.new(m("DIVIDE", d, 0.003, clamp=True), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


# ---------- objecten ----------

def new_obj(name, data, coll, parent=None, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, data)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    return ob

def empty(name, coll, parent=None, loc=(0, 0, 0), rot_z=0.0, props=None):
    ob = new_obj(name, None, coll, parent, loc)
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = 0.05
    ob.rotation_euler.z = rot_z
    for k, v in (props or {}).items():
        ob[k] = v
    return ob

def box(name, x0, y0, z0, x1, y1, z1, mat, coll, parent=None, bevel=0.0):
    """Doos tussen twee hoekpunten (in meters, in de ruimte van parent). Oorsprong op het minimum-hoekpunt."""
    lo = Vector((min(x0, x1), min(y0, y1), min(z0, z1)))
    hi = Vector((max(x0, x1), max(y0, y1), max(z0, z1)))
    size = hi - lo
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((v.co.x + 0.5) * size.x, (v.co.y + 0.5) * size.y, (v.co.z + 0.5) * size.z))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat] if isinstance(mat, str) else mat)
    ob = new_obj(name, me, coll, parent, lo)
    if bevel > 0:
        mod = ob.modifiers.new("Afronding", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return ob

def cylinder(name, r, depth, loc, mat, coll, parent=None, axis="Z"):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=depth)
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    return new_obj(name, me, coll, parent, loc)

def boolean_solver_exact(mod):
    items = [i.identifier for i in mod.bl_rna.properties["solver"].enum_items]
    for s in ("EXACT", "MANIFOLD"):
        if s in items:
            mod.solver = s
            return

def hide_helper(ob):
    ob.display_type = "WIRE"
    ob.hide_render = True
    ob.visible_camera = False
    ob.visible_shadow = False
    try:
        ob.hide_set(True)
    except RuntimeError:
        pass


# ---------- kasten ----------

FD = FRONT_DIKTE * M
GAP = NAAD * M

# Doorsnede van de greeplijst (zoals kasten/greep.WEBP): (f, z) in meters, f = afstand voor het
# front (negatief = over de bovenrand naar achteren), z = hoogte t.o.v. de rand. Een kap op de rand,
# een lip die naar voren krult en omlaag hangt, en een been tegen het front: samen een vingergleuf.
GREEP_PROFIEL = [
    (-0.019, 0.000), (-0.019, 0.003), (0.006, 0.003), (0.013, 0.0015), (0.018, -0.003),
    (0.0205, -0.009), (0.021, -0.016), (0.018, -0.0165), (0.0175, -0.010), (0.015, -0.0055),
    (0.010, -0.0025), (0.0015, -0.0015), (0.0015, -0.024), (0.0, -0.024), (0.0, 0.0),
]
GREEP_AFLOOP = 0.035   # lengte waarover de lip aan de uiteinden terugloopt naar het front

def greeplijst(name, x0, x1, z_rand, boven, y_back, coll, parent):
    """Zwarte greeplijst op de boven- of onderrand van een front (J-profiel, aflopende uiteinden)."""
    length = max(0.10, (x1 - x0) - 0.10)
    xm = (x0 + x1) / 2
    xa = xm - length / 2
    yf = y_back - FD
    sgn = 1 if boven else -1   # profiel spiegelen voor de onderrand
    # plakjes langs de lengte, dichter bij de uiteinden voor de ronde afloop
    ts = sorted(set([i / 12 * GREEP_AFLOOP for i in range(13)] + [length - i / 12 * GREEP_AFLOOP for i in range(13)]))
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    ringen = []
    for t in ts:
        a = min(t, length - t) / GREEP_AFLOOP
        k = math.sin(min(1.0, a) * math.pi / 2)    # 0 aan het uiteinde, 1 in het midden
        ring = []
        for f, z in GREEP_PROFIEL:
            if f > 0.0015:
                f = 0.0015 + (f - 0.0015) * k
                z = z * (0.3 + 0.7 * k) if z < 0 else z
            ring.append(bm.verts.new((xa + t, yf - f, z_rand + sgn * z)))
        ringen.append(ring)
    n = len(GREEP_PROFIEL)
    for r0, r1 in zip(ringen, ringen[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(ringen[0])))
    bm.faces.new(ringen[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS["Greep"])
    ob = new_obj(name, me, coll, parent)
    for poly in me.polygons:
        poly.use_smooth = False
    return ob

def handle(name, x0, x1, z, coll, parent, y_front):
    """Horizontale RVS-greep (voor de oven)."""
    length = max(0.08, (x1 - x0) - 0.06)
    xm = (x0 + x1) / 2
    box(name, xm - length / 2, y_front - 0.022, z - 0.006, xm + length / 2, y_front - 0.010, z + 0.006, "RVS", coll, parent)
    for xs in (xm - length / 2 + 0.01, xm + length / 2 - 0.02):
        box(name + " voet", xs, y_front - 0.012, z - 0.004, xs + 0.01, y_front, z + 0.004, "RVS", coll, parent)

def fronts_column(cab, coll, el, fx0, fx1, z_top, y_back):
    """Plaatst een kolom fronten (van boven naar beneden) tussen fx0 en fx1."""
    y_front = y_back - FD
    z = z_top
    for i, (kind, h_mm) in enumerate(el.get("fronts", [])):
        h = h_mm * M
        z0, z1 = z - h + GAP / 2, z - GAP / 2
        n = el.get("deuren", 1) if kind == "deur" else 1
        wpart = (fx1 - fx0) / n
        for j in range(n):
            x0 = fx0 + j * wpart + GAP / 2
            x1 = fx0 + (j + 1) * wpart - GAP / 2
            label = f"{el['naam']} - {kind} {i + 1}" + (f".{j + 1}" if n > 1 else "")
            if kind == "oven":
                oven(label, x0, x1, z0, z1, y_back, coll, cab)
                continue
            box(label, x0, y_back, z0, x1, y_front, z1, "Front", coll, cab, bevel=0.001)
            # greeplijst: bovenrand bij onderkasten, onderrand bij fronten die hoog hangen
            if el.get("greeploos"):
                pass
            elif (z0 + z1) / 2 > 1.2:
                greeplijst(label + " greep", x0, x1, z0, False, y_back, coll, cab)
            else:
                greeplijst(label + " greep", x0, x1, z1, True, y_back, coll, cab)
        z -= h

def oven(name, x0, x1, z0, z1, y_back, coll, parent):
    """Etna CM450RVS combi-magnetron (45 cm nis)."""
    yf = y_back - FD
    box(name + " RVS", x0, y_back, z0, x1, yf, z1, "RVS", coll, parent)
    box(name + " deur", x0 + 0.01, yf, z0 + 0.01, x1 - 0.01, yf - 0.004, z1 - 0.085, "Zwart glas", coll, parent)
    box(name + " display", x0 + 0.22, yf, z1 - 0.06, x1 - 0.22, yf - 0.003, z1 - 0.03, "Zwart glas", coll, parent)
    for xk in (x0 + 0.06, x1 - 0.06):
        cylinder(name + " knop", 0.016, 0.02, (xk, yf - 0.01, z1 - 0.045), "RVS", coll, parent, axis="Y")
    handle(name + " greep", x0 + 0.04, x1 - 0.04, z1 - 0.11, coll, parent, yf - 0.004)

def onderkast(el, x, run, coll):
    b = el["b"] * M
    D = ONDERKAST_DIEPTE * M
    kind = el.get("type", "kast")
    cab = empty(el["naam"], coll, run, (x, 0, 0), props={"breedte_mm": el["b"], "type": kind})
    z_bot, z_top = PLINT * M, (PLINT + ONDERKAST_H) * M
    px0 = (D - 0.066) if kind == "hoek" else 0.0
    box(el["naam"] + " plint", px0, -(D - 0.05), 0, b, -(D - 0.05) - 0.016, z_bot, "Front", coll, cab)
    if kind == "passtuk":
        box(el["naam"] + " korpus", 0, 0, z_bot, b, -D, z_top, "Korpus", coll, cab)
        box(el["naam"] + " front", 0, -D, z_bot, b, -D - FD, z_top, "Front", coll, cab, bevel=0.001)
        return cab
    if el.get("spoelbak"):
        # open van boven, zodat de spoelbak erin past: zijwanden tot boven, rest tot onder de bak
        t = 0.018
        box(el["naam"] + " korpus", 0, 0, z_bot, b, -D, z_top - 0.22, "Korpus", coll, cab)
        box(el["naam"] + " zijwand L", 0, 0, z_bot, t, -D, z_top, "Korpus", coll, cab)
        box(el["naam"] + " zijwand R", b - t, 0, z_bot, b, -D, z_top, "Korpus", coll, cab)
    else:
        box(el["naam"] + " korpus", 0, 0, z_bot, b, -D, z_top, "Korpus", coll, cab)
    if kind == "hoek":
        # deel langs Muur 5: eigen assenstelsel, 90 graden gedraaid, start bij b_muur5 uit de hoek
        b5 = el.get("b_muur5", el["b"]) * M
        l5 = b5 - D
        poot = empty(el["naam"] + " (deel Muur 5)", coll, cab, (0, -b5, 0), rot_z=math.pi / 2)
        box(el["naam"] + " korpus Muur 5", 0, 0, z_bot, l5, -D, z_top, "Korpus", coll, poot)
        box(el["naam"] + " plint Muur 5", 0, -(D - 0.05), 0, l5 + 0.05, -(D - 0.05) - 0.016, z_bot, "Front", coll, poot)
        fronts_column(poot, coll, dict(el, naam=el["naam"] + " Muur 5"), 0.0, l5 + GAP / 2, z_top, -D)
        fronts_column(cab, coll, el, D + FD - GAP / 2, b, z_top, -D)
        return cab
    fronts_column(cab, coll, el, 0.0, b, z_top, -D)
    return cab

def spotlicht(name, power, size_deg, blend):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy = power
    ld.spot_size = math.radians(size_deg)
    ld.spot_blend = blend
    ld.shadow_soft_size = 0.015
    ld.color = WARM_LICHT
    return ld

def inbouwspot(name, x, y, z, coll, parent):
    """Ronde inbouwspot in de bodem van een bovenkast, schijnt naar beneden."""
    lens = cylinder(name + " lens", 0.025, 0.003, (x, y, z - 0.0015), "Spot lens", coll, parent)
    lens.visible_shadow = False
    new_obj(name, spotlicht(name, SPOT_ONDER_BOVENKAST_W, 110, 0.6), coll, parent, (x, y, z - 0.004))

def bovenkast(el, x, run, coll):
    b = el["b"] * M
    D = BOVENKAST_DIEPTE * M
    kind = el.get("type", "kast")
    cab = empty(el["naam"], coll, run, (x, 0, 0), props={"breedte_mm": el["b"], "type": kind})
    z0, z1 = BOVENKAST_ONDERKANT * M, (BOVENKAST_ONDERKANT + BOVENKAST_H) * M
    if kind == "passtuk":
        box(el["naam"] + " front", 0, 0, z0, b, -D - FD, z1, "Front", coll, cab, bevel=0.001)
        return cab
    box(el["naam"] + " korpus", 0, 0, z0, b, -D, z1, "Korpus", coll, cab)
    e = dict(el)
    e.setdefault("fronts", [("deur", BOVENKAST_H)])
    e["greeploos"] = not BOVENKAST_GREPEN
    fronts_column(cab, coll, e, 0.0, b, z1, -D)
    if el.get("afzuigkap"):
        w = 0.53
        box(el["naam"] + " afzuigkap", (b - w) / 2, -0.02, z0 - 0.015, (b + w) / 2, -0.30, z0, "RVS", coll, cab)
    elif SPOT_ONDER_BOVENKAST_W > 0:
        inbouwspot(el["naam"] + " spot", b / 2, -D * 0.6, z0, coll, cab)
    return cab

def hoge_kast(el, x, run, coll):
    b = el["b"] * M
    D = ONDERKAST_DIEPTE * M
    kind = el.get("type", "hoog")
    cab = empty(el["naam"], coll, run, (x, 0, 0), props={"breedte_mm": el["b"], "type": kind})
    z_bot, z_top = PLINT * M, (PLINT + HOGEKAST_H) * M
    if kind == "open":
        if el.get("tot_plafond"):
            z_bot, z_top = 0.0, PLAFOND * M
        else:
            box(el["naam"] + " plint", 0, -(D - 0.05), 0, b, -(D - 0.05) - 0.016, z_bot, "Front", coll, cab)
        dd = el.get("diepte", ONDERKAST_DIEPTE + FRONT_DIKTE) * M
        t = 0.018
        box(el["naam"] + " achterwand", 0, 0, z_bot, b, -0.01, z_top, "Korpus", coll, cab)
        box(el["naam"] + " zijkant L", 0, 0, z_bot, t, -dd, z_top, "Front", coll, cab, bevel=0.001)
        box(el["naam"] + " zijkant R", b - t, 0, z_bot, b, -dd, z_top, "Front", coll, cab, bevel=0.001)
        n = el.get("planken", 5)
        for i in range(n + 1):
            zp = z_bot + i * (z_top - z_bot - t) / n
            box(f"{el['naam']} plank {i}", t, -0.01, zp, b - t, -dd, zp + t, "Front", coll, cab, bevel=0.001)
        return cab
    box(el["naam"] + " plint", 0, -(D - 0.05), 0, b, -(D - 0.05) - 0.016, z_bot, "Front", coll, cab)
    kb = b - 0.002 if el.get("zijbekleding") else b
    box(el["naam"] + " korpus", 0, 0, z_bot, kb, -D, z_top, "Korpus", coll, cab)
    if el.get("zijbekleding"):   # zijdebekleding in frontkleur aan de kant van de open kast
        box(el["naam"] + " zijdebekleding", kb, 0, 0, b, -D - FD, z_top, "Front", coll, cab)
    fronts_column(cab, coll, el, 0.0, b, z_top, -D)
    return cab

def kast_rij(name, coll, origin, rot_z, items, builder):
    run = empty(name, coll, None, origin, rot_z)
    x = 0.0
    placed = []
    for el in items:
        placed.append((builder(el, x, run, coll), x, el))
        x += el["b"] * M
    return run, placed, x


# ---------- ruimte ----------

def bouw_ruimte(coll, hulp):
    R = {k: v * M if isinstance(v, (int, float)) else v for k, v in RUIMTE.items()}
    H = PLAFOND * M
    t = R["muur_dikte"]
    L5, L6, L4 = R["muur5_lengte"], R["muur6_lengte"], R["muur4_lengte"]
    x2 = -R["muur3_lengte"]                # vlak van Muur 2
    y1 = -(L4 + R["muur2_lengte"])          # vlak van Muur 1
    xo = x2 - t                             # buitenkant links

    # Muur 5 met raamopening (boolean)
    m5 = box("Muur 5 (raam)", xo, 0, 0, L5 + t, R["muur5_dikte"], H, "Muur accent", coll)
    raam = empty("Raam", coll, None, (R["raam_van"], 0, R["raam_onder"]))
    W, Hr = R["raam_breedte"], R["raam_boven"] - R["raam_onder"]
    cutter = box("Raamopening (hulp)", 0, -0.05, 0, W, R["muur5_dikte"] + 0.05, Hr, "Muur", hulp, raam)
    hide_helper(cutter)
    mod = m5.modifiers.new("Raamopening", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    boolean_solver_exact(mod)

    # Kozijn
    p, yk0, yk1 = 0.055, 0.10, 0.17
    box("Kozijn onder", 0, yk0, 0, W, yk1, p, "Kozijn", coll, raam)
    box("Kozijn boven", 0, yk0, Hr - p, W, yk1, Hr, "Kozijn", coll, raam)
    box("Kozijn links", 0, yk0, 0, p, yk1, Hr, "Kozijn", coll, raam)
    box("Kozijn rechts", W - p, yk0, 0, W, yk1, Hr, "Kozijn", coll, raam)
    xm = W - R["raam_rechterdeel"]
    box("Kozijn middenstijl", xm - p / 2, yk0, 0, xm + p / 2, yk1, Hr, "Kozijn", coll, raam)
    zt = Hr - R["raam_bovenlicht"]
    box("Kozijn tussendorpel", xm, yk0, zt - p / 2, W, yk1, zt + p / 2, "Kozijn", coll, raam)
    s = 0.045  # draaikiepraam-vleugel
    box("Vleugel onder", xm + p / 2, yk0 - 0.01, p, W - p, yk0 + 0.04, p + s, "Kozijn", coll, raam)
    box("Vleugel boven", xm + p / 2, yk0 - 0.01, zt - p / 2 - s, W - p, yk0 + 0.04, zt - p / 2, "Kozijn", coll, raam)
    box("Vleugel links", xm + p / 2, yk0 - 0.01, p, xm + p / 2 + s, yk0 + 0.04, zt - p / 2, "Kozijn", coll, raam)
    box("Vleugel rechts", W - p - s, yk0 - 0.01, p, W - p, yk0 + 0.04, zt - p / 2, "Kozijn", coll, raam)
    box("Raamkruk", xm + p / 2 + 0.012, yk0 - 0.035, (p + zt) / 2 - 0.06, xm + p / 2 + 0.03, yk0 - 0.01, (p + zt) / 2 + 0.06, "RVS", coll, raam)
    box("Glas", p, 0.134, p, W - p, 0.136, Hr - p, "Glas", coll, raam)
    # Houten binnenkozijn: bekleedt de dagkanten tot aan de muur, dus daar zit geen pleister/tegel
    bf = R["binnenframe"]
    box("Binnenkozijn links", 0, 0, 0, bf, yk0, Hr, "Kozijn", coll, raam)
    box("Binnenkozijn rechts", W - bf, 0, 0, W, yk0, Hr, "Kozijn", coll, raam)
    box("Binnenkozijn boven", 0, 0, Hr - bf, W, yk0, Hr, "Kozijn", coll, raam)

    # Losse vensterbankplank, op het binnenkozijn geschroefd (fotos/kozijn): steekt vensterbank_uitsteek
    # voor de tegels uit, links door tot Muur 4, rechts gelijk met de buitenkant van het binnenkozijn.
    # Bovenkant op de onderkant van het raam; eronder de witte onderdorpel-lat, dan pas de tegels.
    voor = -(MOZAIEK_DIKTE + R["vensterbank_uitsteek"])
    vd, dh = R["vensterbank_dikte"], R["onderdorpel_hoogte"]
    uitsp = None
    xm_spoel = spoelbak_midden_x()
    if UITSPARING and xm_spoel is not None:
        half = (SPOELBAK["b"] / 2 + SPOELBAK["flens"]) * M      # buitenrand van de spoelbak
        uitsp = (xm_spoel - half - R["raam_van"], xm_spoel + half - R["raam_van"],
                 -(MOZAIEK_DIKTE + UITSPARING["voor_tegels"] * M), UITSPARING["overgang"])
    me = vensterbank_mesh("Vensterbank", -R["raam_van"] + MOZAIEK_DIKTE, W, yk0, voor, vd, R["vensterbank_hoek"], uitsp)
    me.materials.append(MATS["Vensterbank"])
    vb = new_obj("Vensterbank", me, coll, raam)
    mod = vb.modifiers.new("Afronding", "BEVEL")
    mod.width, mod.segments, mod.limit_method = 0.002, 2, "ANGLE"
    box("Binnenkozijn onderdorpel", 0, -MOZAIEK_DIKTE, -vd - dh, W, yk0, -vd, "Kozijn", coll, raam)
    for xs in (0.11, W / 2, W - 0.11):        # schroefjes van boven
        cylinder("Vensterbank schroef", 0.0035, 0.0006, (xs, yk0 - 0.03, 0.0003), "RVS", coll, raam)

    if ROLGORDIJN:
        rg = empty("Rolgordijn", coll, raam)
        ri = R["binnenframe"]                    # steunen tegen het binnenkozijn
        lengte = (Hr - 0.07) * ROLGORDIJN["omlaag"]
        rr = 0.024                               # straal van de opgerolde stof
        yc, zc = 0.035, Hr - 0.012 - rr          # as van de rol, in de dag
        yr = yc + rr                             # doek komt aan de raamkant van de rol naar beneden
        K0 = zc
        for xs in (ri, W - ri - 0.012):          # witte steunen
            box("Rolgordijn steun", xs, yc - 0.03, zc - 0.03, xs + 0.012, yc + 0.03, Hr, "Kozijn", coll, rg, bevel=0.002)
        rol = cylinder("Rolgordijn rol", rr, W - 2 * ri - 0.03, (W / 2, yc, zc), "Rolgordijn", coll, rg)
        rol.rotation_euler.y = math.pi / 2
        for p in rol.data.polygons:
            p.use_smooth = True
        box("Rolgordijn doek", ri + 0.01, yr - 0.001, K0 - lengte, W - ri - 0.01, yr + 0.001, K0, "Rolgordijn", coll, rg)
        box("Rolgordijn onderlat", ri + 0.008, yr - 0.008, K0 - lengte - 0.02, W - ri - 0.008, yr + 0.006, K0 - lengte, "Rolgordijn", coll, rg, bevel=0.004)
        cylinder("Rolgordijn trekkoordje", 0.0015, 0.12, (W / 2, yr - 0.012, K0 - lengte - 0.08), "Kozijn", coll, rg)
        cylinder("Rolgordijn trekker", 0.008, 0.03, (W / 2, yr - 0.012, K0 - lengte - 0.15), "Kozijn", coll, rg)

    # Koof boven het raam
    box("Koof", 0, 0, H - R["koof_hoogte"], L5, -R["koof_diepte"], H, "Muur accent", coll)

    # Overige muren
    box("Muur 4 + 3", xo, -L4, 0, 0, 0, H, "Muur accent", coll)
    box("Muur 2", xo, y1, 0, x2, -L4, H, "Muur", coll)
    box("Muur 1 (verlengd)", xo, y1 - t, 0, x2 + R["muur1_lengte"], y1, H, "Muur", coll)
    box("Muur 6", L5, -L6 - t, 0, L5 + t, R["muur5_dikte"], H, "Muur", coll)
    box("Muur 7", L5 - R["muur7_lengte"], -L6 - t, 0, L5, -L6, H, "Muur", coll)

    # Vloer en plafond (lopen door naar de woonkamer)
    box("Vloer", xo - 1.0, -L6 - 2.0, -0.02, L5 + t, R["muur5_dikte"], 0, "Vloer", coll)
    box("Plafond", xo - 1.0, -L6 - 2.0, H, L5 + t, R["muur5_dikte"], H + 0.05, "Plafond", coll)

    # Uitzicht
    me = bpy.data.meshes.new("Uitzicht")
    bm = bmesh.new()
    tex = next((n for n in MATS["Uitzicht"].node_tree.nodes if n.type == "TEX_IMAGE"), None)
    im = tex.image if tex else None
    aspect = im.size[0] / im.size[1] if im and im.size[1] else 1.8
    wv = UITZICHT_BREEDTE * M
    hv = wv / aspect
    for v in [(-wv / 2, 0, -hv / 2), (wv / 2, 0, -hv / 2), (wv / 2, 0, hv / 2), (-wv / 2, 0, hv / 2)]:
        bm.verts.new(v)
    f = bm.faces.new(bm.verts)
    uv = bm.loops.layers.uv.new()
    for loop, co in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop[uv].uv = co
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS["Uitzicht"])
    u = new_obj("Uitzicht (foto)", me, coll, None, (R["raam_van"] + W / 2, R["muur5_dikte"] + UITZICHT_AFSTAND * M, 1.75))
    u.visible_shadow = False

    if RADIATOR:
        rad = empty("Radiator (bestaand)", coll, None, (0, -0.25, 1.62))
        box("Radiator paneel", 0.03, 0, 0, 0.10, -1.15, 0.62, "Radiator", coll, rad, bevel=0.004)
        for i in range(10):
            zl = 0.04 + i * 0.058
            box(f"Radiator lamel {i}", 0.10, -0.01, zl, 0.115, -1.14, zl + 0.035, "Radiator", coll, rad, bevel=0.003)

    return R


# ---------- keuken ----------

def bouw_keuken(R, c_onder, c_boven, c_hoog, c_blad, c_app, hulp):
    L5 = R["muur5_lengte"]
    D = ONDERKAST_DIEPTE * M
    var = VARIANTEN[VARIANT]

    run5, placed5, len5 = kast_rij("Onderkasten Muur 5", c_onder, (0, 0, 0), 0.0, ONDER_MUUR5, onderkast)
    run6, placed6, len6 = kast_rij("Onderkasten Muur 6", c_onder, (L5, 0, 0), -math.pi / 2, var["onder"], onderkast)
    kast_rij("Bovenkasten Muur 6", c_boven, (L5, 0, 0), -math.pi / 2, var["boven"], bovenkast)
    nis = (-R["muur3_lengte"], -(R["muur4_lengte"] + R["muur2_lengte"]), 0)
    kast_rij("Hoge kasten (nis Muur 2)", c_hoog, nis, math.pi / 2, HOGE_KASTEN, hoge_kast)

    zb0 = (PLINT + ONDERKAST_H) * M
    zb1 = zb0 + WERKBLAD_DIKTE * M
    WD = WERKBLAD_DIEPTE * M

    # Werkbladen
    blad5 = box("Werkblad Muur 5", 0, 0, zb0, L5, -WD, zb1, "Werkblad", c_blad, run5, bevel=0.002)
    box("Werkblad Muur 6", WD, 0, zb0, len6, -WD, zb1, "Werkblad", c_blad, run6, bevel=0.002)

    # Decortegels op Muur 6, staafjesmozaiek op Muur 4, 5 en 7
    zr = BOVENKAST_ONDERKANT * M
    bouw_tegels(run6, len6, zb1, zr, c_blad)
    bouw_mozaiek(R, zb1, c_blad)

    # Spoelbak + kraan op de spoelkast
    for cab, x, el in placed5:
        if el.get("spoelbak"):
            sb = empty("Spoelbak", c_app, run5, (x + el["b"] * M / 2, -SPOELBAK["midden_vanaf_muur"] * M, zb1))
            bouw_spoelbak(sb, blad5, c_app, hulp)

            # Kraan: Quooker Classic Fusion Square
            kr = empty("Kraan", c_app, run5, (x + el["b"] * M / 2, -KRAAN["hart_vanaf_muur"] * M, zb1),
                       rot_z=math.radians(KRAAN["draai"]))
            bouw_quooker(kr, c_app)

    # Kookplaat op de ovenkast
    for cab, x, el in placed6:
        if el.get("kookplaat"):
            kp = empty("Kookplaat (Etna KI159ZT)", c_app, run6, (x + el["b"] * M / 2, -0.30, zb1))
            box("Kookplaat glas", -0.295, -0.26, 0, 0.295, 0.26, 0.005, "Zwart glas", c_app, kp, bevel=0.002)


def doek_mat(naam, kleur, streep):
    """Katoen met strepen in de lengte (op UV)."""
    mat = make_mat(naam, kleur, rough=0.95)
    nt = mat.node_tree
    uv = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_profile = "SAW"
    wave.inputs["Scale"].default_value = 7.0
    nt.links.new(uv.outputs["UV"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = lin(kleur)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = lin(streep)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], principled(mat).inputs["Base Color"])
    weefsel = nt.nodes.new("ShaderNodeTexNoise")
    weefsel.inputs["Scale"].default_value = 900.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(weefsel.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], principled(mat).inputs["Normal"])
    return mat

def simuleer_doek(ob, frames=60):
    """Laat een doek met stofsimulatie uithangen en zet het resultaat vast als gewone mesh."""
    sc = bpy.context.scene
    cl = ob.modifiers.new("Stof", "CLOTH")
    st = cl.settings
    st.vertex_group_mass = "vast"
    st.quality = 8
    st.mass = 0.15
    st.air_damping = 3.0
    st.tension_stiffness = st.compression_stiffness = 15
    st.bending_stiffness = 0.2
    cl.collision_settings.use_collision = True
    cl.point_cache.frame_start, cl.point_cache.frame_end = 1, frames
    f0 = sc.frame_current
    for f in range(1, frames + 1):
        sc.frame_set(f)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    sc.frame_set(f0)
    oud = ob.data
    ob.modifiers.remove(cl)
    ob.data = me
    bpy.data.meshes.remove(oud)

def doek(el, coll, parent):
    """Doek aan een RVS-haakje, opgehangen aan een lusje midden op de bovenrand."""
    b, L = el["b"] * M, el["l"] * M
    haak = empty(el["naam"], coll, parent, (0.008, el["y"] * M, el["z"] * M))
    box(el["naam"] + " haakje plaat", 0, -0.012, -0.02, 0.006, 0.012, 0.02, "RVS", coll, haak, bevel=0.002)
    box(el["naam"] + " haakje", 0.006, -0.004, -0.004, 0.035, 0.004, 0.004, "RVS", coll, haak)
    box(el["naam"] + " haakje punt", 0.029, -0.004, 0.0, 0.035, 0.004, 0.015, "RVS", coll, haak)

    me = bpy.data.meshes.new(el["naam"])
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=24, y_segments=30, size=0.5, calc_uvs=True)
    for v in bm.verts:   # raster in het vlak van de muur, iets ervoor, bovenrand bij het haakje
        u, w = v.co.x, v.co.y
        v.co = Vector((0.03 + 0.004 * math.sin(u * 17 + w * 5), u * b, (w - 0.5) * L - 0.005))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(doek_mat(el["naam"], el["kleur"], el["streep"]))
    ob = new_obj(el["naam"] + " stof", me, coll, haak)
    vg = ob.vertex_groups.new(name="vast")
    vg.add([v.index for v in me.vertices if v.co.z > -0.01 and abs(v.co.y) < 0.02], 1.0, "REPLACE")

    # tijdelijke botsingsvlakken: de muur en het haakje
    wand = box(el["naam"] + " wand (hulp)", -0.03, -0.6, -1.0, 0.0, 0.6, 0.1, "Muur", coll, haak)
    wand.modifiers.new("Botsing", "COLLISION")
    simuleer_doek(ob)
    bpy.data.objects.remove(wand, do_unlink=True)

    ob.modifiers.new("Dikte", "SOLIDIFY").thickness = el.get("dikte", 2) * M
    ob.modifiers.new("Glad", "SUBSURF").levels = 1
    for p in ob.data.polygons:
        p.use_smooth = True

def afvalbak(el, coll, parent):
    """Brabantia Sort & Go-achtig wandbakje: wandbeugel, iets taps toelopende bak, deksel en hengsel."""
    b, d, h = el["b"] * M, el["d"] * M, el["h"] * M
    bak = empty(el["naam"], coll, parent, (0.008, el["y"] * M, el["z"] * M))
    mat = make_mat(el["naam"], el["kleur"], rough=0.45)
    hd = 0.045                                  # hoogte van het deksel
    box(el["naam"] + " beugel", 0, -b / 2 + 0.02, h * 0.35, 0.014, b / 2 - 0.02, h - hd - 0.01, "Wit kunststof", coll, bak, bevel=0.003)

    me = bpy.data.meshes.new(el["naam"] + " bak")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        boven = v.co.z > 0
        t = 1.0 if boven else 0.93              # onderkant iets smaller
        x = 0.014 + (v.co.x + 0.5) * (d - 0.014) * (1.0 if boven or v.co.x < 0 else 0.96)
        v.co = Vector((x, v.co.y * b * t, (v.co.z + 0.5) * (h - hd)))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    body = new_obj(el["naam"] + " bak", me, coll, bak)
    bev = body.modifiers.new("Afronding", "BEVEL")
    bev.width, bev.segments = 0.018, 4

    deksel = box(el["naam"] + " deksel", 0.010, -b / 2 - 0.005, h - hd - 0.004, d + 0.008, b / 2 + 0.005, h, mat, coll, bak)
    bev = deksel.modifiers.new("Afronding", "BEVEL")
    bev.width, bev.segments = 0.014, 3

    # hengsel: draaipunten op de zijkanten, beugel hangt schuin voor de bak langs naar beneden
    cu = bpy.data.curves.new(el["naam"] + " hengsel", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.006
    cu.bevel_resolution = 3
    sp = cu.splines.new("NURBS")
    yy = b / 2 + 0.008
    xp, zp = d * 0.45, h * 0.70
    xf, zf = d + 0.012, h * 0.32
    pts = [(xp, -yy, zp), (xp, -yy, zp), (xf, -yy, zf), (xf, -yy * 0.6, zf), (xf, yy * 0.6, zf), (xf, yy, zf), (xp, yy, zp), (xp, yy, zp)]
    sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts):
        pt.co = (*co, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 3
    cu.materials.append(MATS["Zwart kunststof"])
    new_obj(el["naam"] + " hengsel", cu, coll, bak)
    for zij in (-1, 1):
        cylinder(el["naam"] + " scharnier", 0.012, 0.006, (xp, zij * (b / 2 + 0.003), zp), "Zwart kunststof", coll, bak, axis="Y")

def bouw_aankleding(coll):
    groep = empty("Aankleding Muur 4", coll)
    for el in AANKLEDING["doeken"]:
        doek(el, coll, groep)
    for el in AANKLEDING["afvalbakken"]:
        afvalbak(el, coll, groep)

def spoelbak_midden_x():
    """x (m, vanaf Muur 4) van het midden van de spoelkast, uit de indeling van Muur 5."""
    x = 0.0
    for el in ONDER_MUUR5:
        if el.get("spoelbak"):
            return x + el["b"] / 2 * M
        x += el["b"] * M
    return None


def vensterbank_mesh(naam, x0, x1, y_achter, y_voor, dikte, hoek_r, uitsparing):
    """Plank als bovenaanzicht-profiel, geëxtrudeerd over de dikte (bovenkant op z = 0).
    uitsparing = (xa, xb, y_diep, overgang): voorkant loopt tussen xa en xb terug naar y_diep."""
    voor = []                                    # voorrand van links naar rechts (x, y)
    if uitsparing:
        xa, xb, yd, f = uitsparing
        lo = (xb - xa) * f
        voor.append((x0, y_voor))
        n = 24
        for i in range(n + 1):                   # links: geleidelijk terug (cosinus-overgang)
            t = i / n
            voor.append((xa + lo * t, y_voor + (yd - y_voor) * (1 - math.cos(math.pi * t)) / 2))
        for i in range(n + 1):                   # rechts: weer naar voren
            t = i / n
            voor.append((xb - lo + lo * t, yd + (y_voor - yd) * (1 - math.cos(math.pi * t)) / 2))
    else:
        voor.append((x0, y_voor))
    for i in range(9):                           # afgeronde hoek rechtsvoor
        a = math.radians(-90 + 90 * i / 8)
        voor.append((x1 - hoek_r + hoek_r * math.cos(a), y_voor + hoek_r + hoek_r * math.sin(a)))
    omtrek = voor + [(x1, y_achter), (x0, y_achter)]
    bm = bmesh.new()
    onder = [bm.verts.new((x, y, -dikte)) for x, y in omtrek]
    boven = [bm.verts.new((x, y, 0.0)) for x, y in omtrek]
    n = len(omtrek)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((onder[i], onder[j], boven[j], boven[i]))
    bm.faces.new(list(reversed(onder)))
    bm.faces.new(boven)
    # boven- en onderkant blijven n-gons; Blender's eigen opdeling kan met de holle vorm overweg
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(naam)
    bm.to_mesh(me)
    bm.free()
    return me


def bouw_theepot(coll):
    """Glazen theepot met thee, zwart handvat en deksel (zoals op fotos/rolgordijn)."""
    x, y = THEEPOT["positie"]
    d, h = THEEPOT["diameter"] * M, THEEPOT["hoogte"] * M
    z = RUIMTE["raam_onder"] * M
    tp = empty("Theepot", coll, None, (x * M, -y * M, z))
    me = bpy.data.meshes.new("Theepot glas")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * d * 0.9, v.co.y * d * 0.9, (v.co.z + 0.5) * h * 0.82))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > h * 0.78], context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS["Theepot glas"])
    glas = new_obj("Theepot glas", me, coll, tp)
    for p in me.polygons:
        p.use_smooth = True
    me = bpy.data.meshes.new("Theepot thee")   # thee tot ongeveer de helft: onderste deel van dezelfde bol
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * d * 0.86, v.co.y * d * 0.86, (v.co.z + 0.5) * h * 0.78 + 0.003))
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, h * 0.42),
                           plane_no=(0, 0, 1), clear_outer=True)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS["Thee"])
    new_obj("Theepot thee", me, coll, tp)
    cylinder("Theepot deksel", d * 0.24, 0.012, (0, 0, h * 0.82), "Zwart kunststof", coll, tp)
    cylinder("Theepot knop", 0.009, 0.014, (0, 0, h * 0.82 + 0.012), "Zwart kunststof", coll, tp)
    cylinder("Theepot voet", d * 0.30, 0.004, (0, 0, 0.002), "Zwart kunststof", coll, tp)
    cu = bpy.data.curves.new("Theepot handvat", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.006
    sp = cu.splines.new("NURBS")
    pts = [(d * 0.38, 0, h * 0.7), (d * 0.62, 0, h * 0.75), (d * 0.66, 0, h * 0.35), (d * 0.40, 0, h * 0.2)]
    sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts):
        pt.co = (*co, 1.0)
    sp.use_endpoint_u = True
    cu.materials.append(MATS["Zwart kunststof"])
    new_obj("Theepot handvat", cu, coll, tp)
    tuit = cylinder("Theepot tuit", 0.009, d * 0.32, (-d * 0.52, 0, h * 0.42), "Theepot glas", coll, tp)
    tuit.rotation_euler.y = math.radians(-50)
    tp.rotation_euler.z = math.radians(-20)


def bol_mesh(naam, r, loc, schaal, materiaal, coll, parent):
    me = bpy.data.meshes.new(naam)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * schaal[0], v.co.y * schaal[1], v.co.z * schaal[2]))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(materiaal)
    ob = new_obj(naam, me, coll, parent, loc)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def bouw_koffiezet(coll):
    """Filterkoffiezetapparaat: RVS voet en kop, zwarte watertank achter, glazen kan voor (-y)."""
    x, y = KOFFIEZET["positie"]
    z = (PLINT + ONDERKAST_H + WERKBLAD_DIKTE) * M
    k = empty("Koffiezetapparaat", coll, None, (x * M, y * M, z), rot_z=math.radians(KOFFIEZET["draai"]))
    box("Koffie voet", -0.11, -0.13, 0, 0.11, 0.12, 0.03, "RVS", coll, k, bevel=0.006)
    box("Koffie watertank", -0.105, 0.03, 0.03, 0.105, 0.12, 0.30, "Zwart kunststof", coll, k, bevel=0.01)
    cylinder("Koffie filterhouder", 0.088, 0.04, (0, -0.02, 0.235), "Zwart kunststof", coll, k)
    cylinder("Koffie kop", 0.105, 0.09, (0, -0.02, 0.30), "RVS", coll, k)
    cylinder("Koffie deksel", 0.098, 0.008, (0, -0.02, 0.349), "Zwart kunststof", coll, k)
    cylinder("Koffie kan", 0.072, 0.165, (0, -0.035, 0.1175), "Glas", coll, k)
    cylinder("Koffie in kan", 0.068, 0.05, (0, -0.035, 0.06), "Koffie", coll, k)
    cylinder("Koffie kan rand", 0.074, 0.035, (0, -0.035, 0.1825), "RVS", coll, k)
    box("Koffie kan greep", -0.012, -0.135, 0.07, 0.012, -0.112, 0.19, "RVS", coll, k, bevel=0.004)

def bouw_mozaiek(R, z_blad, coll):
    """Mozaiek als dunne platen (8 mm) op de muren; UV in meters zodat de staafjes op maat liggen."""
    t = MOZAIEK_DIKTE
    top = MOZAIEK["tot"] * M
    L5, L4, L6 = R["muur5_lengte"], R["muur4_lengte"], R["muur6_lengte"]
    x7 = L5 - R["muur7_lengte"]
    r0, r1 = R["raam_van"], R["raam_van"] + R["raam_breedte"]
    groep = empty("Mozaiek", coll)
    stukken = [
        # naam, hoekpunten, functie (x, y, z) -> u langs de muur
        ("Mozaiek Muur 4", (0, 0, 0, t, -L4, top), lambda x, y, z: -y),
        ("Mozaiek Muur 5 links van raam", (t, 0, z_blad, r0, -t, top), lambda x, y, z: x),
        ("Mozaiek Muur 5 onder raam", (r0, 0, z_blad, r1, -t, R["raam_onder"] - R["vensterbank_dikte"] - R["onderdorpel_hoogte"]), lambda x, y, z: x),
        ("Mozaiek Muur 5 rechts van raam", (r1, 0, z_blad, L5 - 0.009, -t, top), lambda x, y, z: x),
        ("Mozaiek Muur 7", (x7, -L6, 0, L5 - 0.009, -L6 + t, top), lambda x, y, z: L5 - x),
    ]
    for naam, (x0, y0, z0, x1, y1, z1), ufun in stukken:
        ob = box(naam, x0, y0, z0, x1, y1, z1, "Mozaiek", coll, groep)
        uv = ob.data.uv_layers.new(name="UVMap")
        for loop in ob.data.loops:
            co = ob.data.vertices[loop.vertex_index].co + ob.location
            uv.data[loop.index].uv = (ufun(co.x, co.y, co.z), co.z)

def bouw_quooker(kr, coll):
    """Quooker Classic Fusion Square: ronde kolom met kartelring en rood ringetje, hoekige uitloop
    met afgeronde bochten (naar -y, de spoelbak in) en de Classic-hendel opzij (+x)."""
    Q = {k: v * M for k, v in KRAAN.items() if k != "draai"}
    rb = Q["buis"] / 2
    kolom_top = 0.163
    cylinder("Quooker voet", Q["voet"] / 2, 0.010, (0, 0, 0.005), "RVS", coll, kr)
    cylinder("Quooker kolom", 0.018, kolom_top - 0.010, (0, 0, (kolom_top + 0.010) / 2), "RVS", coll, kr)
    cylinder("Quooker ring", 0.0195, 0.004, (0, 0, 0.071), "RVS", coll, kr)
    cylinder("Quooker rood ringetje", 0.0186, 0.004, (0, 0, 0.130), "Quooker rood", coll, kr)
    cylinder("Quooker kartelring", 0.0205, 0.022, (0, 0, 0.152), "RVS kartel", coll, kr)

    # uitloop: middellijn met twee afgeronde bochten
    zt = Q["hoogte"] - rb              # middellijn van het bovenste stuk
    r = 0.030
    yv = -Q["uitloop"]                 # hart van de uitloopopening
    pts = [(0, 0, kolom_top - 0.005), (0, 0, zt - r)]
    for i in range(1, 8):              # bocht 1: omhoog -> naar voren
        a = math.radians(90 * i / 8)
        pts.append((0, -r + r * math.cos(a), zt - r + r * math.sin(a)))
    pts.append((0, yv + r, zt))
    for i in range(1, 8):              # bocht 2: naar voren -> omlaag
        a = math.radians(90 * i / 8)
        pts.append((0, yv + r - r * math.sin(a), zt - r + r * math.cos(a)))
    pts.append((0, yv, Q["opening"] + 0.022))
    cu = bpy.data.curves.new("Quooker uitloop", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = rb
    cu.bevel_resolution = 6
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts):
        pt.co = (*co, 1.0)
    cu.materials.append(MATS["RVS"])
    new_obj("Quooker uitloop", cu, coll, kr)
    cylinder("Quooker mondstuk", rb + 0.0015, 0.022, (0, yv, Q["opening"] + 0.011), "RVS", coll, kr)
    cylinder("Quooker straalbreker", rb - 0.002, 0.002, (0, yv, Q["opening"] - 0.0005), "Zwart kunststof", coll, kr)

    # Classic-hendel: taps toelopend staafje met knop, iets omhoog gericht
    hl = Q["hendel"]
    h = empty("Quooker hendel", coll, kr, (0.018, 0, 0.099))
    h.rotation_euler.y = math.radians(-8)
    me = bpy.data.meshes.new("Quooker hendel")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.0055, radius2=0.0035, depth=hl - 0.012)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=((hl - 0.012) / 2, 0, 0))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS["RVS"])
    stang = new_obj("Quooker hendel stang", me, coll, h)
    for p in me.polygons:
        p.use_smooth = True
    cylinder("Quooker hendel knop", 0.0055, 0.016, (hl - 0.008, 0, 0), "RVS", coll, h).rotation_euler.y = math.pi / 2
    cylinder("Quooker hendel kraag", 0.008, 0.008, (0.003, 0, 0), "RVS", coll, h).rotation_euler.y = math.pi / 2


def afgeronde_rechthoek(b, d, r, n=8):
    """Punten (x, y) van een rechthoek b x d met hoekradius r, tegen de klok in."""
    r = max(0.001, min(r, b / 2 - 0.0005, d / 2 - 0.0005))
    pts = []
    for cx, cy, a0 in ((b / 2 - r, d / 2 - r, 0), (-b / 2 + r, d / 2 - r, 90), (-b / 2 + r, -d / 2 + r, 180), (b / 2 - r, -d / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def bouw_spoelbak(sb, blad, coll, hulp):
    """Vlakinbouw-spoelbak: smalle flens gelijk met het werkblad, bak met ronde hoeken en ronde bodem."""
    S = {k: v * M if isinstance(v, (int, float)) else v for k, v in SPOELBAK.items()}
    b, d, h, r, rb, fl = S["b"], S["d"], S["h"], S["r"], S["r_bodem"], S["flens"]

    # uitsparing in het werkblad op de bakmaat
    me = bpy.data.meshes.new("Spoelbak uitsparing")
    bm = bmesh.new()
    onder = [bm.verts.new((px, py, -0.06)) for px, py in afgeronde_rechthoek(b, d, r)]
    boven = [bm.verts.new((px, py, 0.01)) for px, py in afgeronde_rechthoek(b, d, r)]
    n = len(onder)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((onder[i], onder[j], boven[j], boven[i]))
    bm.faces.new(list(reversed(onder)))
    bm.faces.new(boven)
    bm.to_mesh(me)
    bm.free()
    cut = new_obj("Spoelbak uitsparing (hulp)", me, hulp, sb)
    hide_helper(cut)
    mod = blad.modifiers.new("Spoelbak", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cut
    boolean_solver_exact(mod)
    blad.modifiers.move(len(blad.modifiers) - 1, 0)

    # bak: ringen van boven naar beneden (rechte wand, dan bodemafronding), flens rond de bovenrand
    me = bpy.data.meshes.new("Spoelbak")
    bm = bmesh.new()
    ringen = [[bm.verts.new((px, py, 0.0008)) for px, py in afgeronde_rechthoek(b + 2 * fl, d + 2 * fl, r + fl)]]
    for k in range(9):
        t = math.radians(90 * k / 8)
        inset = rb * (1 - math.cos(t))
        z = -(h - rb) - rb * math.sin(t) if k else 0.0008
        ringen.append([bm.verts.new((px, py, z)) for px, py in afgeronde_rechthoek(b - 2 * inset, d - 2 * inset, r - inset)])
        if k == 0:
            ringen.append([bm.verts.new((px, py, -(h - rb))) for px, py in afgeronde_rechthoek(b, d, r)])
    n = len(ringen[0])
    for r0, r1 in zip(ringen, ringen[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(ringen[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS["RVS spoelbak"])
    bak = new_obj("Spoelbak RVS", me, coll, sb)
    sol = bak.modifiers.new("Dikte", "SOLIDIFY")
    sol.thickness = 0.001
    sol.offset = 0.0
    for p in me.polygons:   # flens vlak (scherpe rand), bak glad
        p.use_smooth = p.center.z < 0.0

    # afvoer met korfplug, en de overloop in de achterwand
    zb = -h + 0.0005
    ay = S["afvoer_y"]
    af = empty("Afvoer", coll, sb, (0, ay, zb))
    cylinder("Afvoer rand", 0.047, 0.002, (0, 0, 0.001), "RVS", coll, af)
    cylinder("Afvoer korf", 0.037, 0.002, (0, 0, 0.0018), "Zwart glas", coll, af)
    for i in range(18):   # ring van sleufjes: staande RVS-spaken tussen donkere gaten
        a = 2 * math.pi * i / 18
        arm = empty(f"Afvoer spaak {i}", coll, af, rot_z=a)
        box(f"Afvoer spaak {i}", 0.022, -0.0018, 0.0018, 0.037, 0.0018, 0.0028, "RVS", coll, arm)
    cylinder("Afvoer knop", 0.021, 0.006, (0, 0, 0.004), "RVS", coll, af)
    ov = empty("Overloop", coll, sb, (0, d / 2, -0.032))
    box("Overloop plaatje", -0.028, -0.0015, -0.008, 0.028, 0.0, 0.008, "RVS", coll, ov, bevel=0.002)
    box("Overloop sleuf", -0.020, -0.0018, -0.0025, 0.020, -0.0012, 0.0025, "Zwart glas", coll, ov)

def bouw_tegels(run, lengte, z0, z1, coll):
    tb, th, voeg = TEGEL["b"] * M, TEGEL["h"] * M, TEGEL["voeg"] * M
    groep = empty("Tegels Muur 6", coll, run)
    x, i = 0.0, 0
    while x < lengte - 1e-6:
        w = min(tb, lengte - x)
        x0 = x + (voeg / 2 if i > 0 else 0.0)
        x1 = x + w - (voeg / 2 if x + w < lengte - 1e-6 else 0.0)
        ob = box(f"Tegel {i + 1}" + (" (restant)" if w < tb - 1e-6 else ""), x0, 0, z0, x1, -0.009, z1, "Tegel", coll, groep)
        uv = ob.data.uv_layers.new(name="UVMap")
        for loop in ob.data.loops:
            co = ob.data.vertices[loop.vertex_index].co + ob.location
            uv.data[loop.index].uv = ((co.x - x) / tb, (co.z - z0) / th)
        x += w
        i += 1


# ---------- licht en camera ----------

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def bouw_licht_camera(coll, R):
    sun = bpy.data.lights.new("Zon", "SUN")
    sun.energy = 2.0
    sun.angle = math.radians(2)
    s = new_obj("Zon", sun, coll)
    s.rotation_euler = (math.radians(-50), 0, math.radians(20))

    # Centrale plafondlamp met 3 richtbare spots
    px, py = PLAFONDLAMP["positie"]
    lamp = empty("Plafondlamp", coll, None, (px * M, py * M, PLAFOND * M))
    cylinder("Plafondlamp voet", 0.09, 0.02, (0, 0, -0.01), "Greep", coll, lamp)
    for i, (naam, doel) in enumerate(PLAFONDLAMP["spots"].items()):
        hoek = i * 2 * math.pi / 3
        doel_ob = empty("Richtpunt - " + naam, coll, None, tuple(v * M for v in doel))
        doel_ob.empty_display_type = "SPHERE"
        sp = new_obj(naam, spotlicht(naam, PLAFONDLAMP["spot_w"], 60, 0.8), coll, lamp,
                     (0.05 * math.cos(hoek), 0.05 * math.sin(hoek), -0.08))
        c = sp.constraints.new("TRACK_TO")
        c.target = doel_ob
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        kop = cylinder(naam + " kop", 0.028, 0.07, (0, 0, 0.037), "Greep", coll, sp)
        kop.visible_shadow = False

    cams = {
        "Camera - Overzicht": ((0.45, -2.75, 1.6), (1.75, -0.6, 1.15), 16),
        "Camera - Muur 6": ((0.15, -1.55, 1.6), (2.14, -1.2, 1.25), 15),
        "Camera - Raam": ((1.1, -2.4, 1.6), (1.0, 0.0, 1.35), 18),
        "Camera - Koelkast": ((1.4, -0.75, 1.6), (-0.1, -2.1, 1.15), 16),
        "Camera - Doorkijk woonkamer": ((0.88, -3.7, 1.6), (1.0, -0.6, 1.15), 24),
        "Camera - Hoek Muur 7": ((1.3, -2.3, 1.95), (0.3, -0.35, 0.95), 16),
        "Camera - Langs werkblad": ((1.9, -2.45, 1.12), (1.85, -0.3, 0.98), 20),
        "Camera - Spoelbak": ((1.25, -1.05, 1.55), (0.85, -0.05, 1.0), 22),
    }
    first = None
    for name, (loc, tgt, lens) in cams.items():
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        cd.clip_start = 0.05
        ob = new_obj(name, cd, coll, None, loc)
        look_at(ob, tgt)
        first = first or ob
    bpy.context.scene.camera = first

    # Pan-camera voor de video (ease-in/ease-out tussen begin- en eindhoek)
    cd = bpy.data.cameras.new("Camera - Pan")
    cd.lens = PAN["lens"]
    cd.clip_start = 0.05
    cam = new_obj("Camera - Pan", cd, coll, None, tuple(v * M for v in PAN["positie"]))
    sc = bpy.context.scene
    sc.render.fps = PAN["fps"]
    sc.frame_start, sc.frame_end = 1, PAN["seconden"] * PAN["fps"]
    for frame, hoek in ((sc.frame_start, PAN["van"]), (sc.frame_end, PAN["tot"])):
        cam.rotation_euler = (math.radians(90 + PAN["kantel"]), 0, math.radians(hoek))
        cam.keyframe_insert("rotation_euler", frame=frame)


def instellingen_scene():
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.length_unit = "MILLIMETERS"
    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg is None:
        bg = world.node_tree.nodes.new("ShaderNodeBackground")
        out = next(n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD")
        world.node_tree.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Color"].default_value = (0.75, 0.82, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 0.4
    vs = sc.view_settings
    try:
        vs.view_transform = "AgX"
        vs.look = "AgX - Base Contrast"
    except TypeError:
        pass
    ee = getattr(sc, "eevee", None)
    if ee is not None:
        for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True), ("use_fast_gi", True)):
            if hasattr(ee, attr):
                setattr(ee, attr, val)


# =====================================================================

def main():
    clear_keuken()
    make_materials()
    scene_root = bpy.context.scene.collection
    root = get_coll("Keuken", scene_root)
    c_ruimte = get_coll("Ruimte", root)
    c_onder = get_coll("Onderkasten", root)
    c_boven = get_coll("Bovenkasten", root)
    c_hoog = get_coll("Hoge kasten", root)
    c_blad = get_coll("Werkblad", root)
    c_app = get_coll("Apparatuur", root)
    c_licht = get_coll("Licht en camera", root)
    hulp = get_coll("Hulpobjecten", root)

    R = bouw_ruimte(c_ruimte, hulp)
    bouw_keuken(R, c_onder, c_boven, c_hoog, c_blad, c_app, hulp)
    if KOFFIEZET:
        bouw_koffiezet(c_app)
    if THEEPOT:
        bouw_theepot(c_app)
    if AANKLEDING:
        bouw_aankleding(get_coll("Aankleding", root))
    bouw_licht_camera(c_licht, R)
    instellingen_scene()
    print(f"Keuken opgebouwd (variant {VARIANT}).")


main()
