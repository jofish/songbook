import xml.dom.minidom, re, os, sys, subprocess, datetime

# --- edit these for your own book ---------------------------------
# These are placeholders. Put your own in my_settings.py beside this script and
# they override everything here, so your title, your urls and your paths stay
# out of the public repo. my_settings.py is gitignored.
#
#   cat > my_settings.py <<'EOF'
#   BOOKTITLE = "my songbook"
#   WEBURL    = "https://example.com/songbook"
#   EOF
VERSION      = "11.0"
BOOKTITLE    = "a songbook\n\t\t<br>put your own title here"
DISCARDTITLE = "the discard pile"
WEBURL       = ""                          # printed on the title page; blank omits the line
DISCARDURL   = ""
PRINCE       = "/opt/homebrew/bin/prince"  # or /usr/local/lib/prince/bin/prince on intel macs & linux
THATCHORD    = ""                          # draws any chord diagram we don't already have
# Leave THATCHORD empty and it goes looking: in this folder, in any subfolder
# called ThatChord, and in the folder above. Put a full path there instead if
# it lives somewhere else entirely, eg
#    THATCHORD = "/path/to/ThatChord/thatchord.py"
# Without it NOTHING gets drawn and every chord you haven't already got is a
# blank grid, so the search says where it looked when it comes up empty.
THATCHORD_SEARCH = [".", "..", os.path.expanduser("~")]
# ------------------------------------------------------------------

# Your own settings, if you have them. Last, so they win.
try:
	from my_settings import *            # noqa: F401,F403
except ImportError:
	pass


usechords = True
orderbytitle = False
FIRSTPAGE = 61   # lines on a song's first page — the h1 and its blank line take the other two
NEXTPAGE  = 63   # lines on every page after that

diagramroot = "diagrams/"

# Every instrument has four separate strings, and they are allowed to differ:
#
#   diagramdir  the subdirectory under diagrams/ holding the pngs. This is a
#               real folder on disk, so its capitalisation is whatever the
#               folder actually is - it is never derived from anything else.
#   thatchord   the name thatchord.py knows it by, which is what goes after
#               --instrument. The same as diagramdir today, but that's a
#               coincidence rather than something to rely on.
#   heading     what gets printed over that column in the chord table.
#   slug        what goes in the output filename, so it stays lowercase and
#               hyphen-free whatever the other three look like.
#
# The keys are what you type on the command line. Two keys may point at the
# same instrument (uke and ukulele do); the first one you name wins the column.
instrument_table = {
	'guitar':   {'diagramdir': 'guitar',   'thatchord': 'guitar',
	             'heading':    'Guitar',   'slug':      'guitar'},
	'uke':      {'diagramdir': 'ukulele',  'thatchord': 'ukulele',
	             'heading':    'Uke',      'slug':      'uke'},
	'ukulele':  {'diagramdir': 'ukulele',  'thatchord': 'ukulele',
	             'heading':    'Uke',      'slug':      'uke'},
	'banjo':    {'diagramdir': 'banjo',    'thatchord': 'banjo',
	             'heading':    'Banjo',    'slug':      'banjo'},
	'mandolin': {'diagramdir': 'mandolin', 'thatchord': 'mandolin',
	             'heading':    'Mandolin', 'slug':      'mandolin'},
	'bariuke':  {'diagramdir': 'UKULELE-BARITONE-CHICAGO-LINEAR',
	             'thatchord': 'UKULELE-BARITONE-CHICAGO-LINEAR',
	             'heading':    'BariUke',
	             'slug':       'bariuke'},
}

# the same list with the aliases dropped, for when we want each instrument once
every_instrument = list({i['diagramdir']: i for i in instrument_table.values()}.values())

# misspellings we accept, but mention
corrected_word = {
	'ukelele':   'ukulele',
	'ukukele':   'ukulele',
	'gutiar':    'guitar',
	'banjoe':    'banjo',
	'mandoline': 'mandolin',
}

