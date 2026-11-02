"""choruswrap.py — wrap each song's chorus in <chorus>...</chorus> in the xml.

	python3 choruswrap.py songs.xml songs-tagged.xml

Only songs that refer BACK to a chorus matter: "[CHORUS]" on its own line, or
tacked onto the end of a lyric line. Those are the ones the web view needs to
expand. Everything else is left alone.

The tag is transparent to the pdf: songbookmaker and chordadder both read the
lyrics with a recursive text walk, so <chorus>text</chorus> yields "text" and
the printed book is unchanged.

Where the chorus can't be identified confidently the song is listed at the end
for you to tag by hand. Re-running is safe: a song that already has a <chorus>
tag is left untouched.
"""
import re, sys, collections
from chorusref import isbarereference, istailreference, backreferences, MARKER_WORD

# a marker at the START of a line with the chorus running on after it
HEAD_MARKER = re.compile(r'^((?:pre[\s\-]?)?chorus|refrain)\s*:\s*(?=\S)', re.I)

def isblank(line): return line.strip() == ''

def indentof(line):
	return len(re.match(r'^[ \t]*', line).group().expandtabs(4))


def verseindent(lines):
	"""The column the verses start at — the chorus is whatever is set in from it.

	NOT simply the most common indent: in a chorus-heavy song the chorus can
	have more lines than the verses do, and then the chorus looks like the
	baseline and nothing is found (Rehab did exactly this). Take instead the
	LEFTMOST column that carries a real share of the song, allowing a column of
	slop so a stray leading space doesn't start a new level."""
	levels = collections.Counter(indentof(l) for l in lines if l.strip())
	if not levels: return 0
	total = sum(levels.values())
	for column in sorted(levels):
		nearby = sum(n for ind, n in levels.items() if ind <= column + 1)
		if nearby >= total * 0.15: return column + 1
	return min(levels)


def runafter(lines, start):
	"""the run of lines from start until a blank line"""
	out = []
	while start < len(lines) and not isblank(lines[start]):
		out.append(start)
		start += 1
	return out


def indentrun(lines, start, base):
	"""a run of indented lines, which blank lines inside do NOT end.
	   Single-space 'blank' lines are common inside an indented chorus."""
	out, i, pending = [], start, []
	while i < len(lines):
		line = lines[i]
		if isblank(line):
			pending.append(i)
		elif indentof(line) > base:
			out.extend(pending); pending = []
			out.append(i)
		else:
			break
		i += 1
	return out


def findchorus(lines):
	"""returns (list of line numbers forming the chorus, how we decided) or (None, why not)"""
	refs = backreferences(lines)
	if not refs: return None, 'no back-reference'
	firstref = min(refs)
	base = verseindent(lines)

	# 1. a marker that introduces a block: "Chorus:" with lyrics under it
	for i, line in enumerate(lines):
		if i >= firstref: break
		if isbarereference(line):
			following = lines[i + 1] if i + 1 < len(lines) else ''
			if following.strip():
				body = indentrun(lines, i + 1, base) if indentof(following) > base \
				       else runafter(lines, i + 1)
				if len(body) >= 2: return body, 'labelled block'

	# 2. a marker sharing its line with the chorus: "Chorus:    A   E   F#m"
	for i, line in enumerate(lines):
		if i >= firstref: break
		if HEAD_MARKER.match(line):
			body = [i] + indentrun(lines, i + 1, base)
			if len(body) >= 2: return body, 'inline label'

	# 3. an indented passage before the first reference
	candidates = []
	i = 0
	while i < firstref:
		if lines[i].strip() and indentof(lines[i]) > base:
			run = indentrun(lines, i, base)
			if len(run) >= 3: candidates.append(run)
			i = (run[-1] + 1) if run else i + 1
		else:
			i += 1
	if len(candidates) == 1: return candidates[0], 'indented block'
	if len(candidates) > 1:
		return max(candidates, key=len), 'indented block (several, took the longest)'

	return None, 'no label and nothing indented'


STAGEDIRECTION = re.compile(r'^\s*[\[\(\*]|^\s*(play|strum|repeat|instrumental|solo)\b', re.I)

def lookswrong(lines, body):
	"""reasons to doubt an automatic tag — worth a human glance"""
	block = [lines[i] for i in body]
	words = [l for l in block if len(re.findall(r'[a-z]{3,}', l)) >= 2]
	if len(block) < 4:  return 'only %d lines' % len(block)
	if len(block) > 18: return '%d lines, too long for a chorus' % len(block)
	if not words:       return 'no lyric lines, only chords'
	if STAGEDIRECTION.match(words[0]):
		return 'starts with a stage direction: ' + words[0].strip()[:34]
	if isbarereference(words[0]) or HEAD_MARKER.match(words[0].strip()):
		return 'starts with the marker itself'
	return None


def wrap(lyrics):
	"""returns (newlyrics, how) — how is None when nothing was changed"""
	if '<chorus>' in lyrics: return lyrics, 'already tagged'
	lines = lyrics.split('\n')
	body, how = findchorus(lines)
	if body is None: return lyrics, None
	doubt = lookswrong(lines, body)
	if doubt: how = 'CHECK: ' + doubt
	first, last = min(body), max(body)
	lines[first] = '<chorus>' + lines[first]
	lines[last] = lines[last] + '</chorus>'
	return '\n'.join(lines), how


if len(sys.argv) < 3: sys.exit("usage: python3 choruswrap.py songs.xml songs-tagged.xml")
infile, outfile = sys.argv[1], sys.argv[2]
raw = open(infile, encoding='utf-8').read()

tagged = collections.Counter()
suspect = []
needmanual = []
songcount = 0

def handlesong(match):
	global songcount
	songcount += 1
	block = match.group(0)
	title = re.search(r'<songtitle>(.*?)</songtitle>', block, re.S).group(1).strip()
	lyricsmatch = re.search(r'(<lyrics>)(.*?)(</lyrics>)', block, re.S)
	oldlyrics = lyricsmatch.group(2)
	newlyrics, how = wrap(oldlyrics)
	if how is None:
		if backreferences(oldlyrics.split('\n')): needmanual.append(title)
		return block
	if how.startswith('CHECK: '): suspect.append((title, how[7:]))
	else: tagged[how] += 1
	return block[:lyricsmatch.start(2)] + newlyrics + block[lyricsmatch.end(2):]

out = re.sub(r'<song>.*?</song>', handlesong, raw, flags=re.S)
open(outfile, 'w', encoding='utf-8').write(out)

print("songs:", songcount)
print("wrote", outfile)
print()
print("tagged automatically:")
for how, n in tagged.most_common(): print("   %-42s %d" % (how, n))
print("   %-42s %d" % ("TOTAL", sum(tagged.values())))
print()
if suspect:
	print("tagged, but worth checking —", len(suspect), "songs:")
	for title, why in suspect: print("   %-40s %s" % (title[:39], why))
	print()
if needmanual:
	print("needs a <chorus>...</chorus> by hand —", len(needmanual), "songs:")
	for title in needmanual: print("   ", title)
