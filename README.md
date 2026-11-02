# Songbook

Programs that turn a pile of songs in an XML file into a printed songbook — a
PDF, alphabetised by artist, with a table of contents, page numbers, and chord
diagrams for up to five instruments — and into a web version you can play from
on a phone.

Requires Python 3 and the free version of
[PrinceXML](https://www.princexml.com/) for the PDF.

**Bring your own songs.** `example-songs.xml` has four to work from: Amazing
Grace, Waltzing Mathilda, Drunken Sailor, and one of mine.

## The XML

```xml
<songbook>
	<song>
		<songtitle>song title goes here</songtitle>
		<artist>artist name goes here</artist>
		<lyrics>
			lyrics and chords go here
		</lyrics>
	</song>
</songbook>
```

Chords go above the words they belong to, in a fixed-width layout — the chord
sits in the column of the syllable it is played on. Tabs are four columns
wide, and both stylesheets set `tab-size: 4` to match.

## Building

```sh
python3 chordadder.py example-songs.xml example-songs-with-chords.xml
python3 songbookmaker11.py example-songs-with-chords.xml
```

`chordadder.py` works out which chords each song uses and adds a `<chords>`
element to it. It is safe to re-run: an existing `<chords>` is replaced, not
duplicated. It reads both chordpro-style `[C]` markers and chords written on
their own line, and it tries hard not to mistake tablature, strumming
patterns or stage directions for chords. It ends by printing every chord it
found plus the ones used in only one song — that second list is where typos
show up.

`songbookmaker11.py` writes an HTML file, hands it to Prince, and opens the
PDF. Output is named from the version and the instruments, not from the input
file, so `songbook-11.0-guitar-uke.pdf` and `songbook-11.0-mandolin.pdf` can
coexist. An input filename containing "discard" gets `-discards` appended and
a different title page.

`build.sh` runs the lot: chorus tagging, chords, every PDF, both web pages,
and optionally uploads them. Edit the paths at the top first.

## Instruments

Name them on the command line; the order is the column order.

```sh
python3 songbookmaker11.py songs.xml banjo uke
python3 songbookmaker11.py songs.xml guitar uke banjo mandolin bariuke
```

Recognised: `guitar`, `uke` (or `ukulele`), `banjo`, `mandolin`, `bariuke`.
Each needs a matching subdirectory in `diagrams/`.

About 19 chords fit in the printed diagram block on letter paper before it
runs off the bottom of the page.

## Other words on the command line

* `allkeys` — also draw every chord in all twelve keys, so the web version can
  transpose. Slow the first time, then cached on disk.
* `lulu` — leave off the first two pages, which lulu.com wants as a separate
  file.
* `andy` — build the subset listed in `andy-songbook.txt`, ordered by title.
* `noopen` — don't open the PDF when it's done.

## The web version

```sh
python3 makeweb.py songbook-11.0-guitar-uke-banjo-mandolin-bariuke.html songbook-web.html
```

`makeweb.py` rebuilds the print HTML into one page you can read on a phone.
It is not a second renderer — it transforms the file Prince was given, so the
two can't drift apart. What it adds:

* **search**, and a contents panel listing songs by artist and by title
* **instrument checkboxes** — the page is built from the five-instrument book,
  and unticking one hides its diagrams and drops them from memory
* **transposing**, per song, with the chord diagrams following and the words
  staying over the right syllables. Needs `allkeys` to have been run.
* **auto-scroll** at a readable speed, stopping at the end of the song, and
  holding a wake lock while it runs
* **tap to turn the page** on a touchscreen — one tap moves a screen, the top
  fifth goes back, a drag scrolls normally

Pass `discard` as a third argument for the discard-pile edition.

A page of three hundred songs runs into limits that a short one does not, and
most of the odder-looking code in `makeweb.py` is there because of one:
diagrams are attached and released as you scroll, lyric blocks become
horizontal scroll containers only while they are near the viewport, and the
chord block moves from beside the words to above them below 1000px. Mobile
Safari will drop a tab that asks for too many composited layers, and a
three-hundred-song page asks easily.

## Chord diagrams

`diagrams/<instrument>/<chord>.png`. A filename can't hold a slash, so `A/F#`
is `A_F#.png`. A chord with no diagram gets a blank grid and a `?` after its
name — an empty grid on its own is ambiguous, because on a banjo an open G
really is just strumming it.

The diagrams here are generated, not curated: five instruments, every chord
the book uses, in all twelve keys and both spellings. Use them for whatever
you like. They are drawn by
[ThatChord](https://github.com/tomcontileslie/ThatChord), lightly modified —
see `thatchord-fork/README-fork.md` for what was changed and why. ThatChord
is CC BY-SA 4.0 and the fork carries the same licence.

## Configuration

The block at the top of `songbookmaker11.py`:

```python
VERSION      = "11.0"    # title page and output filenames
BOOKTITLE    = "..."     # the two title lines
DISCARDTITLE = "..."     # and for the discard pile
WEBURL       = ""        # printed on the title page; blank omits the line
PRINCE       = "/opt/homebrew/bin/prince"
```

`FIRSTPAGE` and `NEXTPAGE` are how many lyric lines fit on a song's first and
later pages — 61 and 63 with the supplied stylesheet. The first holds two
fewer because of the title and the blank line under it. Change the margins or
the font size and you must count a full page again and update these, or
two-page songs land wrongly.

## Multi-page songs

Songs longer than a page are held back to start on an even page, so you get a
spread rather than a page turn mid-song. To control *where* one breaks, pad
the lyrics with blank lines so a verse starts exactly on line 62. There is no
automatic version of this. `chordadder.py` preserves the whitespace, so you
can pad before or after adding chords.

## Tests

`testchordspots.py` checks which tokens on a mixed line count as chords —
every case came from a real line, and most from a bug. `testcapo.py` and
`testalign.py` drive a real browser and need `playwright`.