USAGE = (
	"usage: python songbookmaker11.py songs-with-chords.xml [instruments] [lulu] [andy]\n"
	"\n"
	"  instruments  any of guitar, uke, banjo, mandolin, bariuke - default is guitar uke.\n"
	"               the order you give them is the order the columns appear in.\n"
	"  lulu         leave off the first two pages\n"
	"  andy         build the subset listed in andy-songbook.txt, ordered by title\n"
	"  noopen       don't open the pdf when it's finished (for batch builds)\n"
	"  allkeys      also draw every chord in all twelve keys, so the web version\n"
	"               can transpose. Slow the first time, then cached on disk.\n"
	"\n"
	"outputs songbook-<version>-<instruments>.html and .pdf, and renames any\n"
	"previous pdf of that name to .old\n"
	"\n"
	"eg: python songbookmaker11.py songs.xml banjo uke")


def alltext(node, markchorus=False):
	"""Every bit of text under a node, including inside any nested tags.

	With markchorus, a <chorus>...</chorus> element is wrapped in a span on the
	way out. Prince ignores an unstyled inline span, so the pdf is unchanged,
	but it tells makeweb.py exactly where the chorus is -- no guessing."""
	found = ""
	for child in node.childNodes:
		if child.nodeType == child.TEXT_NODE:
			found += child.data
		elif child.nodeType == child.ELEMENT_NODE:
			inner = alltext(child, markchorus)
			if markchorus and child.tagName == 'chorus':
				found += '<span class="chorusblock">' + inner + '</span>'
			else:
				found += inner
	return found


# What's in each diagram folder, read once: lowercased filename -> the real
# filename(s) that fold to it. A list rather than one name because a
# case-sensitive disk really can hold both Em.png and EM.png, while a mac's
# can't - and either way this is how we notice a file named for a chord other
# than the one asking for it.
diagramsondisk = {}
cannotplay = {}     # chords thatchord has already refused, so we ask it once
movedaside = {}     # a diagram whose filename was for a different chord
reconciled = {}     # folded names already sorted out, so we only do it once
stillclashing = {}  # two spellings of one chord still in the xml
respelled = {}      # chordname -> the spelling thatchord actually accepted
def findthatchord():
	"""Where thatchord actually is, or None.

	The folder is called ThatChord and the script inside it thatchord.py, which
	is two different capitalisations of one word - so rather than guess, match
	the names without regard to case and use whatever is really on disk. A mac
	would let "thatchord/thatchord.py" find "ThatChord/thatchord.py" all on its
	own, but relying on that is how the EM.png / Em.png mess happened.

	It gets run with its own folder as the working directory, in case it loads
	config from next to itself, which is why the output folder has to be handed
	over as an absolute path."""
	if THATCHORD:                                   # told explicitly where it is
		return os.path.abspath(THATCHORD) if os.path.isfile(THATCHORD) else None

	def scriptin(folder):
		"""a file in this folder named thatchord.py, whatever its capitals"""
		if not os.path.isdir(folder): return None
		for name in sorted(os.listdir(folder)):
			if name.lower() == "thatchord.py":
				return os.path.abspath(os.path.join(folder, name))
		return None

	for where in THATCHORD_SEARCH:
		here = scriptin(where)
		if here: return here
		if not os.path.isdir(where): continue
		for name in sorted(os.listdir(where)):       # ...or in a ThatChord folder
			if name.lower() != "thatchord": continue
			inside = scriptin(os.path.join(where, name))
			if inside: return inside
	return None

thatchordpath = findthatchord()
candrawchords = thatchordpath is not None


# The trailing b5 / #9 / b5b7 of a chord name, once the root is out of the way.
# The root has to be taken off in code rather than in the pattern: let the regex
# do it and it backtracks, matching Bb9 as B with an altered 9th instead of Bb
# with a 9th.
ALTERATIONS = re.compile(r'^(.*?)((?:[#b](?:5|6|7|9|11|13))+)$')

SHARPNOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLATNOTES  = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
NOTEPITCH = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
	'E#': 5, 'Fb': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
	'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11}


def everykeyfor(chordname):
	"""The same chord in all twelve keys, spelled with sharps and with flats.

	The web version transposes a song as you read it, but a diagram is a
	picture on disk: press + and the picture has to be there already. Only the
	root moves (and the bass note of a slash chord) - the quality is the
	player's instruction and is carried across untouched, so Am7b5 becomes
	Bm7b5 and never anything else."""
	pieces = []
	for part in chordname.split('/'):
		found = re.match(r'^([A-G][#b]?)(.*)$', part)
		if not found or found.group(1) not in NOTEPITCH: return []
		pieces.append((NOTEPITCH[found.group(1)], found.group(2)))
	allkeys = set()
	for steps in range(12):
		for notes in (SHARPNOTES, FLATNOTES):
			allkeys.add('/'.join(notes[(pitch + steps) % 12] + rest
				for pitch, rest in pieces))
	return sorted(allkeys - {chordname})


