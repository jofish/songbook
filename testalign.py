"""After transposing, is every chord still over the letter it started over?
Checked across the whole book, in every key, in the browser."""
import sys
from playwright.sync_api import sync_playwright

CHECK = """(by) => {
  const WORN = /^([|([]*)([A-G][#b]?[^\\s|()\\[\\]*]*)(\\*?)([|)\\]]*)$/;
  let chords = 0, off = 0, widened = 0, songs = 0;
  const examples = [];
  for (const song of document.querySelectorAll('.song[data-cl]')) {
    const lyrics = song.querySelector('.lyrics');
    if (!lyrics) continue;
    songs++;
    const before = lyrics.textContent.split('\\n');
    retunesong(song, by);
    const after = lyrics.textContent.split('\\n');
    const cl = (song.dataset.cl || '').split(',').filter(Boolean).map(Number);
    const marks = new Set(cl);
    for (const n of cl) {
      if (n + 1 >= before.length || marks.has(n + 1)) continue;
      const wasline = before[n], nowline = after[n];
      const waslyric = before[n + 1], nowlyric = after[n + 1];
      if (waslyric.trim() === '') continue;
      const wastok = [...wasline.matchAll(/\\S+/g)].filter(m => WORN.test(m[0]));
      const nowtok = [...nowline.matchAll(/\\S+/g)].filter(m => WORN.test(m[0]));
      if (wastok.length !== nowtok.length) continue;
      if (waslyric.replace(/ /g,'') !== nowlyric.replace(/ /g,'')) {
        off++; examples.push('lyric text changed: ' + nowlyric.slice(0,40)); continue;
      }
      for (let i = 0; i < wastok.length; i++) {
        chords++;
        const a = waslyric[wastok[i].index] || ' ';
        const b = nowlyric[nowtok[i].index] || ' ';
        if (a.trim() && a !== b) {
          off++;
          if (examples.length < 4)
            examples.push(wastok[i][0] + ' was over ' + JSON.stringify(a)
                          + ', now over ' + JSON.stringify(b));
        }
      }
      if (nowlyric.length !== waslyric.length) widened++;
    }
    retunesong(song, 0);
  }
  return {songs, chords, off, widened, examples};
}"""

url = sys.argv[1]
fails = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    page = browser.new_page(viewport={'width': 1200, 'height': 900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(url); page.wait_for_timeout(2500)

    print("key    songs  chords checked   over the wrong letter   lyric lines widened")
    print("-" * 78)
    worst = 0
    for by in range(1, 12):
        r = page.evaluate(CHECK, by)
        rate = 100 * r['off'] / max(r['chords'], 1)
        worst = max(worst, rate)
        print("  %+3d  %5d  %13d   %8d (%5.2f%%)   %10d"
              % (by, r['songs'], r['chords'], r['off'], rate, r['widened']))
        if r['examples'] and by in (1, 6):
            for e in r['examples'][:2]: print("         e.g. %s" % e)
    print()
    print("worst: %.2f%% of chords land a column off" % worst)
    if worst > 3: fails.append("alignment drift of %.2f%%" % worst)
    browser.close()

if errors: print("JS ERRORS:", errors[:3])
print("FAILURES:", fails if fails else "none")
sys.exit(1 if fails or errors else 0)
