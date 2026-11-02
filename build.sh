#!/bin/bash
# build.sh — regenerate every songbook pdf, plus the web version.
#
#   bash build.sh                 build, and open each pdf as it finishes
#   bash build.sh noopen          build without opening anything
#   bash build.sh upload          build, don't open, then publish to the web
#   bash build.sh upload diagrams  ...and push the chord diagrams too (slow)
#
set -e

# --- settings -------------------------------------------------------------
# Everything here is a placeholder. Put your own in my-settings.sh beside this
# script and they override these; that file is not in the public repo, so your
# filenames and your server stay out of it.
#
#   cat > my-settings.sh <<'EOF'
#   SONGS=my-songs.xml
#   REMOTE_USER=you
#   REMOTE_HOST=example.com
#   REMOTE_PATH=/var/www/html/songbook
#   EOF

VERSION=11.0                        # must match VERSION in songbookmaker11.py
SONGS=my-songs.xml                  # the master file you edit
DISCARDS=discardpile.xml

REMOTE_USER=you
REMOTE_HOST=example.com
REMOTE_PATH=/var/www/html/songbook

[ -f my-settings.sh ] && . ./my-settings.sh
# --------------------------------------------------------------------------

# The web version's checkboxes can only hide columns that are in the file it was
# built from, so it is made from the everything build — which is also why that
# one exists, even though it is too crowded to print.
EVERYTHING="guitar uke banjo mandolin bariuke"

OPENPDFS=""            # passed to songbookmaker; "noopen" suppresses the open
DOUPLOAD=no
SENDDIAGRAMS=no
for word in "$@"; do
	case "$word" in
		noopen)   OPENPDFS="noopen" ;;
		upload)   DOUPLOAD=yes; OPENPDFS="noopen" ;;   # publishing implies batch
		diagrams) SENDDIAGRAMS=yes ;;
		*) echo "don't know the option '$word'"
		   echo
		   echo "  bash build.sh                  build, and open each pdf as it finishes"
		   echo "  bash build.sh noopen           build without opening anything"
		   echo "  bash build.sh upload           build, don't open, then publish to the web"
		   echo "  bash build.sh upload diagrams  ...and push the chord diagrams too (slow)"
		   exit 1 ;;
	esac
done

# Tag choruses IN THE MASTER, in place. It skips any song that already has a
# <chorus>, so hand-tagging survives and re-running is free. Doing it here (and
# in place) is what stops the tags living in some -tagged.xml that nothing reads.
echo "=== tagging choruses ==="
python3 choruswrap.py "$SONGS"    "$SONGS"    | grep -E 'TOTAL|by hand' || true
python3 choruswrap.py "$DISCARDS" "$DISCARDS" | grep -E 'TOTAL|by hand' || true
python3 choruscheck.py "$SONGS" > /dev/null || echo "   (choruscheck found problems - run it for details)"

echo
echo "=== adding chords ==="
python3 chordadder.py "$SONGS"    songbook.xml                quiet
python3 chordadder.py "$DISCARDS" discardpile-with-chords.xml quiet

echo
echo "=== building pdfs ==="
# allkeys goes on the first run of each book. The web version transposes a
# song as you read it, and a diagram is a picture on disk, so every chord needs
# drawing in all twelve keys before anyone presses +. It draws for EVERY
# instrument regardless of the columns asked for here, so one run per book
# covers the lot and the builds after it find everything already there.
# Slow the first time only: a chord already on disk costs nothing.
python3 songbookmaker11.py songbook.xml guitar uke allkeys $OPENPDFS
python3 songbookmaker11.py songbook.xml guitar uke banjo $OPENPDFS
python3 songbookmaker11.py songbook.xml mandolin $OPENPDFS
python3 songbookmaker11.py songbook.xml bariuke $OPENPDFS
python3 songbookmaker11.py songbook.xml $EVERYTHING $OPENPDFS
python3 songbookmaker11.py discardpile-with-chords.xml guitar uke banjo mandolin allkeys $OPENPDFS

echo
echo "=== web-resolution copies of the chart scans ==="
# The charts are 300dpi so they print properly -- the guitar one is 2550x3300.
# A phone draws it 366 css px wide, which is 1098 device pixels, so it decodes
# eight megapixels to show a sixth of them and the chart pages are needlessly
# heavy. sips ships with macos, so there is nothing to install. The originals
# are left alone: the pdfs still use them. makeweb picks up a -web copy by
# itself if it finds one, so if sips is missing nothing breaks, the page just
# uses the full-size scans as before.
#
# 1600 wide covers a phone (needs 1098) and an ipad in portrait (1620) with
# room to spare. An ipad in landscape draws them 2312 device pixels wide and
# will be a touch softer; raise this if that bothers you.
CHARTWIDTH=1600
if command -v sips > /dev/null; then
	for f in *.jpg; do
		case "$f" in *-web.jpg) continue ;; esac
		[ -f "$f" ] || continue
		wide=$(sips -g pixelWidth "$f" 2>/dev/null | awk '/pixelWidth/{print $2}')
		# never upscale: a scan already narrower than the target is left alone
		if [ -n "$wide" ] && [ "$wide" -le "$CHARTWIDTH" ]; then continue; fi
		web="${f%.jpg}-web.jpg"
		if [ ! -f "$web" ] || [ "$f" -nt "$web" ]; then
			sips --resampleWidth "$CHARTWIDTH" "$f" --out "$web" > /dev/null \
				&& echo "   $f -> $web (${wide}px wide -> $CHARTWIDTH)"
		else
			echo "   $web is already up to date"
		fi
	done
else
	echo "   no sips on this machine - the page will use the full-size charts"
fi