def thatchordspellings(chordname):
	"""The names to try, in order: what the book calls the chord, then the same
	chord in thatchord's own syntax.

	thatchord writes alterations in parentheses - Am7(b5), C7(#9) - and knows
	nothing of Am7b5, which is how a person writes it and therefore what is in
	the xml. (The xml can't hold the bracketed form anyway: chordadder strips
	parentheses out of a chord line.) Deriving the second spelling instead of
	keeping a list of the chords that need it means an altered chord nobody has
	typed yet works the first time it turns up.

	Only the part in front of a slash is respelled, so Am7b5/Eb follows Am7b5.
	A root's own flat is safe because the root is matched first: Bb9 keeps its
	Bb, and Bb5 is left alone because a power chord's 5 has no b or # on it."""
	root, slash, bass = chordname.partition('/')
	if not root or root[0] not in "ABCDEFG": return [chordname]
	note = root[:2] if len(root) > 1 and root[1] in "#b" else root[:1]
	found = ALTERATIONS.match(root[len(note):])
	if not found: return [chordname]
	quality, alterations = found.groups()
	return [chordname, note + quality + '(' + alterations + ')' + slash + bass]


def diagramfor(instrument, chordname):
	"""The png for this chord on this instrument, drawing it with thatchord if
	it isn't there yet. Returns the path, or None if thatchord can't play it."""
	folder = diagramroot + instrument['diagramdir'] + "/"
	diagramdir = instrument['diagramdir']

	if diagramdir not in diagramsondisk:
		os.makedirs(folder, exist_ok=True)
		ondisk = {}
		for name in os.listdir(folder):
			ondisk.setdefault(name.lower(), []).append(name)
		diagramsondisk[diagramdir] = ondisk
		cannotplay[diagramdir] = set()
		reconciled[diagramdir] = set()
	ondisk = diagramsondisk[diagramdir]

	wanted = chordname.replace('/', '_') + ".png"   # filenames can't have slashes
	samename = ondisk.setdefault(wanted.lower(), [])
	if wanted in samename: return folder + wanted

	if samename and not candrawchords:
		# A file named for another chord is in the way and we have no way to draw
		# the right one. Moving it aside would leave this chord with no diagram
		# at all, which is worse than the wrong grid, so leave it and say so.
		stillclashing[chordname] = samename[0]
		return folder + samename[0]

	if samename:        # something named for another chord is sitting in the way
		# The grid inside it belongs to that other chord - EM.png is E major
		# where Em.png is E minor, and a mac's disk can't hold both at once - so
		# it is no use here: move it out of the way and draw the real one.
		# Renaming it instead would keep the wrong grid under the right name,
		# which is worse than an error message.
		#
		# Only once per filename per run, though. A second chord folding to the
		# same name means the xml still holds two spellings of one chord, and
		# moving the file aside again would just have the two of them taking
		# turns redrawing it for the rest of the build.
		if wanted.lower() in reconciled[diagramdir]:
			stillclashing[chordname] = samename[0]
			return folder + samename[0]
		reconciled[diagramdir].add(wanted.lower())
		for found in list(samename):
			os.replace(folder + found, folder + found + ".wrongcase")
			movedaside[found] = chordname
			samename.remove(found)

	if not candrawchords: return None
	if chordname in cannotplay[diagramdir]: return None    # asked already, no luck

	for askfor in thatchordspellings(chordname):
		was = set(os.listdir(folder))
		drawit = subprocess.run([sys.executable, thatchordpath, askfor,
			"--instrument", instrument['thatchord'],
			"--directory", os.path.abspath(folder), "--output", "NONE"],
			cwd=os.path.dirname(thatchordpath), capture_output=True, text=True)
		if drawit.returncode != 0: continue

		# Whatever thatchord decided to call it, the file we want is the one
		# that just appeared - don't try to predict the name, especially for a
		# respelled chord where it would have parentheses in it.
		if not os.path.isfile(folder + wanted):
			appeared = [n for n in os.listdir(folder)
			            if n not in was and n.lower().endswith(".png")]
			if len(appeared) != 1: continue
			os.replace(folder + appeared[0], folder + wanted)
		if askfor != chordname: respelled[chordname] = askfor
		samename.append(wanted)
		print("   drew", folder + wanted,
			("(asked for %s)" % askfor) if askfor != chordname else "")
		return folder + wanted

	cannotplay[diagramdir].add(chordname)
	return None


