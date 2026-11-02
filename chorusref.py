"""chorusref.py — what counts as a line pointing BACK at the chorus.

Shared by choruswrap.py (which inserts the tags), choruscheck.py (which
verifies them) and makeweb.py (which expands them), so the three can't drift.

The real songs vary a lot -- "(Chorus again)", "Chorus x2", "(second chorus)",
"CHORUS AGAIN", "{chorus, fade}", "REPEAT CHORUS 2x TO FADE" -- so rather than
listing forms, take out the marker word and judge what is left. A few words of
performance note means it points back; chord names mean it is a label sitting
over the chorus itself.
"""
import re

MARKER_WORD = re.compile(r'(?:pre[\s\-]?)?chorus|refrain', re.I)
CHORD_LIKE = re.compile(r'^[A-G][#b]?(m|maj|min|dim|sus|add|M)?[0-9]*(/[A-G][#b]?)?$')
# a marker right-aligned at the end of a lyric line, bracketed or just spaced out
TAIL_MARKER = re.compile(
	r'(?:\s*[\[\(<{]\s*(?:pre[\s\-]?)?(?:chorus|refrain)\s*[\]\)>}]\s*'
	r'|(?:\t|\s{2,})(?:pre[\s\-]?)?(?:chorus|refrain)\s*)$', re.I)


def leftoverwords(line):
	"""what's left of a line once the marker word and its decoration are gone"""
	rest = MARKER_WORD.sub(' ', line)
	rest = re.sub(r'[\[\]\(\)<>{}:,.\-=*_/]', ' ', rest)
	return rest.split()


def isbarereference(line):
	"""a whole line that points back at the chorus"""
	if not MARKER_WORD.search(line): return False
	rest = leftoverwords(line)
	if len(rest) > 5: return False                           # too much else there
	if any(CHORD_LIKE.match(w) for w in rest): return False   # a label over chords
	return True


def istailreference(line):
	"""a marker tacked onto the end of a lyric line"""
	marker = TAIL_MARKER.search(line)
	return bool(marker) and bool(line[:marker.start()].strip())


def backreferences(lines):
	"""Indexes of the lines that point BACK at the chorus.

	A bare marker with lyrics directly under it is a heading introducing the
	chorus, not a pointer to it -- so it only counts when nothing follows."""
	found = []
	for i, line in enumerate(lines):
		if istailreference(line):
			found.append(i)
		elif isbarereference(line):
			following = lines[i + 1] if i + 1 < len(lines) else ''
			if not following.strip(): found.append(i)
	return found
