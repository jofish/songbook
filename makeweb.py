"""makeweb.py — turn the print html songbookmaker feeds to Prince into a web page.

	python3 makeweb.py songbook-10.0-guitar-uke.html songbook-web.html

Adds a per-instrument class to every chord cell so columns can be toggled, drops
the print-only front matter, expands [CHORUS] references, and wires up a control
bar. Uses songbookweb.css instead of the print css.

The instrument columns are read out of the chord-table heading row, so whatever
songbookmaker put in the book is what you get checkboxes for -- there is nothing
here to keep in step with songbookmaker's instrument_table.
"""
import re, sys, os

# Chorus expansion. The chorus itself is marked up in the source xml with
# <chorus>...</chorus> (see choruswrap.py), songbookmaker turns that into a
# <span class="chorusblock">, and this script swaps every later "[CHORUS]"
# reference for the real words. Nothing is guessed. Set False to drop the
# feature and its checkbox from the page.
EXPAND_CHORUSES = True

# Squashing blank lines. The print book is padded on purpose - some songs carry
# extra blank lines so that page two starts at a verse - and on screen that
# padding is just a hole you scroll through. A run LONGER than MAXBLANKS blank
# lines comes out as KEEPBLANKS of them, so at 2 and 2 nothing anywhere shows
# more than two blank lines in a row.
MAXBLANKS  = 2
BOOKNAME   = "a songbook"  # put your own in my_settings.py; see songbookmaker
TABSTOP    = 4            # matches tab-size in songbookweb.css and songbookprint.css

# Your own settings, if you have them, same file songbookmaker reads.
try:
	from my_settings import BOOKNAME          # noqa: F401
except ImportError:
	pass

KEEPBLANKS = 2

from chorusref import isbarereference, istailreference, TAIL_MARKER

CHORUS_BLOCK = re.compile(r'<span class="chorusblock">(.*?)</span>', re.S)

# Which pdfs the download panel offers, in order. The filename is matched against
# whatever songbookmaker actually wrote, so these are the instrument SLUGS from
# its instrument_table, not the headings printed in the book.
pdf_downloads = [
	("songbook-VERSION-guitar-uke.pdf",       "guitar &amp; uke",        "the standard book"),
	("songbook-VERSION-guitar-uke-banjo.pdf", "guitar, uke &amp; banjo", "adds banjo diagrams"),
	("songbook-VERSION-mandolin.pdf",         "mandolin",                "mandolin diagrams only"),
	("songbook-VERSION-bariuke.pdf",          "baritone uke",            "baritone / chicago / linear tuning"),
	("songbook-VERSION-guitar-uke-banjo-mandolin-bariuke.pdf", "every instrument",
	 "not recommended &mdash; five columns of diagrams crowd the lyrics badly"),
]

if len(sys.argv) < 3:
	sys.exit("usage: python3 makeweb.py print.html web.html [discard]")
printfilename, webfilename = sys.argv[1], sys.argv[2]

# The discard pile is the same page with a different name on it and only its
# own pdf to offer. Everything else - the chords, the transposing, the
# scrolling - is identical, so it is the same script with a word on the end
# rather than a second copy to keep in step.
# The name and the url are songbookmaker's - DISCARDTITLE and DISCARDURL at
# the top of it - so the two agree about what this book is called.
isdiscardpile = len(sys.argv) > 3 and sys.argv[3].lower() == 'discard'
booktitle = "the discard pile" if isdiscardpile else BOOKNAME
if isdiscardpile:
	# songbookmaker appends -discards whenever the xml filename says discard
	pdf_downloads = [("songbook-VERSION-guitar-uke-banjo-mandolin-discards.pdf",
		"guitar, uke, banjo &amp; mandolin", "the whole discard pile")]
printhtml = open(printfilename, encoding='utf-8').read()

versionmatch = re.search(r'songbook-([0-9][0-9_.]*)-', os.path.basename(printfilename))
bookversion = versionmatch.group(1) if versionmatch else ""
if not bookversion:
	print("note: couldn't read a version out of the filename; pdf links may be wrong")

# ---- which instruments are in this book, and in what order -------------------
headingrow = re.search(r'<tr><th></th>((?:<th[^>]*>[^<]*</th>)+)</tr>', printhtml)
if not headingrow:
	sys.exit("couldn't find a chord table header - is this a songbookmaker html file?")

columnheadings = re.findall(r'<th[^>]*>([^<]*)</th>', headingrow.group(1))

def classname(heading):
	"""'BariUke' -> 'bariuke'; whatever the heading is, make it safe in a class"""
	return re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')

columnclasses = [classname(h) for h in columnheadings]
print("instruments found:", ", ".join("%s (.c-%s)" % (h, c)
	for h, c in zip(columnheadings, columnclasses)))

if len(set(columnclasses)) != len(columnclasses):
	sys.exit("two columns reduce to the same css class: " + str(columnclasses))

# ---- tag every chord cell with its instrument -------------------------------
def tagheadingrow(match):
	cells = re.findall(r'<th[^>]*>([^<]*)</th>', match.group(1))
	tagged = ''.join('<th class="c-%s">%s</th>' % (cls, text)
		for cls, text in zip(columnclasses, cells))
	return '<tr><th class="c-name"></th>' + tagged + '</tr>'

printhtml = re.sub(r'<tr><th></th>((?:<th[^>]*>[^<]*</th>)+)</tr>', tagheadingrow, printhtml)

def tagchordrow(match):
	chordname, diagramcells = match.group(1), match.group(2)
	cells = re.findall(r'<td>(.*?)</td>', diagramcells, re.S)
	tagged = ''.join('<td class="c-%s">%s</td>' % (cls, cell)
		for cls, cell in zip(columnclasses, cells))
	return '<tr><td class="c-name"><i>%s</i></td>%s</tr>' % (chordname, tagged)

printhtml = re.sub(r'<tr><td><i>(.*?)</i></td>((?:<td>.*?</td>\s*)+)</tr>',
	tagchordrow, printhtml, flags=re.S)

# ---- strip the print-only bits ----------------------------------------------
printhtml = re.sub(r'<div class="titlepage">.*?</div>', '', printhtml, flags=re.S)
printhtml = printhtml.replace('style="position:absolute;top:0;right:0;z-index:1;"', '')
printhtml = printhtml.replace('style="position:relative;z-index:2;"', '')
printhtml = printhtml.replace(' style="z-index:0"', '')
# Drop the fixed height so the diagram-size slider can drive it. Keep the real
# pixel dimensions as width/height attributes: the browser uses them for the
# aspect ratio, so the box is the right shape even before the image loads -- and
# stays right when the script detaches it again further down the page.
# The start-of-frame markers, which are the ones carrying the dimensions.
# C4, C8 and CC sit in the same range and are something else entirely.
SOFMARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
NOPAYLOAD = {0x01, 0xD8, 0xD9} | set(range(0xD0, 0xD8))

def imagesize(filename):
	"""(width, height) for a png or a jpeg, read from the header. No pillow."""
	try:
		with open(filename, 'rb') as f:
			head = f.read(24)
			if head[:8] == b'\x89PNG\r\n\x1a\n' and len(head) >= 24:
				return (int.from_bytes(head[16:20], 'big'),
				        int.from_bytes(head[20:24], 'big'))
			if head[:2] != b'\xff\xd8': return None
			f.seek(2)                      # past the start-of-image marker
			while True:
				marker = f.read(2)
				if len(marker) < 2 or marker[0] != 0xFF: return None
				if marker[1] == 0xFF:      # fill byte, not a marker yet
					f.seek(-1, 1)
					continue
				if marker[1] in NOPAYLOAD: continue
				if marker[1] in SOFMARKERS:
					f.read(3)              # segment length, then sample precision
					tall = int.from_bytes(f.read(2), 'big')
					wide = int.from_bytes(f.read(2), 'big')
					return (wide, tall) if wide and tall else None
				length = int.from_bytes(f.read(2), 'big')
				if length < 2: return None
				f.seek(length - 2, 1)
	except OSError:
		return None

sizecache, sizesfound, sizesmissed = {}, 0, 0

def relabelimage(match):
	global sizesfound, sizesmissed
	path = match.group(1)
	diskpath = path.replace('%23', '#')
	if diskpath not in sizecache: sizecache[diskpath] = imagesize(diskpath)
	size = sizecache[diskpath]
	if size:
		sizesfound += 1
		return ('<img loading="lazy" width="%d" height="%d" data-src="%s" src="%s">'
		        % (size[0], size[1], path, path))
	sizesmissed += 1
	return '<img loading="lazy" data-src="%s" src="%s">' % (path, path)