def writechordtable(songkey):
	chordlist = songbook[songkey][3]
	if len(chordlist) == 0: print("NO CHORDS: ", songkey)
	diagramheight = 50
	# The diagrams are not all one shape — 140x150 guitar, 100x150 uke, 120x170
	# for the 5-string. Only the height is set on each <img>, so each keeps its
	# own proportions; this is just a minimum width for the column heading,
	# worked out from the widest shape.
	headingwidth = round(diagramheight * 140 / 150) + 4

	tablerows = ['<tr><th></th>' + ''.join(
		'<th width=%d>%s</th>' % (headingwidth, instrument['heading'])
		for instrument in chosen_instruments) + '</tr>']

	for chordname in chordlist.split():
		# draw it for every instrument, not just the columns in this edition, so
		# one build fills in the lot and the next build of any edition is instant
		for instrument in every_instrument: diagramfor(instrument, chordname)

		# and, if asked, the same chord in every other key, so the web version
		# has a picture ready whichever way you transpose. diagramfor returns
		# straight away for anything already on disk, so the cost is paid once.
		if drawallkeys:
			for otherkey in everykeyfor(chordname):
				if otherkey in keysdrawn: continue
				keysdrawn.add(otherkey)
				for instrument in every_instrument:
					diagramfor(instrument, otherkey)

		row = '<tr><td><i>' + chordname + '</i></td>'
		for instrument in chosen_instruments:
			imagefile = diagramfor(instrument, chordname)   # already drawn by now
			if imagefile is None:     # thatchord can't play it: a grid to fill in by hand
				imagefile = diagramroot + instrument['diagramdir'] + "/empty.png"
				chordswithoutdiagrams[instrument['heading']].add(chordname)
			row += ('<td><img style="display:block" height=' + str(diagramheight)
			        + ' src="' + imagefile.replace("#", "%23") + '"></td>')
		tablerows.append(row + '</tr>')

	htmlfilehandle.write('<div class="chords" style="z-index:0">'
		'<table border=0 style="width:auto; margin-left:auto; border-collapse:collapse;">'
		+ '\n'.join(tablerows) + '</table></div>')


def readinsongs(parsedxml):
	try:
		for songnode in parsedxml.getElementsByTagName("song"):
			artist = alltext(songnode.getElementsByTagName("artist")[0]).strip()
			artist = re.sub("&", "&amp;", artist)
			songtitle = alltext(songnode.getElementsByTagName("songtitle")[0]).strip()
			songtitle = re.sub("&", "&amp;", songtitle)

			if andymode:
				candidate = artist + " - " + songtitle
				if candidate not in andywantedsongs: continue
				print("adding :", candidate)
				andywantedsongs.remove(candidate)

			lyrics = alltext(songnode.getElementsByTagName("lyrics")[0], markchorus=True)
			# swap out ampersands, strip trailing whitespace and leading newlines
			lyrics = re.sub("&", "&amp;", lyrics).rstrip().strip("\n")
			linecount = lyrics.count("\n") + 1

			overflow = (linecount - FIRSTPAGE) % NEXTPAGE
			if linecount > FIRSTPAGE and 0 < overflow < 15:
				print("might save a page by cutting", overflow, "lines:", linecount, "lines", songtitle)

			chordlist = alltext(songnode.getElementsByTagName("chords")[0]) if usechords else ""
			if "When The Saints Go Marching In" in songtitle:
				lyrics += '<p><img src="saints.jpg" />'   # this is still filthy

			if orderbytitle: sortkey = (songtitle + artist).lower().replace(" ", "")
			else:            sortkey = (artist + songtitle).lower().replace(" ", "")
			titlesortkey = (songtitle + artist).lower().replace(" ", "")

			pagecount = 1 + (linecount - 1 - FIRSTPAGE + NEXTPAGE) // NEXTPAGE
			if sortkey in songbook:
				print("DUPLICATE KEY, one of these will be lost:", artist, "-", songtitle)
			songbook[sortkey] = [artist, songtitle, lyrics, chordlist, pagecount]
			songkeybytitle[titlesortkey] = sortkey
	except Exception as problem:
		print("failure on reading song:", songtitle, "-", problem)


