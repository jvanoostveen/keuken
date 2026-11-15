# Keuken Amelisweerd 15

3D-model en ontwerpdocumenten voor de nieuwe keuken. Het model is parametrisch: alles wordt
opgebouwd door Python-scripts in Blender, zodat maten, kasten, kleuren en materialen op één plek
aan te passen zijn.

## Mappen

| Map / bestand | Wat |
|---|---|
| `keuken.py` | **Het model.** Bouwt de hele keuken op (ruimte, kasten, werkblad, tegels, licht, camera's). Alle instellingen bovenaan, maten in mm. |
| `variaties.py` | Varianten bovenop het model: andere wandtegels, muurverven, eiken vakkenkast, eerdere voorstellen. Kies met `VARIANT`. |
| `tegeltexturen.py` | Maakt zelf getekende tegeltexturen (zellige, visgraat, effen) in `textures/`. |
| `echte_tegels.py` | Maakt tegeltexturen uit productfoto's van echte tegels (`tegels/kandidaten/`). |
| `dagverloop.py` | Video van een dag (zonnestand Amersfoort, keuken op het noorden). |
| `tools/render.py` | Hulp om een variant te bouwen en camerastandpunten te renderen. |
| `tools/pdf.sh` | HTML-document naar PDF via Chrome, controle met poppler in een container. |
| `Keuken.blend` | Basisbestand. `Keuken - variaties.blend` is het werkbestand voor varianten; `Keuken - okt versie.blend` is een bewaarde momentopname. |
| `ideeen/` | Bron van het actuele gespreksdocument (`index.html` + `img/`) → `Keuken ideeën.pdf`. |
| `*.pdf` (root) | Gegenereerde documenten: `Keuken ideeën.pdf` (actueel), `Keuken stand van zaken.pdf`, `Tegels en muurkleur.pdf`, `Keukenvoorstellen.pdf` (eerste ronde, achterhaald). |
| `renders/` | Gerenderde beelden, per onderwerp in submappen. Video's (`*.mp4`) staan in `.gitignore`. |
| `textures/` | Texturen die het model laadt (uitzicht, decortegel, wandtegels, Sparrow-korrel). |
| `bmn/` | Offerte en tekeningen van BMN (v1 PDF, v2 afbeeldingen): bron voor alle maten. |
| `fotos/`, `buren/` | Foto's van de huidige keuken, details (kozijn, rolgordijn), moodboard en de keuken van de buren (gespiegeld). |
| `blad/`, `kasten/`, `tegels/` | Productbeelden: werkblad Sparrow, greepreferentie, decortegel en tegelkandidaten. |

## Werken met het model

1. Open `Keuken - variaties.blend` (of `Keuken.blend`) in Blender.
2. Pas instellingen aan in `keuken.py` (en eventueel `variaties.py`).
3. Werkruimte *Scripting* → open het script → *Run Script*. De collectie `Keuken` wordt volledig
   opnieuw opgebouwd; handmatige wijzigingen daarin gaan verloren. Eigen objecten buiten `Keuken` blijven.

Belangrijkste instellingen in `keuken.py`: `KLEUREN`, `VLOER`, kastmaten (`PLINT`, `BOVENKAST_ONDERKANT`, …),
`RUIMTE` (muren, raam, vensterbank), `ONDER_MUUR5`, `HOEKKAST`, `VARIANTEN` (indeling Muur 6), `HOGE_KASTEN`,
`SPOELBAK`, `KRAAN`, `UITSPARING`, `ROLGORDIJN`, `TEGEL` (decortegel), `MOZAIEK`, `WERKBLAD`, `AANKLEDING`.

Assenstelsel: x langs de raamwand (Muur 5) vanaf Muur 4, y = 0 is Muur 5, de keuken ligt bij negatieve y,
Muur 6 (kookwand) op x = 2140 mm. Muurnummers volgen de BMN-tekening.

### Varianten

```python
VARIANT = "echt Steenbok Rustic Olive 13x13 | LG Pleat"   # echte tegel | muurverf
VARIANT = "bmn"            # huidige stand (olijf + Frosted Sky), "bmn eiken" met eiken vakkenkast
```

Tegels en verven staan in `WANDTEGELS` en `MUURVERF` in `variaties.py`.

### Renderen

In Blender of via de Blender-MCP:

```python
ns = {"__name__": "render"}; exec(open("tools/render.py").read(), ns)
ns["toon"]("bmn")
ns["shot"]("renders/test/raam", "Raam")
```

Vanaf de terminal (bestand blijft onaangeroerd):

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b "Keuken - variaties.blend" --python tools/render.py -- "bmn" renders/test Raam Overzicht
```

Vaste camera's: Overzicht, Muur 6, Raam, Koelkast, Doorkijk woonkamer, Hoek Muur 7, Langs werkblad, Spoelbak.

### Video

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b Keuken.blend --python dagverloop.py
```

De pan-video wordt gerenderd met de camera `Camera - Pan` (instellingen `PAN` in `keuken.py`).

## Documenten (PDF)

Documenten zijn HTML-pagina's (A4 liggend, `@page` in de CSS) met beelden uit `renders/`, omgezet met Chrome:

```bash
tools/pdf.sh ideeen/index.html "Keuken ideeën.pdf"
```

Met `png <map>` erachter worden ook alle pagina's als PNG weggeschreven om de opmaak te controleren.

## Afspraken

- Maten in mm in de scripts; in documenten cm.
- Hexwaarden van verven komen van derden (verf-plaza, pontata e.d.) en zijn schattingen; altijd een tester halen.
- Telefoonfoto's zijn Display P3: eerst naar sRGB omzetten (`sips --matchTo "/System/Library/ColorSync/Profiles/sRGB Profile.icc"`) voordat je kleuren meet.
- Niets op de machine installeren; extra tools (poppler, qpdf) via een container (OrbStack/Docker).