printhtml = re.sub(r'<img style="display:block" height=\d+ src="([^"]*)">',
	relabelimage, printhtml)
print("diagram sizes read from disk:", sizesfound, "| not found:", sizesmissed)
if sizesmissed and not sizesfound:
	print("   (run this from the directory that has diagrams/ so the boxes size correctly)")

# Everything else carrying a src: the full-page chart scans at the back of the
# book, and anything an XML file drops in by hand. Only a handful of images,
# but they are the enormous ones -- the guitar chart is 2550x3300, which is
# 34MB of bitmap for 0.2MB of file. Left as they come out of the print build
# they are plain <img src>, so they are fetched and decoded the instant the
# page opens, three hundred songs before anyone could see them, and the
# observer never releases them because it only knows about images with a
# data-src. That is 80MB resident from load, which is what kills the tab on
# iOS ("a problem repeatedly occurred"). Handed over to the observer on the
# same terms as the diagrams they cost nothing until you turn to them.
#
# Done by rewriting whatever tag is already there rather than by naming the
# files, so another chart, or an illustration in a song, needs no code here.
eagerimages = 0

def manageimage(match):
	global eagerimages
	tag = match.group(0)
	if 'data-src' in tag: return tag              # a diagram, already handled
	found = re.search(r'src="([^"]*)"', tag)
	if not found: return tag
	path = found.group(1)
	# Use the web-resolution copy if build.sh has made one. Looked up on disk
	# rather than named here, so a new chart needs no code: drop the scan in,
	# and whatever sips produces beside it gets used.
	webcopy = re.sub(r'\.(jpe?g|png)$', r'-web.\1', path, flags=re.I)
	if webcopy != path and os.path.exists(webcopy.replace('%23', '#')):
		path = webcopy
	size = imagesize(path.replace('%23', '#'))
	eagerimages += 1
	return ('<img loading="lazy" decoding="async" %sdata-src="%s" src="%s">'
	        % ('width="%d" height="%d" ' % size if size else '', path, path))

printhtml = re.sub(r'<img\b[^>]*>', manageimage, printhtml)
print("full-size images handed to the observer:", eagerimages)


# ---- chords across the top, one instrument at a time ------------------------
# The printed page pins a tall narrow table of diagrams to the top right and
# lets the words run underneath it. On a screen that spends a third of the
# width on every song, and on a phone the table was wide enough to need its own
# sideways scroll. The chords sit above the words in nearly every song anyway,
# so on the web they go across the top instead: one labelled row per
# instrument, wrapping to as many lines as the viewport needs.
#
# Rebuilt from the table the print build already emits, so songbookmaker and
# every pdf are untouched. The c-<instrument> class moves onto the group, which
# is what the generated .hide-<instrument> rules key off, so hiding an
# instrument now takes its label with it.
CHORDTABLE = re.compile(r'<table[^>]*>(.*?)</table>', re.S)
CHORDROW   = re.compile(r'<tr>(.*?)</tr>', re.S)
CHORDCELL  = re.compile(r'<t[dh][^>]*class="c-([a-z0-9-]+)"[^>]*>(.*?)</t[dh]>', re.S)

chordgroups = 0

def chordsacross(match):
	global chordgroups
	rows = CHORDROW.findall(match.group(1))
	if not rows: return match.group(0)

	labels = dict(CHORDCELL.findall(rows[0]))          # guitar -> "Guitar"
	perinstrument = {}                                  # guitar -> [(name, img)]
	for row in rows[1:]:
		cells = dict(CHORDCELL.findall(row))
		name = re.sub(r'<[^>]*>', '', cells.get('name', '')).strip()
		for instrument, cell in cells.items():
			if instrument == 'name': continue
			perinstrument.setdefault(instrument, []).append((name, cell.strip()))

	built = []
	for instrument in columnclasses:                    # the print build's order
		if instrument not in perinstrument: continue
		# A blank grid is ambiguous: on a banjo an open G really is "strum it",
		# so a chord nobody could draw must not look like one you play open.
		# The stylesheet puts a ? after these.
		diagrams = ''.join(
			'<span class="chord%s">%s<span class="chordname">%s</span></span>'
			% (' unplayable' if 'empty.png' in cell else '', cell, name)
			for name, cell in perinstrument[instrument])
		built.append('<div class="chordgroup c-%s">'
			'<div class="chordgroupname">%s</div>'
			'<div class="chordrow">%s</div></div>'
			% (instrument, labels.get(instrument, instrument), diagrams))
		chordgroups += 1
	return ''.join(built) if built else match.group(0)

printhtml = CHORDTABLE.sub(chordsacross, printhtml)
print("chord diagrams laid across the top:", chordgroups, "instrument groups")


# ---- pull the two tocs out so we can put them behind a button ---------------
# Each one is a heading plus its <ul>. They go side by side in the panel - by
# artist on the left, by title on the right - so wrap each as its own section
# and let the css lay the pair out in two columns.
tableofcontents = re.findall(r'<div class="tocheader">.*?</ul>', printhtml, re.S)
printhtml = re.sub(r'<div class="tocheader">.*?</ul>', '', printhtml, flags=re.S)

# ---- give every song a searchable data attribute ----------------------------
def addsearchtext(match):
	wholesong = match.group(0)
	names = re.findall(r'<span class="(?:artist|songtitle)">(.*?)</span>', wholesong)
	searchtext = ' '.join(names).lower().replace('"', '&quot;')
	return wholesong.replace('<div class="song">',
		'<div class="song" data-find="%s">' % searchtext, 1)

printhtml = re.sub(r'<div class="song"><h1>.*?</h1>', addsearchtext, printhtml, flags=re.S)

# ---- squash the long gaps the printed page needs and the screen doesn't ------
blankruns_squashed = blanklines_dropped = 0

def squashblanks(match):
	"""Shorten any over-long run of blank lines inside one song's lyrics.

	A line counts as blank only when it is nothing but whitespace. A line
	holding a tag - the <span class="chorusblock"> that opens a chorus, say -
	is left alone even if it shows nothing, because dropping it would take the
	tag with it and break the markup."""
	global blankruns_squashed, blanklines_dropped
	lines = match.group(2).split('\n')
	out, run = [], 0
	for line in lines + ['\x00']:          # sentinel flushes a trailing run
		if line.strip() == '':
			run += 1
			continue
		if run > MAXBLANKS:
			out.extend([''] * KEEPBLANKS)
			blankruns_squashed += 1
			blanklines_dropped += run - KEEPBLANKS
		else:
			out.extend([''] * run)
		run = 0
		out.append(line)
	out.pop()                              # the sentinel
	return match.group(1) + '\n'.join(out) + match.group(3)

printhtml = re.sub(r'(<div class="lyrics"[^>]*>)(.*?)(</div>)', squashblanks,
	printhtml, flags=re.S)
print("blank-line runs over %d squashed to %d: %d runs, %d lines dropped"
	% (MAXBLANKS, KEEPBLANKS, blankruns_squashed, blanklines_dropped))

# ---- bring the deeply-indented blocks back in -------------------------------
# Choruses are indented by hand in the source, and how far was never consistent:
# Piano Man's sits one tab in, Stand By Me's two, The Old Black Rum's four. On a
# phone the deep ones throw away a quarter of the width before a word appears.
#
# The whole block moves together, by the same number of columns, so a chord can
# never drift off the syllable it sits over. The amount is the SMALLEST indent
# in the block, less the indent we are keeping -- take any more and the least
# indented line would hit the margin and the rest would pile up behind it.
#
# A block is a run of consecutive non-blank lines. Verses are safe by
# construction: a verse almost always has one line at column zero, so its
# smallest indent is zero and nothing moves.
INDENTKEPT = 4                           # one tab, which is what Piano Man has

# Markup and entities sit in the middle of a lyrics line and occupy no columns
# (a tag) or exactly one (an entity), so columns are counted over the visible
# text alone.
PIECES  = re.compile(r'<[^>]*>|&[a-zA-Z]+;|&#\d+;|[^<&]+|&')
INDENTOF = re.compile(r'^((?:<[^>]*>)*)( *)')

