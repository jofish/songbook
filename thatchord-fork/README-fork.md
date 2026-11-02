# ThatChord, with three changes

The chord diagrams in `../diagrams/` are drawn by
[ThatChord](https://github.com/tomcontileslie/ThatChord) by Tom Conti-Leslie,
distributed under **CC BY-SA 4.0**. This folder is a modified copy, and under
the share-alike terms it carries the same licence.

## What was changed, and why

All three changes are in `output.py`, and all three are about making a diagram
that sits in a songbook rather than one you look at on its own:

1. **The header is suppressed.** `if header:` became `if False:`, so no
   title bar is drawn above the grid.
2. **The chord name is not drawn into the image.** The `drw.text((tx, ty),
   title)` call is commented out. The songbook prints the name itself, in the
   page's own font, underneath or beside the diagram — baked-in text would be
   a second name in a different typeface.
3. **The file is named after the chord.** Upstream writes every diagram to
   `ThatChordTemp.png`; this writes `<chordname>.png`, so a whole book's worth
   can be generated in one run and found again by name.

There is also a small vertical-spacing adjustment (`hgh = (h + 2) * 20 + b`)
so the grids pack tightly enough to fit a songbook page.

## What was not changed

Everything else: the chord dictionaries, the fingering search, the ranking that
decides which voicing to show. Those are upstream's work and the reason this is
worth using at all.

## Running it

ThatChord needs `pyyaml` and `pillow` (see `requirements.txt`). songbookmaker
finds this folder by looking for `thatchord.py` and runs it per chord, so you
do not normally invoke it yourself.
