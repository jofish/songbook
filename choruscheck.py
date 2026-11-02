"""choruscheck.py — sanity-check the <chorus> tags in a songbook xml file.

	python3 choruscheck.py songs.xml

Run it after hand-tagging. It catches the mistakes that would otherwise show up
as a wrong page break in the pdf weeks later, and lists what still needs doing.
"""
import re, sys, xml.dom.minidom
from chorusref import backreferences

OPEN_ALONE = re.compile(r'^\s*<chorus>\s*$')
CLOSE_ALONE = re.compile(r'^\s*</chorus>\s*$')

if len(sys.argv) < 2: sys.exit("usage: python3 choruscheck.py songs.xml")
filename = sys.argv[1]
raw = open(filename, encoding='utf-8').read()

problems, untagged, tagged = [], [], 0

try:
	xml.dom.minidom.parse(filename)
except Exception as whatwentwrong:
	problems.append(("THE WHOLE FILE", "xml does not parse: %s" % whatwentwrong))

for mo in re.finditer(r'<song>(.*?)</song>', raw, re.S):
	block = mo.group(1)
	titlematch = re.search(r'<songtitle>(.*?)</songtitle>', block, re.S)
	title = titlematch.group(1).strip() if titlematch else '(no title)'
	lyricsmatch = re.search(r'<lyrics>(.*?)</lyrics>', block, re.S)
	if not lyricsmatch: continue
	lyrics = lyricsmatch.group(1)
	lines = lyrics.split('\n')

	opens, closes = lyrics.count('<chorus>'), lyrics.count('</chorus>')

	# the one that matters: a tag on its own line silently adds a blank line to
	# the song, which moves every page break after it
	for n, line in enumerate(lines, 1):
		if OPEN_ALONE.match(line) or CLOSE_ALONE.match(line):
			problems.append((title,
				"line %d: a chorus tag on its own line ADDS A BLANK LINE to the song. "
				"Glue it to the text instead: <chorus>G    D" % n))

	if opens != closes:
		problems.append((title, "%d <chorus> but %d </chorus>" % (opens, closes)))
	elif opens > 1:
		problems.append((title, "%d chorus blocks - expected one" % opens))
	elif opens == 1:
		if lyrics.index('</chorus>') < lyrics.index('<chorus>'):
			problems.append((title, "</chorus> comes before <chorus>"))
		else:
			tagged += 1
			body = re.search(r'<chorus>(.*?)</chorus>', lyrics, re.S).group(1)
			real = [l for l in body.split('\n') if l.strip()]
			if not real:
				problems.append((title, "the chorus block is empty"))
			elif len(real) < 2:
				problems.append((title, "the chorus block is only one line"))
			elif len(real) > 20:
				problems.append((title, "the chorus block is %d lines - too long?" % len(real)))

	# does this song still need a tag?
	if opens == 0 and backreferences(lines):
		untagged.append(title)

print("file:", filename)
print("songs with a <chorus> block :", tagged)
print("still need one              :", len(untagged))
print()

if problems:
	print("PROBLEMS —", len(problems))
	for title, why in problems: print("   %-38s %s" % (title[:37], why))
	print()
else:
	print("no problems found.")
	print()

if untagged:
	print("these refer back to a chorus but have no <chorus> block:")
	for title in untagged: print("   ", title)

sys.exit(1 if problems else 0)