echo
echo "=== building the web version ==="
WEBSOURCE="songbook-$VERSION-guitar-uke-banjo-mandolin-bariuke.html"
python3 makeweb.py "$WEBSOURCE" songbook-web.html

# The discard pile gets the same page under its own name, built from the print
# run above rather than a build of its own. songbookmaker puts -discards on the
# end of anything whose xml filename says discard, which is why this is not the
# plain instrument name.
DISCARDSOURCE="songbook-$VERSION-guitar-uke-banjo-mandolin-discards.html"
python3 makeweb.py "$DISCARDSOURCE" discard-web.html discard

echo
echo "=== done building ==="
ls -lh songbook-"$VERSION"-*.pdf songbook-web.html discard-web.html

# --------------------------------------------------------------------------

if [ "$DOUPLOAD" = no ]; then exit 0; fi

echo
echo "=== publishing to $REMOTE_HOST:$REMOTE_PATH ==="

# Everything the page actually asks the server for: itself, the stylesheet, the
# pdfs it offers, and the back-matter images (the four chord charts and the
# Saints music). Miss the images and they're broken on the live site.
# index.html is not in here on purpose: on the server it's a symlink to
# songbook-web.html, so uploading a copy would overwrite the link with a file
# that then goes stale.
UPLOADS=(songbook-web.html songbookweb.css)
for f in songbook-"$VERSION"-*.pdf; do UPLOADS+=("$f"); done
# Read the image names out of the page rather than listing them here, so the
# -web copies go up, and so another chart or an illustration in a song needs no
# edit in this file. Only the top-level ones: everything under diagrams/ has a
# slash in it and travels with "bash build.sh upload diagrams".
while IFS= read -r f; do
	[ -n "$f" ] && [ -f "$f" ] && UPLOADS+=("$f")
done < <(grep -oE 'data-src="[^"/]+\.(jpg|jpeg|png)"' songbook-web.html \
         | sed 's/^data-src="//; s/"$//' | sort -u)

missing=no
for f in "${UPLOADS[@]}"; do
	[ -f "$f" ] || { echo "   missing, not uploading: $f"; missing=yes; }
done
[ "$missing" = yes ] && { echo "   fix the above first"; exit 1; }

# fail early and clearly if the remote directory isn't there
if ! ssh "$REMOTE_USER@$REMOTE_HOST" "test -d '$REMOTE_PATH'" 2>/dev/null; then
	echo "   can't see $REMOTE_PATH on $REMOTE_HOST"
	echo "   check REMOTE_PATH at the top of this script, or make the directory:"
	echo "      ssh $REMOTE_USER@$REMOTE_HOST \"mkdir -p $REMOTE_PATH\""
	exit 1
fi

# the diagrams are what the chord images come from - no point publishing without
# them, so say so if they have never been sent
if [ "$SENDDIAGRAMS" = no ] \
   && ! ssh "$REMOTE_USER@$REMOTE_HOST" "test -d '$REMOTE_PATH/diagrams'" 2>/dev/null; then
	echo "   NOTE: there are no diagrams on the server yet, so every chord will be"
	echo "         a broken image. Run:  bash build.sh upload diagrams"
	echo
fi

# rsync is much better than sftp here: it only sends what changed, which matters
# a lot for the ~1800 chord diagrams. Fall back to sftp if it isn't installed.
# The discard pile sits next to the songbook rather than inside it, so the two
# have separate urls. It shares the diagrams instead of carrying 4000 copies of
# them: make that one symlink on the server once and it stays made.
#   ssh $REMOTE_HOST "mkdir -p $DISCARD_PATH && ln -s ../songbook/diagrams $DISCARD_PATH/diagrams"
#   ssh $REMOTE_HOST "ln -s discard-web.html $DISCARD_PATH/index.html"
DISCARD_PATH="$(dirname "$REMOTE_PATH")/discard"
DISCARDUPLOADS=(discard-web.html songbookweb.css)
for f in songbook-"$VERSION"-guitar-uke-banjo-mandolin-discards.pdf; do
	[ -f "$f" ] && DISCARDUPLOADS+=("$f")
done
while IFS= read -r f; do
	[ -n "$f" ] && [ -f "$f" ] && DISCARDUPLOADS+=("$f")
done < <(grep -oE 'data-src="[^"/]+\.(jpg|jpeg|png)"' discard-web.html 2>/dev/null \
         | sed 's/^data-src="//; s/"$//' | sort -u)

if command -v rsync > /dev/null; then
	rsync -av --progress "${UPLOADS[@]}" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
	if [ -f discard-web.html ]; then
		ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p '$DISCARD_PATH'"
		rsync -av --progress "${DISCARDUPLOADS[@]}" \
			"$REMOTE_USER@$REMOTE_HOST:$DISCARD_PATH/"
		ssh "$REMOTE_USER@$REMOTE_HOST" \
			"test -e '$DISCARD_PATH/diagrams' || ln -s ../songbook/diagrams '$DISCARD_PATH/diagrams'"
	fi
	if [ "$SENDDIAGRAMS" = yes ]; then
		echo "   sending diagrams (only the changed ones)..."
		rsync -av diagrams/ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/diagrams/"
	fi
else
	echo "   rsync not found, using sftp (sends everything, every time)"
	{
		echo "cd $REMOTE_PATH"
		for f in "${UPLOADS[@]}"; do echo "put $f"; done
		if [ "$SENDDIAGRAMS" = yes ]; then
			echo "mkdir diagrams" ; echo "put -r diagrams"
		fi
	} | sftp -b - "$REMOTE_USER@$REMOTE_HOST"
fi

echo
echo "=== published ==="
echo "   https://$REMOTE_HOST/songbook"
if [ "$SENDDIAGRAMS" = no ]; then
	echo "   (chord diagrams not sent — add 'diagrams' if they've changed)"
fi
