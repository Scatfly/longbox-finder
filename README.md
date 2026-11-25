# Longbox Finder

Look up Marvel comics by series (like *Wolverine and Jubilee*) or by character (like *Jubilee*). Pick the issues you want and get links to the best places to buy each one: eBay, MyComicShop, Midtown Comics, Amazon, Kindle and local shops.

**App:** https://scatfly.github.io/longbox-finder/

## Put it on your phone

- **iPhone (Safari):** open the link, tap Share, then **Add to Home Screen**.
- **Android (Chrome):** open the link, tap the ⋮ menu, then **Add to Home screen** or **Install app**.

## Looking up any series

Some series and characters are built in. To look up anything else, including brand-new series, get a free API key at [comicvine.gamespot.com/api](https://comicvine.gamespot.com/api/) and paste it into the app. The key is saved only on your device.

## Files

- `index.html` is the phone app. It's generated, so don't edit it directly.
- `longbox-finder.html` is the Claude artifact version, which uses Claude for lookups.
- `phone/` holds the Comic Vine lookup and the phone styles.
- To rebuild after changing either page: `py build_phone.py`
- `make_icons.py` draws the app icons.
