"""Which tokens on a mixed line count as chords.

Each case came from a real line in the songbook, and most of them from a bug.
The ones that are prose rather than chords have been rewritten here so this
file carries no lyrics: what is tested is the SHAPE of the line - an article
at the start, a capitalised word beside a chord-shaped letter - which the
replacements keep exactly."""
import re, sys
src=open(sys.argv[1] if len(sys.argv)>1 else 'makeweb.py').read()
ns={'re':re}
exec(src[src.index('CHORDNAME = re.compile'):src.index('LYRICSBLOCK = re.compile')], ns)
chordspots=ns['chordspots']

CASES=[
 # the article, which must never move: transposing it would turn "A ship"
 # into "B ship"
 ("A ship came sailing in at break of day",              "nothing"),
 ("A quiet evening many years ago,",                     "nothing"),
 ("A thousand candles burning in the hall",              "nothing"),
 # prose that names chords - left alone on purpose
 ("Form a D chord, then pick the single strings D D B G","nothing"),
 ("Form a C chord, then pick the single strings A A B G","nothing"),
 ("original is in F#, ie play in E with capo II",        "nothing"),
 ("(start: C power chord on 8th fret)",                  "nothing"),
 ("REPEAT CHORUS (ends on F instead of returning to Am)","nothing"),
 ("Play E7 as C7 on 5th, slide up from 4th.",            "nothing"),
 # real chords sharing a line with a label or an aside
 ("Em                     A7   (just strum chords once)","Em A7"),
 ("Chorus    G     D   A",                               "G D A"),
 ("D D5 D D5        (repeat and fade)",                  "D D5 D D5"),
 ("|C*             D*                            G",     "|C* D* G"),
 ("Intro: G C Em C x2",                                  "G C Em C"),
 # a word only wins on a line that is ALL prose: "end" does not get to veto
 # a chord on a line that already has four confident ones
 ("Outro: G Am Em C x4 end G",                           "G Am Em C G"),
 ("Bb5 C5 F5 G5 x4, end on Bb5",                         "Bb5 C5 F5 G5 Bb5"),
 ("F                           (G)  F",                  "F (G) F"),
 ("D                                            G ( 2 bars)", "D G"),
 # a word that happens to be capitalised is still a word
 ("We sailed away aboard the Mary B",                    "nothing"),
 ("Am I the first one here today?",                      "nothing"),
 ("A Year has passed since we were last ashore",         "nothing"),
 ("[A You diddleum diddleum dum day]",                   "nothing"),
 # a chord carrying a note to the player is not a word
 ("B(b9) B  x8    [and now repeat chorus again]",        "B"),
 ("Dm  Bb           (repeat this closing chorus 2x)",    "Dm Bb"),
]
bad=0
for line, want in CASES:
    got=[line[c:].split(' ')[0] for c in chordspots(line)]
    g=" ".join(got) if got else "nothing"
    if g!=want:
        bad+=1
        print("  FAIL |%s\n       got %r, wanted %r" % (line, g, want))
print("chord-spotting: %d of %d cases as expected" % (len(CASES)-bad, len(CASES)))
sys.exit(1 if bad else 0)