def spacedout(line):
	"""Tabs to spaces, on real tab stops, counting only what you can see.

	Everything downstream shifts lines sideways, and a tab that survived would
	land on a different stop afterwards and pull its chord with it. Spaces move
	predictably. Rendering is unchanged: the stylesheet is already tab-size 4,
	which is what songbookprint.css has always used."""
	out, column = [], 0
	for piece in PIECES.findall(line):
		if piece.startswith('<'):
			out.append(piece)                     # a tag: no width at all
			continue
		if piece.startswith('&') and piece.endswith(';'):
			out.append(piece); column += 1        # an entity: one column
			continue
		for character in piece:
			if character == '\t':
				width = TABSTOP - (column % TABSTOP)
				out.append(' ' * width); column += width
			else:
				out.append(character); column += 1
	return ''.join(out)

blocksmoved = columnsreclaimed = 0

def unindent(match):
	global blocksmoved, columnsreclaimed
	lines = [spacedout(line) for line in match.group(2).split('\n')]
	isblank = [re.sub(r'<[^>]*>', '', line).strip() == '' for line in lines]

	start = 0
	while start < len(lines):
		if isblank[start]: start += 1; continue
		end = start
		while end < len(lines) and not isblank[end]: end += 1

		smallest = min(len(INDENTOF.match(lines[at]).group(2))
		               for at in range(start, end))
		if smallest > INDENTKEPT:
			shift = smallest - INDENTKEPT
			for at in range(start, end):
				tags, spaces = INDENTOF.match(lines[at]).groups()
				lines[at] = tags + spaces[shift:] + lines[at][len(tags) + len(spaces):]
			blocksmoved += 1
			columnsreclaimed += shift
		start = end

	return match.group(1) + '\n'.join(lines) + match.group(3)

printhtml = re.sub(r'(<div class="lyrics"[^>]*>)(.*?)(</div>)', unindent,
	printhtml, flags=re.S)
print("indented blocks brought in to %d columns: %d blocks, %d columns average"
	% (INDENTKEPT, blocksmoved,
	   round(columnsreclaimed / blocksmoved) if blocksmoved else 0))

# ---- the chart pages at the back get their own line in the contents ---------
# They belong under neither heading - a chord chart has no artist and no title
# - so they go in their own centred row under the two lists. The names come
# from the data-chart songbookmaker put on each one.
chartlinks = re.findall(r'<div class="song" id="(chart-[^"]+)" data-chart="([^"]*)"', printhtml)
chartlist = ''
if chartlinks:
	chartlist = ('<div class="toccharts">'
		+ ' '.join('<a href="#%s">%s</a>' % (anchor, label) for anchor, label in chartlinks)
		+ '</div>')
print("chart pages listed in the contents:", len(chartlinks))

# ---- swap every back-reference for the real chorus ---------------------------
choruses_marked = songs_with_a_chorus = 0

def markchorusreferences(match):
	global choruses_marked, songs_with_a_chorus
	lyrics = match.group(1)
	block = CHORUS_BLOCK.search(lyrics)
	if not block: return match.group(0)
	songs_with_a_chorus += 1
	chorustext = block.group(1)

	# only look for references OUTSIDE the chorus itself, or a chorus that
	# happens to open with the word "chorus" would reference itself
	before, after = lyrics[:block.start()], lyrics[block.end():]

	def swap(segment, isbefore=False):
		global choruses_marked
		lines = segment.split('\n')
		# The label that INTRODUCES the chorus sits just above the block, so it
		# is the last non-blank line of the "before" segment. Expanding it would
		# print the chorus twice in a row.
		introducer = -1
		if isbefore:
			for i in range(len(lines) - 1, -1, -1):
				if lines[i].strip():
					if isbarereference(lines[i]): introducer = i
					break
		out = []
		for lineno, line in enumerate(lines):
			if lineno == introducer:
				out.append(line)
				continue
			marker = TAIL_MARKER.search(line)
			if marker and line[:marker.start()].strip():
				out.append(line[:marker.start()]
					+ '<span class="cref">' + line[marker.start():] + '</span>'
					+ '<span class="cexp">\n' + chorustext + '</span>')
				choruses_marked += 1
			elif isbarereference(line):
				out.append('<span class="cref">' + line + '</span>'
					+ '<span class="cexp">' + chorustext + '</span>')
				choruses_marked += 1
			else:
				out.append(line)
		return '\n'.join(out)

	return ('<div class="lyrics">' + swap(before, isbefore=True)
		+ block.group(0) + swap(after) + '</div>')

if EXPAND_CHORUSES:
	printhtml = re.sub(r'<div class="lyrics"[^>]*>(.*?)</div>', markchorusreferences,
		printhtml, flags=re.S)
	print("songs with a tagged chorus:", songs_with_a_chorus,
		"| references expanded:", choruses_marked)

# ---- where the chords are, so the web version can transpose -----------------
# THIS MUST STAY THE LAST THING THAT TOUCHES THE LYRICS TEXT. What it records
# is LINE NUMBERS, and every pass above moves them: squashing blank lines drops
# a hundred-odd, expanding a chorus inserts whole blocks, and a third of the
# songs come out a different length than the printed build. Record them earlier
# and a third of the book would point at a lyric line instead of a chord line,
# quietly. The self-check below is there to catch exactly that if this ever
# gets moved.
#
# Two attributes go on the song, not a tag round every chord. Wrapping each of
# the 22,000 chords in its own element costs 22,574 dom nodes and about 36MB of
# renderer memory, which is the last thing this page needs; this costs 36kB of
# text (7.6kB over the wire) and no nodes at all. The browser only has to wrap
# the one song it is transposing.
#
#   data-cl   lines that are nothing BUT chords. The line number is enough:
#             every token on such a line is a chord by definition, so the
#             browser can split it up without having to judge anything.
#   data-cm   lines that mix chords and words, as line:col.col.col. These are
#             the ones that need judgement - "Chorus  G  D  A", "D D5 D D5
#             (repeat and fade)" - so the judgement is made here, in python,
#             and the browser is only told where to look.

CHORDNAME = re.compile(r'^[A-G][#b]?(?:m|maj|min|dim|aug|sus|add|M)?[0-9]{0,2}'
	r'(?:sus|add|maj|dim|aug|b5|#5|b9|#9|#11|b13|no3)?[0-9]{0,2}'
	r'(?:/[A-G][#b]?)?$')
# punctuation that shares a line with chords without being one. N.C. is
# "no chord", which is an instruction rather than something to transpose.
CHORDJUNK = re.compile(r'^(?:(?:[()|:,.]|x\d+|\d+x|-{2,})+|N\.?C\.?)$', re.I)
TAGS = re.compile(r'<[^>]*>')

# A chord often turns up wearing notation: a bar line out of "| B B A D | E |",
# brackets round one that is optional, or the star this book uses to mean strum
# it once. The decoration is part of the instruction, so it stays exactly where
# it was and only the chord inside it moves: D* transposes to E*, never to E.
# One decorated chord used to disqualify its whole line, which quietly left 116
# lines and 367 chords behind in the old key.
DECORATED = re.compile(r'^([|(\[]*)([A-G][#b]?[^\s|()\[\]*]*)(\*?)([|)\]]*)$')

def chordin(token):
	"""the chord inside whatever is wrapped round it, or None if it is not one"""
	worn = DECORATED.match(token)
	if not worn: return None
	return worn.group(2) if CHORDNAME.match(worn.group(2)) else None

def visible(line):
	"""what the reader sees: columns are counted over this, never over the
	markup, because the browser will be working on text nodes"""
	return TAGS.sub('', line)

def ischordline(line):
	tokens = visible(line).split()
	return bool(tokens) and all(chordin(t) or CHORDJUNK.match(t)
		for t in tokens)

# The vocabulary that legitimately sits one space from a run of chords.
SECTIONLABEL = re.compile(r'^(?:intro|outro|chorus|verse|bridge|solo|tag|coda'
	r'|riff|instrumental|interlude|ending|pre-chorus|refrain)[:.,]?$', re.I)
# A chord carrying a note to the player - B(b9), F(bar), Em7(hold). Not every
# one of these parses as a chord, but none of them is a word, so they must not
# make their neighbours look like prose.
ANNOTATEDCHORD = re.compile(r'^[A-G][#b]?[A-Za-z0-9#b/]*\(')

def isword(token):
	"""an ordinary English word, as opposed to a chord or notation"""
	if chordin(token) or CHORDJUNK.match(token): return False
	if SECTIONLABEL.match(token) or ANNOTATEDCHORD.match(token): return False
	# "Year", "John" and "You" are words despite the capital; "I" is a word
	# with no lowercase in it at all.
	return bool(re.search(r'[a-z]', token)) or token == 'I'