def writetableofcontents():
	htmlfilehandle.write('<div class="tocheader"><h1>songlist by artist</h1>'
		'<span class="tocnote">(these are links, click to follow)</span></div>')
	htmlfilehandle.write('<ul class="toc">')
	for songkey in sorted(songbook.keys()):
		htmlfilehandle.write('<li class="tocline1"><a href="#' + songkey + '">'
			+ songbook[songkey][0] + ' - ' + songbook[songkey][1] + "</a>\n")
	htmlfilehandle.write("</ul>\n")

	htmlfilehandle.write('<div class="tocheader"><h1>songlist by title</h1>'
		'<span class="tocnote">(these are links, click to follow)</span></div>')
	htmlfilehandle.write('<ul class="toc">')
	for titlekey in sorted(songkeybytitle.keys()):
		songkey = songkeybytitle[titlekey]
		htmlfilehandle.write('<li class="tocline1"><a href="#' + songkey + '">'
			+ songbook[songkey][1] + ' - ' + songbook[songkey][0] + "</a>\n")
	htmlfilehandle.write("</ul>\n")


def writesong(songkey, pagesinthissong):
	"""write one song, and return the new (currentlyodd, nextpagenumber)"""
	global currentlyodd, nextpagenumber
	htmlfilehandle.write('<div class="song">')
	anchor = '<a name="' + songkey + '" id="' + songkey + '"></a>'
	if orderbytitle:
		htmlfilehandle.write('<h1>' + anchor + '<span class="songtitle">' + songbook[songkey][1] + '</span> - ')
		htmlfilehandle.write('<span class="artist">' + songbook[songkey][0] + '</span></h1>')
	else:
		htmlfilehandle.write('<h1>' + anchor + '<span class="artist">' + songbook[songkey][0] + '</span> - ')
		htmlfilehandle.write('<span class="songtitle">' + songbook[songkey][1] + '</span></h1>')

	htmlfilehandle.write('<div class="chords" style="position:absolute;top:0;right:0;z-index:1;">')
	if usechords: writechordtable(songkey)
	htmlfilehandle.write("</div>")   # chords
	# the leading newline gives one blank line under the title; lyrics sit on top of the chords
	htmlfilehandle.write('\n<div class="lyrics" style="position:relative;z-index:2;">'
		+ songbook[songkey][2] + '</div>')
	htmlfilehandle.write('</div>')   # song

	if pagesinthissong % 2 == 1: currentlyodd = not currentlyodd
	nextpagenumber += pagesinthissong


def fullpageimage(imagefile, label):
	"""One of the chart pages at the back. The label is carried on the div so
	the web version can list them in its contents without keeping its own copy
	of the names - same idea as reading the instrument columns out of the chord
	table headings. Nothing is printed from it, so the pdf is unchanged."""
	anchor = "chart-" + re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')
	htmlfilehandle.write('<div class="song" id="%s" data-chart="%s">'
		'<a name="%s"></a>\n<img src="%s">\n</div>\n'
		% (anchor, label, anchor, imagefile))


# ---------------------------------------------------------------- arguments

if len(sys.argv) < 2: sys.exit(USAGE)

lulumode, andymode, openwhendone = False, False, True
drawallkeys = False
keysdrawn = set()      # chords drawn only because of allkeys, so we skip repeats
chosen_instruments = []          # entries from instrument_table, in column order

for argument in sys.argv[2:]:
	for word in re.split(r'[\s,]+', argument.lower()):
		if not word: continue
		if word in corrected_word:
			print("note:", repr(word), "- assuming you meant", repr(corrected_word[word]))
			word = corrected_word[word]
		if word == 'lulu':
			lulumode = True
			print("running in lulu mode")
		elif word == 'andy':
			andymode = True
			orderbytitle = True
			print("running in andy mode")
		elif word == 'noopen':
			openwhendone = False
		elif word == 'allkeys':
			drawallkeys = True
			print("drawing every chord in all twelve keys - slow the first time,"
				" instant after that")
		elif word in instrument_table:
			instrument = instrument_table[word]
			already = [i['diagramdir'] for i in chosen_instruments]
			if instrument['diagramdir'] not in already:   # first mention wins the position
				chosen_instruments.append(instrument)
		else:
			sys.exit("don't know what to do with " + repr(word) + "\n\n" + USAGE)

