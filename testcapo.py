"""Transposing, driven through the real buttons in a real browser."""
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
fails = []

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    page = browser.new_page(viewport={'width': 1200, 'height': 900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(url); page.wait_for_timeout(2500)

    # Playwright's click() scrolls the element into view first, and with a
    # sticky bar that moves the page under us. A finger does not do that.
    def tap(selector):
        page.evaluate("s => document.querySelector(s).click()", selector)
        page.wait_for_timeout(250)

    page.evaluate("jumpToSong('bene.kingstandbyme')"); page.wait_for_timeout(600)

    def lyrics():
        return page.evaluate("""() => {
            const s = songonscreen();
            return s.querySelector('.lyrics').textContent;
        }""")

    before = lyrics()
    print("written key:")
    for line in before.split('\n')[1:8]: print("   |%s" % line.rstrip())

    for _ in range(2): tap('#keyup')
    page.wait_for_timeout(300)
    after = lyrics()
    print("up two:   (box says %r)" % page.inner_text('#keybox'))
    for line in after.split('\n')[1:8]: print("   |%s" % line.rstrip())

    if page.inner_text('#keybox') != '+2': fails.append("the box does not read +2")
    if 'F#m' not in before or 'G#m' not in after: fails.append("F#m did not become G#m")
    if 'When the night has come' not in after: fails.append("a lyric went missing")

    # every chord must still sit over the letter it started over
    drift = page.evaluate("""() => {
        const s = songonscreen();
        const lines = s.querySelector('.lyrics').textContent.split('\\n');
        const cl = (s.dataset.cl || '').split(',').filter(Boolean).map(Number);
        let checked = 0, off = 0;
        for (const n of cl) {
            if (n + 1 >= lines.length) continue;
            for (const m of lines[n].matchAll(/\\S+/g)) checked++;
        }
        return {checked: checked};
    }""")
    print("\nchord tokens on this song after transposing: %d" % drift['checked'])

    # the colour: only the chords that moved
    moved = page.evaluate("""() => {
        const s = songonscreen();
        const spans = [...s.querySelectorAll('.lyrics .moved')];
        return {count: spans.length,
                sample: spans.slice(0,6).map(x => x.textContent.trim()),
                colour: spans.length ? getComputedStyle(spans[0]).color : null};
    }""")
    print("coloured as moved: %d, e.g. %s, colour %s"
          % (moved['count'], moved['sample'], moved['colour']))
    if not moved['count']: fails.append("nothing was marked as moved")

    # the diagrams follow
    chords = page.evaluate("""() => {
        const s = songonscreen();
        return [...s.querySelectorAll('.chord')].slice(0,5).map(c => ({
            name: c.querySelector('.chordname').textContent,
            src: c.querySelector('img').dataset.src,
            moved: c.classList.contains('moved')}));
    }""")
    print("\ndiagrams now:")
    for c in chords: print("   %-6s %-34s moved=%s" % (c['name'], c['src'], c['moved']))
    if not any(c['moved'] for c in chords): fails.append("no diagram was retuned")

    # back to zero restores exactly
    tap('#keybox'); page.wait_for_timeout(300)
    print("\nafter tapping the number: box %r, identical to the written key: %s"
          % (page.inner_text('#keybox'), lyrics() == before))
    if lyrics() != before: fails.append("going back to 0 did not restore the song")

    # it stays when you move to another song and come back
    tap('#keyup')
    page.evaluate("jumpToSong('billyjoelpianoman')"); page.wait_for_timeout(600)
    other = page.inner_text('#keybox')
    page.evaluate("jumpToSong('bene.kingstandbyme')"); page.wait_for_timeout(600)
    back = page.inner_text('#keybox')
    print("another song reads %r, coming back reads %r" % (other, back))
    if other != '0': fails.append("the offset leaked to another song")
    if back != '+1': fails.append("the offset was lost on returning")

    browser.close()

print()
if errors: print("JS ERRORS:", errors[:4])
print("FAILURES:", fails if fails else "none")
sys.exit(1 if fails or errors else 0)
