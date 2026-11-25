"""Builds the phone app (index.html) from the Claude artifact page (longbox-finder.html).

The artifact uses Claude for lookups; the phone version swaps those parts for the
Comic Vine API (phone/comicvine.js) and adds the bits an installable web app needs.
Run:  py build_phone.py
"""
from pathlib import Path

ROOT = Path(__file__).parent
src = (ROOT / "longbox-finder.html").read_text(encoding="utf-8")
cv_js = (ROOT / "phone" / "comicvine.js").read_text(encoding="utf-8")
extra_css = (ROOT / "phone" / "extra.css").read_text(encoding="utf-8")


def cut(text, start, end, replacement):
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + replacement + text[b:]


def swap(text, old, new):
    assert old in text, "marker not found: " + old[:60]
    return text.replace(old, new, 1)


page = src
# Drop the Claude lookup and the Claude-app browser lookup; insert Comic Vine instead.
page = cut(page, "  // ---------- Claude ----------", "  function normalizeComics(data) {", "")
page = cut(page, "  // ---------- Live lookup", "  function showFallback(query, message) {", cv_js)

page = swap(page, ".foot { margin-top: 36px;", extra_css + "\n.foot { margin-top: 36px;")
page = swap(page, '    <div class="quick" id="quick">', '    <div id="keybar"></div>\n    <div class="quick" id="quick">')
page = swap(page, 'if (c.source === "Built-in") {\n      const more = el("button", "btn", "Ask Claude for more");',
            'if (c.source === "Built-in" && !liveOK) {\n      const more = el("button", "btn", "Look up more on Comic Vine");')
page = swap(page, 'if (liveOK && (c.source === "Built-in" || c.source === "Claude")) {\n      const live = el("button", "btn", "Check online for newer issues");',
            'if (liveOK && c.source === "Built-in") {\n      const live = el("button", "btn", "Check Comic Vine for newer issues");')
page = swap(page, '    if (liveOK) {\n      const again = el("button", "btn", "Try the online lookup again");',
            '    {\n      const again = el("button", "btn", liveOK ? "Try Comic Vine again" : "Add a Comic Vine key to look it up");')
page = swap(page, "    if (!c.comics.length) {\n      root.append(fallbackBox(",
            "    if (!c.comics.length && !(c.related && c.related.length)) {\n      root.append(fallbackBox(")
page = swap(page, "    c.comics.forEach(x => grid.append(comicCard(x)));\n    root.append(grid);",
            "    c.comics.forEach(x => grid.append(comicCard(x)));\n    root.append(grid);\n    if (c.related && c.related.length) root.append(relatedBox(c));")
page = swap(page, 'Results from "Ask Claude" are generated and may contain mistakes; double-check issue numbers before you buy.',
            'Series and character data from <a href="https://comicvine.gamespot.com/" target="_blank" rel="noopener">Comic Vine</a>.')
page = swap(page, "  renderPull();\n  renderWelcome();\n", "  renderKeybar(false);\n  renderPull();\n  renderWelcome();\n")

assert 'use("sample")' not in page and 'use("mcp")' not in page, "Claude-only code left in phone build"

head = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#15171c">
<meta name="description" content="Look up Marvel series and characters and find the best places to buy each comic.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Longbox">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<style>
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; -webkit-text-size-adjust: 100%; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""
# Move the artifact's <title>/<meta>/<link>/<style> into <head>; the rest is body.
split = page.index('<div class="wrap">')
out = head + page[:split] + "</head>\n<body>\n" + page[split:] + """
<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
</script>
</body>
</html>
"""
(ROOT / "index.html").write_text(out, encoding="utf-8")
print("Wrote index.html", len(out), "bytes")
