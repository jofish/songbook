# Songbook

A set of programs for generating guitar/piano/uke songbooks, alphabetized by artist and with tables of contents and page numbers.

Requires Python3 and the free version of [PrinceXML](https://www.princexml.com/) installed. 

## Data flow

Start by putting your songs into an xml file formatted like example-songs.xml. The XML format looks like this:

```
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
```
Then run

```python3 chordadder.py example-songs.xml example-songs-with-chords.xml```

```chordadder.py``` does its best to identify chords in those songs and use it to generate the second file, example-songs-with-chords.xml.
It adds a ```<chords>....</chords>``` line to each ```<song>...</song>```

Then run 

```python3 songbookmaker8.py example-songs-with-chords.xml```

which will first generate an html document ```example-songs-with-chords.html```, and then send it to PrinceXML. It will also take the most recent pdf and rename it, ie example-songs-with-chords.old

PrinceXML will then take the html file and use it to generate the pdf, ```example-songs-with-chords.pdf```, including the page numbers, the table of contents, and the songlist-by-artist.

And you're done. Best practice is probably to put your songs in the XML file, and then run both programs back to back like this:

```python3 chordadder.py example-songs.xml example-songs-with-chords.xml; python3 songbookmaker8.py example-songs-with-chords.xml```

## Modes

There's a few modes you can use by specifying the name on the command line. They are detailed in ```modes.py``` which are about adding different text to the title.

* lulu: leaves off the first two pages (which if you print through lulu.com are a separate file)
* discard: just alternate text on the front page

## guitar-chords-no-labels.zip and ukulele-chords-no-labels.zip

These are the chord names included in the ```diagrams``` directory, but they're useful by themselves so I include them here.

Note that any slash chords, like "A/F#", meaning "an A chord with a F# in the bass" have their slashes replaced with underscores, \_, in the filenames, so that would be A\_F#.png

These are generated from chord descriptions in ChordPro using ThatChord by running chord-generator.py, with a few tweaks to make it work at scale.

Nothing fancy, but useful, and I couldn't find anything like a complete set easily available on the web.