def isprose(tokens, which):
	"""True when this chord-shaped token is really just a word.

	A chord floats in whitespace; a word sits one space from its neighbours.
	That is the whole difference between

	    Chorus    G     D   A          <- chords, and they should move
	    A ship came sailing in at dawn <- an article, and it must not
	    Form a D chord, then pick the single strings

	Getting this wrong is the expensive direction: a missed chord stays in the
	old key, but a transposed article turns "A ship came sailing in" into
	"B ship came sailing in"."""
	token, start, end = tokens[which]
	for step, gap in ((-1, start - tokens[which-1][2] if which else None),
	                  (1, tokens[which+1][1] - end if which+1 < len(tokens) else None)):
		if gap is None or gap > 1: continue
		if isword(tokens[which + step][0]):
			return -step        # which way the prose runs: away from the word
	return 0

def chordspots(line):
	tokens = [(m.group(0), m.start(), m.end())
		for m in re.finditer(r'\S+', visible(line))]
	runs = [isprose(tokens, i) if chordin(t) else 0
		for i, (t, s, e) in enumerate(tokens)]
	prose = [bool(r) for r in runs]

	# Prose spreads along a run of single spaces, but only AWAY from the word
	# that started it. "pick the single strings D D B G" names four strings and
	# the run carries rightwards over all of them; "G Am Em C x4 end G" has its
	# word in the middle, and spreading backwards would throw away four real
	# chords to its left.
	for i, step in enumerate(runs):
		if not step: continue
		at = i + step
		while 0 <= at < len(tokens):
			near, far = sorted((at, at - step))
			if tokens[far][1] - tokens[near][2] > 1: break
			prose[at] = True
			at += step

	# A word only wins on a line that is ALL prose. "Outro: G Am Em C x4 end G"
	# has four chords nothing is touching, so the G after "end" is a chord
	# being named, not a word - whereas "Form a D chord, then pick the single
	# strings D D B G" has no confident chord anywhere and stays prose.
	confident = any(chordin(t) and not prose[i]
		for i, (t, s, e) in enumerate(tokens))
	if confident: prose = [False] * len(tokens)

	return [start for i, (token, start, end) in enumerate(tokens)
		if chordin(token) and not prose[i]]

LYRICSBLOCK = re.compile(r'<div class="lyrics"[^>]*>(.*?)</div>', re.S)

purelines = mixedlines = mixedchords = taggedlines = 0
mixedreport = []

def recordchords(chunk):
	"""chunk is one song, from just after <div class="song" to the next one"""
	global purelines, mixedlines, mixedchords, taggedlines
	found = LYRICSBLOCK.search(chunk)
	if not found: return ''                     # a chart page has no lyrics
	title = re.search(r'<h1[^>]*>(.*?)</h1>', chunk, re.S)
	title = TAGS.sub('', title.group(1)).strip() if title else '?'

	pure, mixed = [], []
	for number, line in enumerate(found.group(1).split('\n')):
		if not visible(line).strip(): continue
		if ischordline(line):
			pure.append(number)
			if '<' in line: taggedlines += 1
		else:
			spots = chordspots(line)
			if not spots: continue
			mixed.append('%d:%s' % (number, '.'.join(str(c) for c in spots)))
			mixedchords += len(spots)
			mixedreport.append((title, len(spots),
				len(visible(line).split()), visible(line).strip()[:70]))
	purelines += len(pure)
	mixedlines += len(mixed)

	out = ''
	if pure:  out += ' data-cl="%s"' % ','.join(str(n) for n in pure)
	if mixed: out += ' data-cm="%s"' % ','.join(mixed)
	return out

songchunks = printhtml.split('<div class="song"')
printhtml = songchunks[0] + ''.join('<div class="song"' + recordchords(chunk) + chunk
	for chunk in songchunks[1:])
print("chord positions recorded: %d chord-only lines, %d mixed lines holding %d chords"
	% (purelines, mixedlines, mixedchords))

# ---- read it back and prove it points at what it says it does ---------------
# Cheap, and it turns "the indices rotted because a pass got added below this
# one" from a silent wrong-key bug into a build failure.
wrong = []
for chunk in printhtml.split('<div class="song"')[1:]:
	found = LYRICSBLOCK.search(chunk)
	if not found: continue
	lines = found.group(1).split('\n')
	opening = chunk[:chunk.index('>')]
	for attribute, check in (('data-cl', 'chord-only'), ('data-cm', 'mixed')):
		got = re.search(attribute + r'="([^"]*)"', opening)
		if not got: continue
		for entry in got.group(1).split(','):
			number = int(entry.split(':')[0])
			if number >= len(lines):
				wrong.append((attribute, number, 'past the end of the song')); continue
			line = lines[number]
			if check == 'chord-only' and not ischordline(line):
				wrong.append((attribute, number, visible(line).strip()[:50]))
			if check == 'mixed':
				for column in entry.split(':')[1].split('.'):
					token = visible(line)[int(column):].split(' ')[0]
					if not chordin(token):
						wrong.append((attribute, number, 'col %s is %r' % (column, token)))
if wrong:
	for attribute, number, why in wrong[:10]:
		print("   %s line %d: %s" % (attribute, number, why))
	sys.exit("chord positions do not match the page - %d bad entries" % len(wrong))
print("   checked against the finished page: every recorded line is what it claims")
if taggedlines:
	print("   note: %d chord lines carry markup (an expanded chorus); the browser"
		% taggedlines)
	print("         will have to walk text nodes on those, not just split a string")

reportfile = os.path.splitext(webfilename)[0] + '-chordlines.txt'
with open(reportfile, 'w', encoding='utf-8') as handle:
	handle.write("Lines where chords and words share a line, so the marker had to\n"
		"decide token by token. Read these: a wrong call here transposes a\n"
		"lyric, or leaves a chord behind in the old key.\n\n")
	for title, hits, total, line in mixedreport:
		handle.write("%-34s %d of %-3d |%s\n" % (title[:34], hits, total, line))
print("   lines to eyeball written to", reportfile)

# ---- which diagrams transposing would ask for that nobody has drawn ---------
# The page can retune the words on its own, but a diagram is a picture on disk.
# Transposing into a key whose diagram is missing shows the chord name with an
# empty box beside it, which is honest but not much use. So: say how many are
# missing, and write the list out, rather than letting it be discovered one
# song at a time on a phone.
SHARPKEYS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLATKEYS  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
PITCHOF = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'E#':5,'Fb':4,'F':5,
	'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11,'Cb':11}

def transposed(name, steps, flat):
	table = FLATKEYS if flat else SHARPKEYS
	out = []
	for part in name.split('/'):
		found = re.match(r'^([A-G][#b]?)(.*)$', part)
		if not found or found.group(1) not in PITCHOF: out.append(part); continue
		out.append(table[(PITCHOF[found.group(1)] + steps) % 12] + found.group(2))
	return '/'.join(out)

wanted = set()
for group in re.finditer(r'<div class="chordgroup[^>]*>(.*?)</div>\s*</div>',
		printhtml, re.S):
	for chord in re.finditer(r'data-src="([^"]*)".*?<span class="chordname">([^<]*)</span>',
			group.group(1), re.S):
		folder = chord.group(1).rsplit('/', 1)[0]
		for steps in range(12):
			for flat in (False, True):
				wanted.add((folder, transposed(chord.group(2), steps, flat)))

def diagrampath(folder, name):
	return '%s/%s.png' % (folder, name.replace('/', '_'))

missing = sorted(set(diagrampath(folder, name).replace('#', '%23')
	for folder, name in wanted
	if not os.path.exists(diagrampath(folder, name).replace('%23', '#'))))
if missing:
	print("transposing would want %d diagrams that aren't drawn yet (of %d)"
		% (len(missing), len(wanted)))
	wantfile = os.path.splitext(webfilename)[0] + '-missingdiagrams.txt'
	with open(wantfile, 'w', encoding='utf-8') as handle:
		handle.write("\n".join(missing) + "\n")
	print("   the list is in", wantfile)
	print("   until they exist those chords show their name and an empty box")
else:
	print("every key has its diagrams drawn")

songsbody = printhtml[printhtml.index('<body>') + 6 : printhtml.rindex('</body>')]

# ---- assemble ---------------------------------------------------------------