if not chosen_instruments:
	chosen_instruments = [instrument_table['guitar'], instrument_table['uke']]

for instrument in chosen_instruments:
	print("column %-10s reads from %s%s/" % (instrument['heading'],
		diagramroot, instrument['diagramdir']))

# A chord with no diagram gets drawn on the spot, into every instrument's folder
# rather than only this edition's, so the first build after adding a song is
# slow and every build after it is instant.
if candrawchords:
	print("missing diagrams get drawn with", thatchordpath, "as we go")
else:
	print("CAN'T FIND THATCHORD, so every chord you haven't already got stays blank.")
	if THATCHORD:
		print("   THATCHORD is set to", repr(THATCHORD), "and there's no file there.")
	else:
		print("   looked for thatchord.py, and for a ThatChord folder holding it, in:")
		print("     ", ", ".join(os.path.abspath(w) for w in THATCHORD_SEARCH))
	print("   put the full path in THATCHORD at the top of this file.")

chordswithoutdiagrams = {i['heading']: set() for i in chosen_instruments}

xmlfilename = sys.argv[1]
discardmode = "discard" in xmlfilename


def instrumentphrase():
	"""'guitar & uke', or 'guitar, uke & banjo' — for the title page"""
	names = [i['heading'].lower() for i in chosen_instruments]
	if len(names) == 1: return names[0]
	return ", ".join(names[:-1]) + " &amp; " + names[-1]


basename = "songbook-" + VERSION + "-" + "-".join(
	i['slug'] for i in chosen_instruments)
if discardmode: basename += "-discards"
if andymode:    basename += "-andy"
if lulumode:    basename += "-lulu"
htmlfilename, pdffilename, oldpdfname = basename + ".html", basename + ".pdf", basename + ".old"

print(xmlfilename, htmlfilename, pdffilename, oldpdfname)

# andy mode takes a list of song titles and generates the sorted-by-title version
andywantedsongs = []
if andymode:
	with open('andy-songbook.txt', 'r') as listfile:
		andywantedsongs = [line.strip().replace("&", "&amp;") for line in listfile]

# ---------------------------------------------------------------- read

songbook = {}        # sortkey -> [artist, title, lyrics, chords, pagecount]
songkeybytitle = {}  # title sortkey -> sortkey into songbook

readinsongs(xml.dom.minidom.parse(xmlfilename))
print(len(songbook), "songs read in")

# ---------------------------------------------------------------- write html

htmlfilehandle = open(htmlfilename, 'w', encoding='utf-8')

htmlfilehandle.write("""<html><meta charset="UTF-8"><?xml version="1.0" encoding="utf-8"?>
		<?xml-stylesheet type="text/css" href="songbookprint.css"?>
		<link rel="stylesheet" type="text/css" href="songbookprint.css" />

		\n<body>\n""")

if not lulumode:   # for lulu, the cover and inside cover are a separate file
	htmlfilehandle.write("""
		<div class="titlepage">
		<br>{booktitle}
		<br>{edition} chords edition
		<br>version {version}<br>{today}
		<br>shorter and cleaner than ever!<br>
		{weblink}</div>
		<div class="titlepage">this page left blank for printing<br>delete before sending to lulu</div>""".format(
			booktitle = DISCARDTITLE if discardmode else BOOKTITLE,
			ordering  = "song title" if orderbytitle else "artist first name",
			edition   = instrumentphrase(),
			version   = VERSION,
			today     = datetime.date.today().isoformat(),
			weblink   = ("<br>pdf: " + (DISCARDURL if discardmode else WEBURL))
			            if (DISCARDURL if discardmode else WEBURL) else ""))

if not andymode: writetableofcontents()

# ---------------------------------------------------------------- the songs

currentlyodd = True     # we always start on an odd page
nextpagenumber = 13     # starting page
heldbacksongs = []      # 2+ page songs that would otherwise start on an odd page

