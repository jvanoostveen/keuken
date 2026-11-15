# Werken in deze repo

Parametrisch Blender-model van een keuken plus ontwerpdocumenten. Zie `README.md` voor de mappen en commando's.
Communiceer in het Nederlands; de eigenaren zijn geen Blender-experts.

## Model

- `keuken.py` is de bron van waarheid. Wijzig het model altijd via de scripts, nooit alleen in Blender: een
  nieuwe run gooit handmatige wijzigingen in de collectie `Keuken` weg.
- Nieuwe instellingen bovenaan in het INSTELLINGEN-blok, met commentaar (bron van de maat, of "geschat").
  Maten in mm. Bestaande stijl volgen: Nederlandse namen, `box()`/`cylinder()`/`empty()`-helpers, materialen via `make_mat()`.
- Varianten (tegels, muurverf, extra's) horen in `variaties.py`, niet in `keuken.py`.
- `keuken.py` bevat ook de tekst die in het `.blend`-bestand zit; na een wijziging die tekst bijwerken
  (`t.clear(); t.write(...)`) en het bestand opslaan, zodat Blender-gebruikers de nieuwe versie zien.
- Maak een wijziging zichtbaar met een render en kijk er zelf naar voordat je iets rapporteert.
- Zeg welke maten gemeten, opgegeven (BMN, fabrikant, gebruiker) of geschat zijn.

## Blender via MCP

- `mcp__blender__execute_blender_code` draait in de open Blender. Lange renders (> ~1 min) lopen tegen de
  time-out aan: start ze via `bpy.app.timers.register(...)` met een klaar-bestand als signaal, en wacht met een
  Bash-`until`-lus op de achtergrond. Of render op de achtergrond met `Blender -b ... --python`.
- `tools/render.py` heeft `toon(variant)` en `shot(uit, camera, w, h)`.
- Shadernodes op type opzoeken, niet op naam.
- Controleer geometrie met maten uit `matrix_world` + `bound_box` (afstand kraan–tegels, spoelbak, enz.).

## Beelden en kleuren

- Contactsheets maken met een klein Swift/AppKit-script of numpy in Blender om veel renders tegelijk te bekijken.
- Foto's van de telefoon: Display P3 → sRGB voordat je kleuren meet.
- Texturen uit productfoto's: zie `echte_tegels.py` (cellen uitsnijden, willekeurig gedraaid opnieuw leggen).

## Documenten

- PDF = HTML (A4 liggend) + `tools/pdf.sh`. Bron van een document hoort in de repo (zoals `ideeen/`),
  niet in de scratchpad: die wordt gewist.
- Controleer elke pagina als PNG (`tools/pdf.sh <html> <pdf> png <map>`) op overlopende tekst en lege vlakken.
- Gespreksdocumenten voor BMN: geen vragenlijst en geen "officiële" wijzigingstabel in het document; open
  vragen apart in de chat.

## Niet doen

- Niets installeren (brew, pip, npm -g). poppler/qpdf e.d. via `docker run --rm` (OrbStack).
- Geen `Co-Authored-By`-regel in commits.