# The column-hiding rules are generated rather than living in songbookweb.css,
# so adding an instrument to songbookmaker needs no stylesheet edit.
hiderules = '\n'.join('.hide-%s .c-%s { display: none; }' % (cls, cls)
	for cls in columnclasses)

checkboxes = '\n'.join(
	'    <label><input type="checkbox" data-col="%s" checked>%s</label>' % (cls, heading)
	for cls, heading in zip(columnclasses, columnheadings))

pdflinks = '\n'.join(
	'      <li><a href="%s" download>%s</a><span>%s</span></li>'
	% (filename.replace("VERSION", bookversion), label, note)
	for filename, label, note in pdf_downloads)

pagetemplate = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@BOOKTITLE@@</title>
<style>[hidden]{display:none!important}</style>
<link rel="stylesheet" href="songbookweb.css">
<style>
/* generated from this book's chord-table headings */
@@HIDERULES@@
</style>
</head>
<body>

<header class="bar">
  <span class="booktitle">@@BOOKTITLE@@</span>
  <input type="search" id="find" placeholder="search&hellip;" autocomplete="off">
@@CHORUSBOX@@@@CAPOBOX@@  <span class="nav" id="nav">
    <button id="prev" type="button" title="previous match (shift-enter)">&lsaquo;</button>
    <span class="count" id="count"></span>
    <button id="next" type="button" title="next match (enter)">&rsaquo;</button>
  </span>
  <span class="instruments">
@@CHECKBOXES@@
  </span>
  <label class="sl" title="lyric text size">A<input type="range" id="size" min="9" max="22" value="13" step="1"></label>
  <label class="sl" title="chord diagram size">&#9634;<input type="range" id="dsize" min="24" max="110" value="50" step="2"></label>
  <span class="scrollgroup"><button id="scrollbtn" type="button"
      title="scroll this song (s)">scroll</button><label class="sl" id="speedwrap"
      hidden title="slower / faster"><input type="range" id="speed"
      min="4" max="60" value="16" step="1"></label></span>
  <button id="tocbtn" type="button">contents</button>
  <button id="pdfbtn" type="button">pdf</button>
</header>

<div id="tocwrap" hidden style="display:none">
  <div id="tocpanel">
    <button class="panelclose" id="tocclose" type="button" title="close">&times;</button>
    <nav id="toc">
@@TOCS@@
    </nav>
  </div>
</div>

<div id="pdfwrap" hidden style="display:none">
  <div id="pdfpanel">
    <button class="panelclose" type="button" title="close">&times;</button>
    <h1>download a pdf</h1>
    <p class="pdfnote">printable versions of the book. each one has the same songs &mdash;
       they differ only in which chord diagrams are printed beside them.</p>
    <ul class="pdflist">
@@PDFS@@
    </ul>
  </div>
</div>

<main id="songs">
@@BODY@@
</main>

<button id="top" type="button" title="back to top">&uarr;</button>

<script>
const $ = s => document.querySelector(s);
const songs = [...document.querySelectorAll('.song')];

/* remember choices between visits, but never break if storage is blocked */
const save = (key, value) => { try { localStorage.setItem('songbook.' + key, value); } catch (e) {} };
const load = key => { try { return localStorage.getItem('songbook.' + key); } catch (e) { return null; } };

/* --- instrument columns --- */
function applyColumns() {
  document.querySelectorAll('.instruments input').forEach(box => {
    const column = box.dataset.col;
    document.documentElement.classList.toggle('hide-' + column, !box.checked);
    save('col.' + column, box.checked ? '1' : '0');
    /* display:none still keeps the image decoded, so turning a column off has to
       drop the src as well if it is going to save any memory at all */
    document.querySelectorAll('.c-' + column + ' img[data-src]').forEach(img => {
      if (!box.checked) img.removeAttribute('src');
    });
  });
}
document.querySelectorAll('.instruments input').forEach(box => {
  const remembered = load('col.' + box.dataset.col);
  if (remembered !== null) box.checked = remembered === '1';
  box.addEventListener('change', applyColumns);
});
applyColumns();

/* --- search, and stepping through the matches --- */
let matches = [], cursor = -1;

function filter() {
  const query = $('#find').value.trim().toLowerCase();
  matches = [];
  songs.forEach(song => {
    const hit = !query || (song.dataset.find || '').includes(query);
    song.hidden = !hit;
    if (hit && query) matches.push(song);
  });
  cursor = -1;
  $('#nav').classList.toggle('stepping', matches.length > 1);
  showCount();
}

function showCount() {
  const total = songs.length;
  if (!matches.length) {
    $('#count').textContent = $('#find').value.trim() ? 'no matches' : total + ' songs';
  } else if (cursor < 0) {
    $('#count').textContent = matches.length + ' of ' + total;
  } else {
    $('#count').textContent = (cursor + 1) + '/' + matches.length;
  }
}

function step(by) {
  if (!matches.length) return;
  cursor = (cursor + by + matches.length) % matches.length;
  /* instant, for the same reason as the contents links: the next match can be
     hundreds of songs away and an animated scroll renders everything between */
  attachDiagrams(matches[cursor]);
  matches[cursor].scrollIntoView({ block: 'start', behavior: 'instant' });
  showCount();
}

$('#find').addEventListener('input', filter);
$('#find').addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); step(e.shiftKey ? -1 : 1); }
});
$('#prev').addEventListener('click', () => step(-1));
$('#next').addEventListener('click', () => step(1));
addEventListener('keydown', e => {
  if (e.target === $('#find') || !matches.length) return;
  if (e.key === 'ArrowDown' || e.key === 'j') { e.preventDefault(); step(1); }
  if (e.key === 'ArrowUp'   || e.key === 'k') { e.preventDefault(); step(-1); }
});
filter();

@@CHORUSSCRIPT@@
@@CAPOSCRIPT@@
/* --- sizes: lyrics and diagrams move independently --- */
function slider(selector, cssproperty, unit, storagekey) {
  const control = $(selector);
  const remembered = load(storagekey);
  if (remembered !== null) control.value = remembered;
  const apply = () => {
    document.documentElement.style.setProperty(cssproperty, control.value + unit);
    save(storagekey, control.value);
  };
  control.addEventListener('input', apply);
  apply();
}
slider('#size',  '--songsize',  'px', 'size');
slider('#dsize', '--chordsize', 'px', 'dsize');

/* --- automatic scrolling ------------------------------------------------
   Scrolls the song you are in, and STOPS at the end of it. The whole book is
   one page, so a scroller that just kept going would carry you out of one
   song and into the next while you were still playing it.

   Movement is done by requestAnimationFrame against a floating-point
   position, not setInterval + scrollBy(0,1): at a readable speed you want
   about a third of a pixel per frame, and whole-pixel steps judder badly
   when you are trying to read off the screen. */
let scrolling = false;      /* the song element we are scrolling, or false */
let wantedy = 0;            /* where we have put the page, to the sub-pixel */
let lastframe = 0;
let wakelock = null;

const speed = $('#speed'), speedwrap = $('#speedwrap'), scrollbtn = $('#scrollbtn');
const rememberedspeed = load('speed');
if (rememberedspeed !== null) speed.value = rememberedspeed;
speed.addEventListener('input', () => save('speed', speed.value));

/* Pixels per second, scaled by the lyric size: at 26px text the same number of
   pixels is half as many LINES, and it is lines you are reading. */
function pixelspersecond() {
  const size = parseFloat(getComputedStyle(document.documentElement)
                 .getPropertyValue('--songsize')) || 13;
  return Number(speed.value) * (size / 13);
}

/* the song whose words are on screen: the first one whose bottom is below the
   top of the viewport, allowing for the sticky bar */
function songonscreen() {
  const under = (parseFloat(getComputedStyle(document.documentElement)
                   .scrollPaddingTop) || 0) + 4;
  for (const song of document.querySelectorAll('.song')) {
    if (song.getBoundingClientRect().bottom > under) return song;
  }
  return null;
}

async function keepawake() {                 /* or the phone locks mid-song */
  try { wakelock = await navigator.wakeLock.request('screen'); } catch (e) {}
}
function letitsleep() {
  if (wakelock) { wakelock.release().catch(() => {}); wakelock = null; }
}

function stopscrolling() {
  if (!scrolling) return;
  scrolling = false;
  scrollbtn.textContent = 'scroll';
  scrollbtn.classList.remove('going');
  speedwrap.hidden = true;
  letitsleep();
}