for songkey in sorted(songbook.keys()):
	pagesinthissong = songbook[songkey][4]

	if pagesinthissong > 1 and currentlyodd:
		heldbacksongs.append(songkey)   # wait for an even page so it's a spread
		continue
	writesong(songkey, pagesinthissong)

	while not currentlyodd and heldbacksongs:
		heldkey = heldbacksongs.pop(0)
		writesong(heldkey, songbook[heldkey][4])

while heldbacksongs:    # anything still waiting at the end goes in regardless
	heldkey = heldbacksongs.pop(0)
	writesong(heldkey, songbook[heldkey][4])

# ---------------------------------------------------------------- back matter

for chartimage, chartlabel in [
		("guitar-chords-chord-chart-enlarged-300dpi.jpg", "guitar chords"),
		("ukechords-larger.jpg",                          "uke chords"),
		("piano_chords.jpg",                              "piano chords"),
		("banjochart-larger.jpg",                         "banjo chords")]:
	fullpageimage(chartimage, chartlabel)

if not (lulumode or andymode or discardmode):
	changesfilename = 'changes' + VERSION + '.txt'
	if os.path.isfile(changesfilename):
		htmlfilehandle.write('<div class="song" style="white-space: pre-wrap;">')
		htmlfilehandle.write('<h1>Changes, v' + VERSION + '</h1>'
			+ open(changesfilename, encoding='utf-8').read())
		htmlfilehandle.write('</div>')
	else:
		print("no", changesfilename, "- skipping the changes page")

if andymode: writetableofcontents()   # short version: the toc fits at the end
htmlfilehandle.write('</body></html>\n')
htmlfilehandle.close()

# ---------------------------------------------------------------- run prince

workingdir = os.getcwd() + "/"
if os.access(workingdir + oldpdfname, os.F_OK): os.remove(workingdir + oldpdfname)
if os.access(workingdir + pdffilename, os.F_OK):
	os.rename(workingdir + pdffilename, workingdir + oldpdfname)

# one line per instrument, each chord once, so the list is short enough to read
for heading, chords in chordswithoutdiagrams.items():
	if not chords: continue
	distinct = sorted(chords, key=lambda c: (c.upper(), c))
	why = "thatchord can't play" if candrawchords else "no diagram for"
	print("%s: %s %d chords, so they're blank grids: %s"
		% (heading, why, len(distinct), " ".join(distinct)))

if movedaside:
	print()
	print("moved %d diagram(s) aside: the filename was for a different chord, so"
		% len(movedaside))
	print("the grid in it was the wrong one. Each has been redrawn correctly.")
	for found in sorted(movedaside):
		print("   %-14s -> %-14s (%s wanted it, and that isn't it)"
			% (found, found + ".wrongcase", movedaside[found]))
	print("   delete the .wrongcase files once the pdfs look right")

if respelled:
	print()
	print("%d chord(s) only drew once rewritten the way thatchord spells"
		% len(respelled))
	print("alterations. The book still prints the name in the xml:")
	for chordname in sorted(respelled, key=lambda c: (c.upper(), c)):
		print("   %-12s asked for as %s" % (chordname, respelled[chordname]))

if stillclashing:
	print()
	if not candrawchords:
		print("These chords are using a diagram named for a DIFFERENT chord, so the")
		print("grid is wrong - EM.png is E major where Em.png is E minor, and the disk")
		print("can't tell them apart. Can't fix it without thatchord: point THATCHORD")
		print("at it and the right diagrams get drawn.")
	else:
		print("THE XML STILL HAS TWO SPELLINGS OF THE SAME CHORD. The disk can only")
		print("hold one diagram for each pair, so one of them prints the wrong grid.")
		print("Rename one of each in the xml - Bbmaj7 rather than BbM7, say:")
	for chordname in sorted(stillclashing, key=lambda c: (c.upper(), c)):
		print("   %-8s is getting %s" % (chordname, stillclashing[chordname]))
if andymode: print("not found in the xml: ", andywantedsongs)

print("now running prince:", PRINCE, workingdir + htmlfilename, "-o", workingdir + pdffilename)
princeresult = subprocess.run([PRINCE, workingdir + htmlfilename, "-o", workingdir + pdffilename])
if princeresult.returncode == 0:
	if openwhendone: subprocess.run(["open", workingdir + pdffilename])
else:
	print("prince failed with exit code", princeresult.returncode, "- not opening the pdf")
