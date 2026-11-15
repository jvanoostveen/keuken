---
name: keuken-render
description: Het keukenmodel aanpassen en renders maken in Blender (variant bouwen, vaste of eigen camera's, achtergrondrenders, controleren). Gebruik bij elke vraag om iets in het model te veranderen of nieuwe beelden/video te maken.
---

# Keukenmodel aanpassen en renderen

## 1. Aanpassen
- Model: instellingen bovenin `keuken.py` (mm). Varianten: `variaties.py` (`WANDTEGELS`, `MUURVERF`, `VARIANTEN`).
- Nieuwe functie? Volg de bestaande helpers (`box`, `cylinder`, `empty`, `make_mat`, `new_obj`) en zet de
  instellingen als `NAAM = dict(...)` in het INSTELLINGEN-blok met een commentaarregel over de bron.

## 2. Bouwen en snel bekijken (open Blender, MCP)
```python
ns = {"__name__": "render"}; exec(open("/Users/joeri/Development/keuken/tools/render.py").read(), ns)
ns["toon"]("bmn")                       # of None voor alleen keuken.py
ns["shot"]("<scratchpad>/test", "Raam", 960, 540, samples=32)   # proefbeeld
```
Bekijk het beeld met Read. Eigen standpunt: `camera=((x, y, z), (richtpunt), lens)` in meters;
recht aanzicht: `ortho=<breedte m>` en een `clip` die alles vóór het vlak wegsnijdt.

## 3. Definitieve renders
- 1600×900, 96 samples, naar `renders/<onderwerp>/<naam>`.
- Meer dan een paar beelden of > 1 min: zet de renderlus in een script, start het met
  `bpy.app.timers.register(lambda: exec(...))`, laat het aan het eind een `.klaar`-bestand schrijven en wacht
  met `until [ -f ... ]; do sleep 5; done` in Bash op de achtergrond.
- Alternatief zonder de open Blender te blokkeren:
  `Blender -b "Keuken - variaties.blend" --python tools/render.py -- "<variant>" renders/<map> Raam Overzicht`

## 4. Controleren
- Maak een contactsheet van de nieuwe renders en kijk naar fouten (vlakken die doorlopen, z-fighting, objecten
  door elkaar, te fel/donker).
- Meet kritieke maten na in Blender (`matrix_world @ Vector(c) for c in bound_box`).

## 5. Afronden
- Werk de ingebedde tekst `keuken.py` in het `.blend`-bestand bij en sla op (`bpy.ops.wm.save_mainfile()`).
- Stuur de beste beelden met SendUserFile en vermeld wat geschat is.

## Video
- Pan: camera `Camera - Pan`, instellingen `PAN`; render in de achtergrond naar `renders/pan.mp4` (FFMPEG/H264).
- Dagverloop: `Blender -b Keuken.blend --python dagverloop.py` (proefframes: `-- 1 200 350`).