function startscrolling() {
  const song = songonscreen();
  if (!song) return;
  if (song.getBoundingClientRect().bottom <= window.innerHeight) return;  /* all of it is already up */
  scrolling = song;
  wantedy = window.scrollY;
  lastframe = 0;
  scrollbtn.textContent = 'stop';
  scrollbtn.classList.add('going');
  speedwrap.hidden = false;
  keepawake();
  requestAnimationFrame(frame);
}

function frame(now) {
  if (!scrolling) return;
  if (lastframe) {
    /* The page moves under us without anyone touching it: the observer that
       attaches chord diagrams changes the height of songs ABOVE this one as
       they come and go, and everything below shifts. So follow the page
       rather than reading the jump as a person taking over - the hand on the
       page is detected from its own events instead, below. */
    if (Math.abs(window.scrollY - wantedy) > 3) wantedy = window.scrollY;

    /* How far is left is measured from the song itself every frame, never
       from a remembered document position, for the same reason. */
    const left = scrolling.getBoundingClientRect().bottom - window.innerHeight;
    if (left <= 0) { stopscrolling(); return; }      /* the last line is up */
    wantedy += Math.min(pixelspersecond() * Math.min((now - lastframe) / 1000, 0.1), left);
    window.scrollTo(0, wantedy);
  }
  lastframe = now;
  requestAnimationFrame(frame);
}

scrollbtn.addEventListener('click', () => scrolling ? stopscrolling() : startscrolling());

/* s starts and stops it, unless you are typing in the search box */
addEventListener('keydown', e => {
  if (e.key !== 's' || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.target === $('#find') || e.target.tagName === 'INPUT') return;
  e.preventDefault();
  scrolling ? stopscrolling() : startscrolling();
});

/* A person taking over is recognised by their own input, not by the page
   having moved - see the note in frame() about why those are different.

   A tap or click on the control bar is exempt, or pressing the stop button
   would stop it and then the click would start it again. A WHEEL is not
   exempt: the pointer often sits over the bar, and a wheel there scrolls the
   page just the same, so it means the same thing as a wheel anywhere else. */
addEventListener('wheel', () => { if (scrolling) stopscrolling(); }, {passive: true});
for (const event of ['touchstart', 'mousedown']) {
  addEventListener(event, e => {
    if (scrolling && !e.target.closest('.bar')) stopscrolling();
  }, {passive: true});
}
const SCROLLKEYS = [' ', 'ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End'];
addEventListener('keydown', e => {
  if (scrolling && SCROLLKEYS.includes(e.key) && e.target !== $('#find')) stopscrolling();
});

/* the lock is dropped when the tab goes away, so take it again on the way back */
addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && scrolling) keepawake();
});

/* --- tap to turn the page, on a touch screen -----------------------------
   A tap and the first moments of a flick are the same event, so nothing is
   intercepted on the way DOWN: no preventDefault, no blocking, native
   scrolling and momentum untouched. The decision is made on touchend, by
   which point a tap has provably not scrolled anything - it was short and it
   did not move.

   Zones are measured from the bar downwards, not from the top of the screen:
   the top fifth of the READABLE area pages back, the rest pages on. */
const TAPMS = 300;          /* longer than this is a hold, not a tap */
const TAPSLOP = 10;         /* further than this is a drag, not a tap */
const BACKZONE = 0.2;       /* top fifth of the area below the bar goes back */
const TAPGAP = 350;         /* ignore the second half of a double-tap */

let tapstarted = 0, tapx = 0, tapy = 0, taptookover = false, lasttap = 0;

function barheight() {
  return parseFloat(getComputedStyle(document.documentElement)
           .getPropertyValue('--barheight')) || 0;
}

/* a tap on anything you can operate is that thing's business, not a page turn */
function turnspage(target) {
  return !target.closest('.bar, #tocwrap, #pdfwrap, a, button, input, label, select, textarea');
}

/* Capture phase, so this runs BEFORE the listener that stops the auto-scroll
   on a touch - otherwise the scroller has already been switched off by the
   time we look, and a tap meant only to stop it would turn the page too. */
addEventListener('touchstart', e => {
  if (e.touches.length !== 1) { tapstarted = 0; return; }
  taptookover = !!scrolling;
  tapstarted = Date.now();
  tapx = e.touches[0].clientX;
  tapy = e.touches[0].clientY;
}, {capture: true, passive: true});

addEventListener('touchend', e => {
  const started = tapstarted, stoppedscroll = taptookover;
  tapstarted = 0; taptookover = false;
  if (!started || stoppedscroll) return;          /* that tap just stopped the scroll */
  if (Date.now() - started > TAPMS) return;       /* a hold, or a selection */
  if (Date.now() - lasttap < TAPGAP) return;      /* second half of a double-tap */
  const finger = e.changedTouches[0];
  if (Math.abs(finger.clientX - tapx) > TAPSLOP) return;
  if (Math.abs(finger.clientY - tapy) > TAPSLOP) return;
  if (!turnspage(e.target)) return;
  lasttap = Date.now();
  turnthepage(finger.clientY);
}, {passive: true});

function turnthepage(y) {
  const bar = barheight();
  const readable = window.innerHeight - bar;       /* what you can actually see */
  const lineheight = 1.35 * (parseFloat(getComputedStyle(document.documentElement)
                        .getPropertyValue('--songsize')) || 13);
  /* leave a couple of lines showing, or you lose the line you were on */
  const step = Math.max(readable - 2 * lineheight, readable * 0.5);
  window.scrollBy(0, y < bar + readable * BACKZONE ? -step : step);
}

/* --- contents and pdf panels --- */
function openPanel(selector) {
  const panel = $(selector);
  panel.hidden = false;
  panel.style.display = '';                        /* let the stylesheet take over */
  document.body.style.overflow = 'hidden';         /* don't scroll the page behind it */
}
function closePanel(selector) {
  const panel = $(selector);
  panel.hidden = true;
  panel.style.display = 'none';
  document.body.style.overflow = '';
}

const closeToc = () => closePanel('#tocwrap');
$('#tocbtn').addEventListener('click', () => openPanel('#tocwrap'));
$('#tocclose').addEventListener('click', closeToc);

const closePdf = () => closePanel('#pdfwrap');
$('#pdfbtn').addEventListener('click', () => openPanel('#pdfwrap'));
$('#pdfpanel .panelclose').addEventListener('click', closePdf);
$('#pdfwrap').addEventListener('click', e => { if (e.target.id === 'pdfwrap') closePdf(); });
/* Jumping to a song is done by hand rather than by letting the browser follow
   the #fragment. .song is content-visibility:auto, so every song that hasn't
   rendered yet is only an ESTIMATED height -- the browser lands using those
   estimates and then drifts as the real heights arrive. Re-running the scroll
   over the next few frames pins it to the right place once layout settles. */
let jumpToSong = function (id) {
  const target = document.getElementById(id);
  if (!target) return false;
  stopscrolling();          /* landing somewhere else means a different song */
  /* 'instant', NOT 'auto'. 'auto' defers to css scroll-behavior:smooth, which
     animates through every song in between -- and the observer then attaches
     the diagrams for all of them on the way past. */
  const land = () => target.scrollIntoView({ block: 'start', behavior: 'instant' });
  land();
  requestAnimationFrame(land);
  setTimeout(land, 80);
  setTimeout(land, 250);
  return true;
};

$('#tocwrap').addEventListener('click', e => {
  if (e.target.id === 'tocwrap') { closeToc(); return; }
  const link = e.target.closest('a[href^="#"]');
  if (!link) return;
  e.preventDefault();
  closeToc();
  /* A search left in the box hides every song it does not match, so the song
     just picked from the contents has no layout to scroll to and the page
     stays where it was - which reads as the contents being ignored. Clear the
     box and re-filter before jumping. */
  if ($('#find').value) { $('#find').value = ''; filter(); }
  const id = decodeURIComponent(link.getAttribute('href').slice(1));
  if (jumpToSong(id)) history.replaceState(null, '', '#' + encodeURIComponent(id));
});

/* same treatment for a link someone arrives on, or pastes in */
addEventListener('load', () => {
  if (location.hash.length > 1) jumpToSong(decodeURIComponent(location.hash.slice(1)));
});
addEventListener('keydown', e => { if (e.key === 'Escape') { closeToc(); closePdf(); } });

/* safari restores the dom exactly as you left it, inline styles and all, so a
   panel left open comes back open with the page still scroll-locked. reset both
   on load and whenever the page is shown again. */
function resetPanels() { closeToc(); closePdf(); }
resetPanels();
addEventListener('pageshow', resetPanels);

