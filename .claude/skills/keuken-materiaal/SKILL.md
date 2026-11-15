---
name: keuken-materiaal
description: Een echt product (tegel, werkblad, verf, kraan) in het model zetten op basis van productfoto's of kleurcodes. Gebruik als de gebruiker een nieuw materiaal of product wil zien in de renders.
---

# Echt materiaal in het model

## Zoeken
Laat zoekwerk over aan de agent `materiaal-zoeker` (eventueel twee parallel: tegels en verf). Geef context
mee: huidige kleuren (olijftegel #8E957A, decortegel brons, Sparrow #8A8378, kasten RAL 9001, eiken vloer,
limoen rolgordijn), keuken op het noorden, verkrijgbaar in NL/BE.

## Tegels uit productfoto's
1. Foto's met een recht van voren gefotografeerd tegelveld naar `tegels/kandidaten/`.
2. Voeg een regel toe aan `TEGELS` in `echte_tegels.py` (foto, kolommen × rijen, bruikbare cellen zonder
   glansplekken, tegelmaat en voeg in mm, voegkleur) en draai het in Blender → `textures/<naam>_kleur/_data.png`.
3. Registreer in `variaties.py`: `WANDTEGELS["<Merk Serie Kleur Maat>"] = dict(textuur=..., maat=(N*(tegel+voeg),)*2, glans=..., reliëf=...)`.
4. Render met `VARIANT = "echt <tegelnaam> | <muurverf>"`.

## Verf
- Voeg toe aan `MUURVERF` in `variaties.py` met hex en bron in commentaar ("schatting").
- Flexa-waarden: verf-plaza.nl (swatch-kleur in de HTML); F&B/Little Greene: pontata.com e.d.

## Werkblad / decortegel
- Werkblad: paneelfoto voor kleur, monsterfoto als hoogdoorlaat-korrel (`WERKBLAD` in `keuken.py`).
- Decortegel: foto perspectiefcorrigeren naar 1 tegel (2 px/mm), lichtverloop wegdelen met een kwadratisch vlak
  (`TEGEL` in `keuken.py`).

## Kleuren meten
Telefoonfoto's eerst naar sRGB (`sips --matchTo ".../sRGB Profile.icc"`), daarna de mediaan van een vlak zonder
glansplekken meten (numpy in Blender).
