---
name: keuken-pdf
description: Een keukendocument (PDF) maken of bijwerken uit renders: HTML-bron in de repo, Chrome naar PDF, controle met poppler in een container. Gebruik voor gespreksdocumenten voor BMN, voorstellen en overzichten.
---

# Keukendocument maken

## Opzet
- Bron in de repo: een map met `index.html` + `img/` (voorbeeld: `ideeen/`). Niet in de scratchpad.
- Pagina's als `<section class="page">` van 297×210 mm met `@page { size: 297mm 210mm; margin: 0 }` en
  `print-color-adjust: exact`. Neem de stijl van `ideeen/index.html` over (kop met label + paginanummer,
  `card`-blokken, `figure` met `figcaption`).
- Beelden: renders verkleinen naar jpg (~1600 px, kwaliteit 82–85) in `img/`:
  `sips -s format jpeg -s formatOptions 84 -Z 1600 renders/x.png --out <map>/img/x.jpg`
- Schema's/plattegronden als inline of losse SVG (maten in mm, labels groot genoeg: ≥ 45 eenheden bij een
  tekening van ~3000 mm breed).

## Bouwen en controleren
```bash
tools/pdf.sh ideeen/index.html "Keuken ideeën.pdf" png <scratchpad>/pag
```
Bekijk elke PNG (contactsheet). Let op: tekst die van de pagina loopt, lege grids (een grid met `flex: 0`
klapt in, gebruik `flex: none`), vervormde beelden (`object-fit`), te kleine labels.

## Inhoud
- Gespreksdocument, niet zakelijk: geen vragenlijst en geen wijzigingstabel; vragen apart in de chat.
- `Keuken ideeën.pdf`: noem de leverancier (BMN) nergens, ook niet in schema's (`grep -ri bmn ideeen/`).
- Alleen de huidige keuzes tonen; alternatieven alleen waar nog getwijfeld wordt (bijv. wit/eiken).
- Productnamen exact (decortegel: Argenta Studio Litter; werkblad: Dekker TopCore Sparrow;
  kraan: Quooker Classic Fusion Square; spoelbak: SDE-0047).
- Maten in cm in de tekst, met vermelding als iets geschat is.