/* --- keep memory bounded: only songs near the viewport hold their diagrams ---
   A five-instrument book has thousands of chord images. loading="lazy" stops
   them loading early, but once you have scrolled past, they stay decoded and
   mobile safari eventually kills the tab ("a problem repeatedly occurred").
   So: attach src when a song comes near, and take it away again when it is far.
   Each img carries width/height attributes, so the box keeps its shape while
   the picture is detached and nothing jumps around. */
const NEARBY = '1200px 0px';

function columnIsOn(img) {
  const group = img.closest('.chordgroup');
  if (!group) return true;
  const column = [...group.classList].find(c => c.startsWith('c-'));
  return !column || !document.documentElement.classList.contains('hide-' + column.slice(2));
}
function attachDiagrams(song) {
  song.querySelectorAll('img[data-src]').forEach(img => {
    if (!columnIsOn(img)) return;
    if (img.getAttribute('src') !== img.dataset.src) img.setAttribute('src', img.dataset.src);
  });
}
function detachDiagrams(song) {
  song.querySelectorAll('img[data-src]').forEach(img => img.removeAttribute('src'));
}

/* The same nearness decides whether a song's lyrics are allowed to be a
   horizontal scroll container -- see .song.near in the stylesheet. Marking
   it here rather than in a second observer keeps one definition of "near". */
function comenear(song) { song.classList.add('near'); attachDiagrams(song); }
function gofar(song)    { song.classList.remove('near'); detachDiagrams(song); }

if ('IntersectionObserver' in window) {
  const watcher = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) comenear(entry.target);
      else gofar(entry.target);
    });
  }, { rootMargin: NEARBY });
  songs.forEach(song => watcher.observe(song));
} else {
  songs.forEach(comenear);          /* no observer: everything stays as it was */
}

/* a jump can land somewhere the observer hasn't caught up with yet */
const originalJump = jumpToSong;
jumpToSong = function (id) {
  const target = document.getElementById(id);
  const song = target && target.closest('.song');
  if (song) comenear(song);
  return originalJump(id);
};

/* --- keep --barheight in step with the bar, which wraps on a narrow window --- */
function measureBar() {
  document.documentElement.style.setProperty('--barheight',
    $('.bar').offsetHeight + 'px');
}
measureBar();
addEventListener('resize', measureBar);

/* --- back to top --- */
/* same reason: a smooth scroll home from song 300 would travel the whole book */
$('#top').addEventListener('click', () => scrollTo({ top: 0, behavior: 'instant' }));
let scrollPending = false;
addEventListener('scroll', () => {
  if (scrollPending) return;                 /* once per frame, not per event */
  scrollPending = true;
  requestAnimationFrame(() => {
    scrollPending = false;
    $('#top').classList.toggle('show', scrollY > 600);
  });
}, { passive: true });
</script>
</body>
</html>
"""

capobox = ('  <span class="capo" title="transpose this song - not kept after a reload">'
	'<button id="keydown" type="button">&minus;</button>'
	'<span class="keybox" id="keybox" title="tap to go back to the written key">0</span>'
	'<button id="keyup" type="button">+</button></span>\n')

caposcript = r"""/* --- transposing ---------------------------------------------------------
   Per song, and deliberately not remembered: a capo you have forgotten you put
   on is worse than no capo, so this dies with the page. It does follow you
   from song to song, which is why it lives in a map rather than a variable.

   WHERE the chords are was decided at build time and written on the song as
   data-cl (lines that are nothing but chords - the line number is enough,
   since every token on such a line is a chord) and data-cm (lines where chords
   and words share a line, with the column of each chord, because those need
   judgement and python is where the judgement lives).

   Nothing is wrapped in a tag until you actually transpose, and then only on
   the song in front of you. Tagging all 22,000 chords up front cost 36MB of
   renderer memory on a phone that could not spare it. */

const SHARPKEYS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
const FLATKEYS  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B'];
const PITCHOF = {C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,'E#':5,Fb:4,F:5,'F#':6,
                 Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11,Cb:11};
