# Songbook

A set of programs for generating guitar/uke/banjo songbooks, alphabetized by artist, with a table of contents, page numbers, and per-song chord diagrams.

Requires Python3 and the free version of [PrinceXML](https://www.princexml.com/) installed.

## Data flow

Start by putting your songs into an xml file formatted like example-songs.xml. The XML format looks like this:

``````
<songbook>
	<song>
		<songtitle>song title goes here</songtitle>
		<artist>artist name goes here</artist>
		<lyrics> 
			lyrics and chords go here
		</lyrics>
	</song>
	
	<song>.....
	</song>
</songbook>
``````

Then run

``````python3 chordadder.py example-songs.xml example-songs-with-chords.xml```

`````chordadder.py``` does its best to identify chords in those songs and use it to generate the second file, example-songs-with-chords.xml. It adds a ```<chords>....</chords>``` element to each ```<song>...</song>```. It's safe to re-run: an existing ```<chords>``` element is replaced rather than duplicated.

It recognises both chordpro-style ```[C]``` markers and chords written on their own line above the lyrics, and it tries hard not to mistake tablature, strumming patterns, or stage directions for chords. At the end it prints every chord it found, plus a list of chords used in only one song — that list is where false positives and typos in your source show up.

Then run

````python3 songbookmaker9.py example-songs-with-chords.xml```

which generates an html document, sends it to PrinceXML, and opens the resulting pdf. Any previous pdf of the same name is renamed to ```.old``` first.

Output files are named from the version and the instruments, not from the input file — so the above produces ```songbook-9.3-guitar-uke.html```, ```songbook-9.3-guitar-uke.pdf```, and ```songbook-9.3-guitar-uke.old```.

Best practice is to run both programs back to back:

```python3 chordadder.py example-songs.xml example-songs-with-chords.xml; python3 songbookmaker9.py example-songs-with-chords.xml```

## Instruments

By default you get guitar and uke chord diagrams. Name the instruments on the command line to change that — the order you give them is the order the columns appear in:

```
python3 songbookmaker9.py songs.xml banjo uke
python3 songbookmaker9.py songs.xml guitar uke banjo
python3 songbookmaker9.py songs.xml "banjo, uke"
````

Recognised names are ```guitar```, ```uke``` (or ```ukulele```), and ```banjo```. Each needs a matching subdirectory in ```diagrams/```. The instrument list also determines the output filename, so ```songbook-9.3-banjo-uke.pdf``` and ```songbook-9.3-guitar-uke-banjo.pdf``` can coexist.

About 19 chords fit in the diagram block, assuming letter size paper, before it runs off the bottom of the page. Songs with more than that will have the extras clipped.

## Modes

A few other words can be given on the command line:

* ```lulu```: leaves off the first two pages (which if you print through lulu.com are a separate file)
* ```andy```: builds a subset, listed one per line in ```andy-songbook.txt```, ordered by song title rather than artist

If the input filename contains "discard", the title page changes to the discard-pile text automatically — no command-line word needed.

## Configuration

The block at the top of ```songbookmaker10-public.py``` is what you'll want to edit for your own book:

````python
VERSION   = "9.3"        # appears on the title page and in the output filenames
BOOKTITLE = "..."        # the two title lines
WEBURL    = ""           # printed on the title page; leave blank to omit the line
PRINCE    = "/opt/homebrew/bin/prince"   # or /usr/local/lib/prince/bin/prince
````

````FIRSTPAGE``` and ```NEXTPAGE``` are the number of lyric lines that fit on a song's first and subsequent pages — 61 and 63 with the supplied stylesheet. The first page holds two fewer because of the song title and the blank line under it. If you change the page margins or the font size in the css, count the lines on a full page and update these, or the two-page-song handling will place songs wrongly.

## Multi-page songs

Songs longer than one page are held back so they start on an even page, giving you a two-page spread rather than a page turn mid-song.

To control *where* a song breaks, put blank lines in the lyrics so that a verse or chorus starts exactly on line 62. There's no automatic version of this — it's manual padding in the XML. ```chordadder.py``` preserves that whitespace, so you can pad first and add chords afterwards in either order.

## Chord diagrams

Diagrams live in


Then run

`````python3 songbookmaker9.py example-songs-with-chords.xml```

which generates an html document, sends it to PrinceXML, and opens the resulting pdf. Any previous pdf of the same name is renamed to ```.old``` first.

Output files are named from the version and the instruments, not from the input file — so the above produces ```songbook-9.3-guitar-uke.html```, ```songbook-9.3-guitar-uke.pdf```, and ```songbook-9.3-guitar-uke.old```.

Best practice is to run both programs back to back:

````python3 chordadder.py example-songs.xml example-songs-with-chords.xml; python3 songbookmaker9.py example-songs-with-chords.xml```

## Instruments

By default you get guitar and uke chord diagrams. Name the instruments on the command line to change that — the order you give them is the order the columns appear in:

````
python3 songbookmaker9.py songs.xml banjo uke
python3 songbookmaker9.py songs.xml guitar uke banjo
python3 songbookmaker9.py songs.xml "banjo, uke"
`````

Recognised names are ```guitar```, ```uke``` (or ```ukulele```), and ```banjo```. Each needs a matching subdirectory in ```diagrams/```. The instrument list also determines the output filename, so ```songbook-9.3-banjo-uke.pdf``` and ```songbook-9.3-guitar-uke-banjo.pdf``` can coexist.

About 15 chords fit in the diagram block before it runs off the bottom of the page. Songs with more than that will have the extras clipped.

## Modes

A few other words can be given on the command line:

* ```lulu```: leaves off the first two pages (which if you print through lulu.com are a separate file)
* ```andy```: builds a subset, listed one per line in ```andy-songbook.txt```, ordered by song title rather than artist

If the input filename contains "discard", the title page changes to the discard-pile text automatically — no command-line word needed.

## Configuration

The block at the top of ```songbookmaker9.py``` is what you'll want to edit for your own book:

`````python
VERSION   = "9.3"        # appears on the title page and in the output filenames
BOOKTITLE = "..."        # the two title lines
WEBURL    = ""           # printed on the title page; leave blank to omit the line
PRINCE    = "/opt/homebrew/bin/prince"   # or /usr/local/lib/prince/bin/prince
`````

`````FIRSTPAGE``` and ```NEXTPAGE``` are the number of lyric lines that fit on a song's first and subsequent pages — 61 and 63 with the supplied stylesheet. The first page holds two fewer because of the song title and the blank line under it. If you change the page margins or the font size in the css, count the lines on a full page and update these, or the two-page-song handling will place songs wrongly.

## Multi-page songs

Songs longer than one page are held back so they start on an even page, giving you a two-page spread rather than a page turn mid-song.

To control *where* a song breaks, put blank lines in the lyrics so that a verse or chorus starts exactly on line 62. There's no automatic version of this — it's manual padding in the XML. ```chordadder.py``` preserves that whitespace, so you can pad first and add chords afterwards in either order.

## Chord diagrams

Diagrams live in ```diagrams/<instrument>/```, named for the chord. Slash chords like "A/F#" have the slash replaced with an underscore, so that's ```A_F#.png```.

If a chord isn't found there, songbookmaker falls back to ```diagrams/<instrument>-truechord/```, which holds diagrams generated automatically rather than curated. Failing that it draws a blank grid from ```empty.png``` for you to fill in by hand, and lists the chord in the "unknown chords" report at the end of the run.

You'll want to install [ThatChord](https://github.com/tomcontileslie/ThatChord) to generate these. It needs ```pyyaml``` and ```pillow```.