/* a chord wearing notation: |D out of a bar, (G) optional, D* strum it once */
const WORN = /^([|([]*)([A-G][#b]?[^\s|()\[\]*]*)(\*?)([|)\]]*)$/;

const keyof = new Map();        /* song element -> semitones */
const asbuilt = new Map();      /* song element -> what the build produced */

function shiftchord(name, by, flat) {
  const table = flat ? FLATKEYS : SHARPKEYS;
  return name.split('/').map(function (part) {
    const m = /^([A-G][#b]?)(.*)$/.exec(part);
    if (!m || !(m[1] in PITCHOF)) return part;
    return table[((PITCHOF[m[1]] + by) % 12 + 12) % 12] + m[2];
  }).join('/');
}

function shifttoken(token, by, flat) {
  const worn = WORN.exec(token);
  if (!worn) return null;
  return {before: worn[1], was: worn[2], now: shiftchord(worn[2], by, flat),
          star: worn[3], after: worn[4]};
}

const safetext = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

/* Rewrite one chord line, widening the lyric under it where a longer name
   needs the room. Both lines are stretched at the SAME column, so a chord and
   its syllable move together. Only where the lyric has no gap to widen does
   the chord line creep right by itself, and then one chord ends up a column
   off its syllable - about 1.7% of them in the worst key. */
function retune(chordline, lyricline, by, flat, columns) {
  const tokens = [];
  const finder = /\S+/g;
  let m;
  while ((m = finder.exec(chordline)))
    if (columns ? columns.indexOf(m.index) >= 0 : WORN.test(m[0]))
      tokens.push([m[0], m.index, m.index + m[0].length]);
  if (!tokens.length) return null;

  const inserts = [];                 /* [column in the lyric, how many] */
  const bare = lyricline.replace(/\s+$/, '').length;
  const movedby = upto =>
    inserts.reduce((t, i) => t + (i[0] <= upto ? i[1] : 0), 0);

  let out = '', outcol = 0, at = 0, creep = 0;

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i][0], start = tokens[i][1], end = tokens[i][2];
    const worn = shifttoken(token, by, flat);
    const text = worn ? worn.before + worn.now + worn.star + worn.after : token;
    const changed = worn && worn.now !== worn.was;

    /* Whatever sat between the last chord and this one is kept exactly as it
       was: a label like (Solo):, a bar line, a repeat marker, or a line of
       verse sharing the line with the chords. Only the run of spaces on the
       end of it may be stretched or squeezed. Rebuilding the line from the
       chords alone threw all of that away. */
    const between = chordline.slice(at, start);
    const keep = between.replace(/ +$/, '');
    const stretchy = between.length - keep.length;
    out += safetext(keep);
    outcol += keep.length;

    const target = start + movedby(start) + creep;
    const pad = Math.max(stretchy ? 1 : 0, target - outcol);
    out += ' '.repeat(pad);
    outcol += pad;

    out += changed ? '<span class="moved">' + safetext(text) + '</span>'
                   : safetext(text);
    outcol += text.length;
    at = end;

    if (i + 1 >= tokens.length) continue;
    const nextstart = tokens[i + 1][1];
    const short = (outcol + 1) - (nextstart + movedby(nextstart) + creep);
    if (short <= 0) continue;

    /* Make room by widening the lyric at the same column, so the chord and
       its syllable move together. Where there is no gap to widen, the chord
       line alone creeps right and one chord sits a column off. */
    const low = Math.max(outcol - movedby(start) - creep, start + 1);
    if (low >= bare) { inserts.push([nextstart, short]); continue; }
    let spot = -1;
    for (let c = Math.max(low, 0); c <= nextstart; c++)
      if (c < lyricline.length && lyricline[c] === ' ') { spot = c; break; }
    if (spot >= 0) inserts.push([spot, short]); else creep += short;
  }
  out += safetext(chordline.slice(at));

  let lyric = lyricline;
  inserts.sort((a, b) => b[0] - a[0]).forEach(function (insert) {
    const col = insert[0], many = insert[1];
    lyric = col <= lyric.length
      ? lyric.slice(0, col) + ' '.repeat(many) + lyric.slice(col)
      : lyric.padEnd(col);
  });
  return {chords: out, lyric: lyric};
}

const LEADINGTAGS = /^(?:<[^>]*>)*/;

function remember(song) {
  if (asbuilt.has(song)) return asbuilt.get(song);
  const lyrics = song.querySelector('.lyrics');
  const kept = {
    lyrics: lyrics ? lyrics.innerHTML : '',
    chords: [...song.querySelectorAll('.chord')].map(function (chord) {
      const img = chord.querySelector('img');
      return {name: chord.querySelector('.chordname').textContent,
              src: img ? img.dataset.src : null,
              unplayable: chord.classList.contains('unplayable')};
    })
  };
  /* Which key the song is in, taken as the chord it uses most. It decides
     whether the new key is spelled with sharps or with flats, which is not a
     matter of taste: transposed down four, Stand By Me lands in F, and in F
     the chord is Bb. Spelling it A# is the mark of a transposer that is just
     adding numbers. */
  const counted = {};
  kept.chords.forEach(function (chord) {
    const root = /^([A-G][#b]?)/.exec(chord.name);
    if (root && root[1] in PITCHOF)
      counted[PITCHOF[root[1]]] = (counted[PITCHOF[root[1]]] || 0) + 1;
  });
  kept.tonic = Object.keys(counted).sort((a, b) => counted[b] - counted[a])[0];
  kept.tonic = kept.tonic === undefined ? 0 : +kept.tonic;
  asbuilt.set(song, kept);
  return kept;
}

/* The keys a musician writes with flats: Db, Eb, F, Ab, Bb - and their minors.
   Everything else gets sharps. F# rather than Gb, by convention. */
const FLATKEY = new Set([1, 3, 5, 8, 10]);

function retunesong(song, by) {
  const original = remember(song);
  const flat = FLATKEY.has(((original.tonic + by) % 12 + 12) % 12);
  const diagrams = song.querySelectorAll('.chord');

  original.chords.forEach(function (was, i) {
    const chord = diagrams[i];
    if (!chord) return;
    const now = by ? shiftchord(was.name, by, flat) : was.name;
    chord.querySelector('.chordname').textContent = now;
    chord.classList.toggle('moved', now !== was.name);
    const img = chord.querySelector('img');
    if (!img || !was.src) return;
    if (!by) {                       /* back to the written key, as built */
      chord.classList.remove('nodiagram');
      chord.classList.toggle('unplayable', was.unplayable);
      img.onerror = null;
      img.dataset.src = was.src;
      if (img.getAttribute('src')) img.setAttribute('src', was.src);
      return;
    }
    const folder = was.src.slice(0, was.src.lastIndexOf('/') + 1);
    /* a filename cannot hold a slash, so songbookmaker writes G/B as G_B.png */
    const file = folder + encodeURIComponent(now.replace(/\//g, '_')) + '.png';
    /* A key nobody has drawn yet shows the name over an empty box, and the
       stylesheet puts a ? after it: an empty grid on its own would read as
       "play it open", which on a banjo is a real chord. Transposing can also
       rescue a chord that had no diagram in the written key, so this starts
       clean and lets the picture decide. */
    chord.classList.remove('nodiagram', 'unplayable');
    img.onerror = () => chord.classList.add('nodiagram');
    img.dataset.src = file;
    if (img.getAttribute('src')) img.setAttribute('src', file);
  });

  const lyrics = song.querySelector('.lyrics');
  if (!lyrics) return;
  if (!by) { lyrics.innerHTML = original.lyrics; return; }

  const lines = original.lyrics.split('\n');
  const plan = [];
  (song.dataset.cl || '').split(',').filter(Boolean)
    .forEach(n => plan.push([+n, null]));
  (song.dataset.cm || '').split(',').filter(Boolean).forEach(function (entry) {
    const bits = entry.split(':');
    plan.push([+bits[0], bits[1].split('.').map(Number)]);
  });
  const chordlines = new Set(plan.map(p => p[0]));

  for (const job of plan) {
    const n = job[0], columns = job[1];
    if (n >= lines.length) continue;
    const tags = LEADINGTAGS.exec(lines[n])[0];
    const under = n + 1;
    const haslyric = under < lines.length && !chordlines.has(under);
    const lyrictags = haslyric ? LEADINGTAGS.exec(lines[under])[0] : '';
    const lyrictext = haslyric ? lines[under].slice(lyrictags.length) : '';
    const done = retune(lines[n].slice(tags.length), lyrictext, by, flat, columns);
    if (!done) continue;
    lines[n] = tags + done.chords;
    if (haslyric) lines[under] = lyrictags + done.lyric;
  }
  lyrics.innerHTML = lines.join('\n');
}

const keybox = $('#keybox');

function showkey() {
  const song = songonscreen();
  const by = song ? (keyof.get(song) || 0) : 0;
  keybox.textContent = by > 0 ? '+' + by : String(by);
  keybox.classList.toggle('shifted', by !== 0);
}

/* Rewriting a song can change its height - a diagram nobody has drawn yet, a
   lyric line widened to make room - and the browser then scrolls to compensate,
   which slides the song out from under you. Put it back where it was. */
function holdstill(song, change) {
  const was = song.getBoundingClientRect().top;
  change();
  const moved = song.getBoundingClientRect().top - was;
  if (moved) window.scrollBy(0, moved);
}

/* Stepping from A down to E is four presses, and rewriting on each one asks
   the server for the diagrams of G#, G and F# on the way past - 18 requests
   where the one key you want needs 2. So the number moves the instant you
   press, and the song is rewritten once you stop. */
const SETTLEMS = 220;
let rewritesoon = 0;

function nudgekey(by) {
  const song = songonscreen();
  if (!song) return;
  const now = Math.max(-11, Math.min(11, (keyof.get(song) || 0) + by));
  keyof.set(song, now);
  showkey();
  clearTimeout(rewritesoon);
  rewritesoon = setTimeout(() => holdstill(song, () => retunesong(song, now)),
    SETTLEMS);
}

/* The box has to follow you from song to song, or it reads out the key of a
   song you have already scrolled past. songonscreen() walks the songs until it
   finds the one under the bar, so this waits until the scrolling STOPS rather
   than running on every frame - on a three-hundred song page that walk is not
   something to do sixty times a second. */
let keysoon = 0;
addEventListener('scroll', () => {
  clearTimeout(keysoon);
  keysoon = setTimeout(showkey, 150);
}, {passive: true});

$('#keyup').addEventListener('click', () => nudgekey(1));
$('#keydown').addEventListener('click', () => nudgekey(-1));
keybox.addEventListener('click', function () {   /* tap the number to undo it */
  const song = songonscreen();
  if (!song || !keyof.get(song)) return;
  keyof.set(song, 0);
  clearTimeout(rewritesoon);
  holdstill(song, () => retunesong(song, 0));
  showkey();
});
showkey();
"""

chorusbox = ('  <label class="chorusbox" title="replace a [CHORUS] reference with the words">'
	'<input type="checkbox" id="expandchorus" checked>expand choruses</label>\n') if EXPAND_CHORUSES else ''

chorusscript = """/* --- expand chorus references in place --- */
function applyChorus() {
  document.documentElement.classList.toggle('expandchorus', $('#expandchorus').checked);
  save('chorus', $('#expandchorus').checked ? '1' : '0');
}
const chorusWas = load('chorus');          /* on by default; remember either choice */
if (chorusWas !== null) $('#expandchorus').checked = chorusWas === '1';
$('#expandchorus').addEventListener('change', applyChorus);
applyChorus();
""" if EXPAND_CHORUSES else ''

webpage = (pagetemplate
	.replace('@@BOOKTITLE@@', booktitle)
	.replace('@@CHORUSBOX@@', chorusbox)
	.replace('@@CHORUSSCRIPT@@', chorusscript)
	.replace('@@CAPOBOX@@', capobox)
	.replace('@@CAPOSCRIPT@@', caposcript)
	.replace('@@HIDERULES@@', hiderules)
	.replace('@@CHECKBOXES@@', checkboxes)
	.replace('@@TOCS@@', '<div class="toccols">'
		+ ''.join('<section class="toccol">' + toc + '</section>'
		          for toc in tableofcontents) + '</div>' + chartlist)
	.replace('@@PDFS@@', pdflinks)
	.replace('@@BODY@@', songsbody))

open(webfilename, 'w', encoding='utf-8').write(webpage)
print("wrote", webfilename, "-",
	len(re.findall(r'<div class="song"', songsbody)), "songs,", len(webpage), "bytes")

missingpdfs = [f.replace("VERSION", bookversion) for f, _, _ in pdf_downloads
               if not os.path.isfile(f.replace("VERSION", bookversion))]
if missingpdfs:
	print("note: the download panel links to pdfs that aren't here yet:")
	for filename in missingpdfs: print("   ", filename)
