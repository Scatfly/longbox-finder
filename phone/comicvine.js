  // ---------- Comic Vine (phone version) ----------
  // The phone app can't use Claude, so unknown series and characters are looked up
  // with the Comic Vine API (JSONP, since the API doesn't allow cross-site fetch).
  const CV = "https://comicvine.gamespot.com";
  const KEY_STORE = "longbox-cv-key";
  const DISMISS_STORE = "longbox-cv-dismissed";
  let cvKey = "";
  let keyDismissed = false;
  try { cvKey = localStorage.getItem(KEY_STORE) || ""; keyDismissed = localStorage.getItem(DISMISS_STORE) === "1"; } catch (e) {}
  let liveOK = !!cvKey;
  let ctl = null;
  let cbN = 0;
  const mkCtl = () => ({ aborted: false, abort() { this.aborted = true; } });

  function cv(path, params) {
    return new Promise((resolve, reject) => {
      const cb = "__cv" + Date.now() + "_" + (++cbN);
      const s = document.createElement("script");
      const qs = new URLSearchParams(Object.assign({ api_key: cvKey, format: "jsonp", json_callback: cb }, params));
      const timer = setTimeout(() => { done(); reject({ code: "timeout" }); }, 20000);
      function done() { clearTimeout(timer); window[cb] = function () {}; s.remove(); }
      window[cb] = data => {
        done();
        if (data && data.status_code === 1) resolve(data);
        else reject({ code: data && data.status_code === 100 ? "bad_key" : data && data.status_code === 107 ? "rate_limited" : "cv_error", message: data && data.error });
      };
      s.onerror = () => { done(); reject({ code: "load_failed" }); };
      s.src = CV + "/api/" + path + "?" + qs.toString();
      document.head.append(s);
    });
  }

  const isMarvel = x => !!(x && x.publisher && /marvel/i.test(x.publisher.name || ""));
  const safeCv = u => typeof u === "string" && u.startsWith(CV + "/") ? u : "";
  const yearOf = d => d ? Number(String(d).slice(0, 4)) || "" : "";
  const volInfo = v => ({ id: v.id, name: String(v.name || ""), start_year: v.start_year, count_of_issues: v.count_of_issues, site_detail_url: v.site_detail_url });

  function cvMessage(code) {
    if (code === "bad_key") return "Comic Vine didn't accept your API key. Check it with “Change key” at the top.";
    if (code === "load_failed") return "Couldn't reach Comic Vine. Check your internet connection and that your API key is right (Comic Vine answers a wrong key this way too).";
    if (code === "rate_limited") return "Comic Vine's hourly lookup limit was reached. Try again later.";
    if (code === "timeout") return "Comic Vine took too long to answer. Try again.";
    return "Comic Vine returned an error. Try again.";
  }

  async function cvLookup(query, kind) {
    if (!cvKey) {
      showFallback(query, "Add your free Comic Vine API key at the top to look up any Marvel series or character, including brand-new ones.");
      renderKeybar(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    ctl && ctl.abort();
    const my = ctl = mkCtl();
    renderThinking(query, "Looking up “" + query + "” on Comic Vine…");
    try {
      if (kind === "character") await cvCharacter(query, my);
      else await cvSeries(query, my);
    } catch (e) {
      if (!my.aborted) showFallback(query, cvMessage(e && e.code));
    }
  }
  const askClaude = cvLookup;
  const liveLookup = cvLookup;

  async function cvSeries(query, my) {
    const r = await cv("search/", { query, resources: "volume", field_list: "id,name,start_year,publisher,count_of_issues,site_detail_url", limit: 30 });
    if (my.aborted) return;
    const vols = (r.results || []).filter(isMarvel);
    if (!vols.length) { showFallback(query, "Comic Vine has no Marvel series matching “" + query + "”. Check the spelling, or add the issues yourself."); return; }
    const q = norm(query);
    const exact = vols.filter(v => norm(v.name || "") === q).sort((a, b) => (Number(b.start_year) || 0) - (Number(a.start_year) || 0));
    const pick = exact[0] || vols[0];
    await cvShowVolume(volInfo(pick), vols.filter(v => v !== pick).slice(0, 8).map(volInfo), query, my);
  }

  async function cvShowVolume(vol, others, query, my) {
    const label = vol.name + (vol.start_year ? " (" + vol.start_year + ")" : "");
    renderThinking(label, "Loading the issues of " + label + "…");
    const r = await cv("issues/", { filter: "volume:" + vol.id, field_list: "id,issue_number,cover_date,name,image", sort: "cover_date:asc", limit: 100 });
    if (my.aborted) return;
    const issues = (r.results || []).slice().sort((a, b) => (parseFloat(a.issue_number) || 0) - (parseFloat(b.issue_number) || 0));
    const comics = issues.map(i => ({
      series: vol.name, issue: String(i.issue_number || ""), year: yearOf(i.cover_date) || Number(vol.start_year) || "",
      writer: "", artist: "", format: "single", key: false, note: i.name ? String(i.name) : "",
      img: i.image && /^https:\/\//.test(String(i.image.medium_url || "")) && !/\/img\//.test(i.image.medium_url) ? String(i.image.medium_url) : ""
    }));
    const total = Number(r.number_of_total_results) || comics.length;
    current = {
      title: label,
      summary: "Marvel series from Comic Vine, " + total + " issue" + (total === 1 ? "" : "s") + (total > comics.length ? " (showing the first " + comics.length + ")" : "") + ".",
      comics, source: "Comic Vine", sourceUrl: safeCv(vol.site_detail_url), kind: "series", query,
      related: others, relatedLabel: "Other Marvel series with similar names"
    };
    renderResults();
  }

  async function cvCharacter(query, my) {
    const r = await cv("search/", { query, resources: "character", field_list: "id,name,publisher,real_name,count_of_issue_appearances", limit: 20 });
    if (my.aborted) return;
    const chars = (r.results || []).filter(isMarvel);
    if (!chars.length) { showFallback(query, "Comic Vine has no Marvel character matching “" + query + "”. Check the spelling."); return; }
    const q = norm(query);
    const byApps = (a, b) => (b.count_of_issue_appearances || 0) - (a.count_of_issue_appearances || 0);
    const pick = chars.filter(x => norm(x.name || "") === q || norm(x.real_name || "") === q).sort(byApps)[0] || chars.slice().sort(byApps)[0];
    renderThinking(pick.name, "Loading " + pick.name + "'s comics…");
    const d = await cv("character/4005-" + pick.id + "/", { field_list: "name,deck,first_appeared_in_issue,volume_credits,site_detail_url,count_of_issue_appearances" });
    if (my.aborted) return;
    const ch = d.results || {};
    const name = String(ch.name || pick.name);
    const comics = [];
    const fa = ch.first_appeared_in_issue;
    if (fa && fa.id) {
      try {
        const i = await cv("issue/4000-" + fa.id + "/", { field_list: "issue_number,cover_date,volume,name" });
        const iss = i.results || {};
        comics.push({ series: String((iss.volume && iss.volume.name) || fa.name || "First appearance"), issue: String(iss.issue_number || fa.issue_number || ""), year: yearOf(iss.cover_date), writer: "", artist: "", format: "single", key: true, note: "First appearance of " + name + "." });
      } catch (e) { if (e && e.code === "bad_key") throw e; }
    }
    if (my.aborted) return;
    const local = localMatch(query, "character");
    if (local) local.comics.forEach(x => { if (!comics.some(y => keyOf(y) === keyOf(x) || (y.series === x.series && y.issue === x.issue))) comics.push(x); });
    const ids = (Array.isArray(ch.volume_credits) ? ch.volume_credits : []).map(v => Number(v.id)).filter(Boolean).sort((a, b) => b - a).slice(0, 60);
    let related = [];
    if (ids.length) {
      const v = await cv("volumes/", { filter: "id:" + ids.join("|"), field_list: "id,name,start_year,publisher,count_of_issues,site_detail_url", limit: 100 });
      if (my.aborted) return;
      related = (v.results || []).filter(isMarvel).sort((a, b) => (Number(b.start_year) || 0) - (Number(a.start_year) || 0)).slice(0, 16).map(volInfo);
    }
    const apps = Number(ch.count_of_issue_appearances) || 0;
    current = {
      title: name,
      summary: [ch.deck ? String(ch.deck) : "", apps ? "Appears in " + apps.toLocaleString() + " issues." : "", related.length ? "Tap a series below to see its issues." : ""].filter(Boolean).join(" "),
      comics, source: "Comic Vine", sourceUrl: safeCv(ch.site_detail_url), kind: "character", query,
      related, relatedLabel: "Series featuring " + name + ", newest first"
    };
    renderResults();
  }

  function relatedBox(c) {
    const box = el("div", "related");
    box.append(el("div", "flabel", c.relatedLabel || "Related series"));
    const wrap = el("div", "relchips");
    c.related.forEach(v => {
      const b = el("button", "pill", v.name + (v.start_year ? " (" + v.start_year + ")" : "") + (v.count_of_issues ? " · " + v.count_of_issues + " issues" : ""));
      b.type = "button";
      b.addEventListener("click", async () => {
        ctl && ctl.abort();
        const my = ctl = mkCtl();
        try { await cvShowVolume(v, [], v.name, my); }
        catch (e) { if (!my.aborted) showFallback(v.name, cvMessage(e && e.code)); }
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      wrap.append(b);
    });
    box.append(wrap);
    return box;
  }

  function setKey(k) {
    cvKey = k;
    liveOK = !!k;
    try { if (k) localStorage.setItem(KEY_STORE, k); else localStorage.removeItem(KEY_STORE); } catch (e) {}
    renderKeybar(false);
    if (current) renderResults();
  }

  function renderKeybar(open) {
    const bar = $("keybar");
    bar.replaceChildren();
    if (!open && cvKey) {
      const s = el("div", "keystatus");
      s.append(el("span", "on", "Comic Vine lookups on"));
      const b = el("button", "linkbtn", "Change key"); b.type = "button";
      b.addEventListener("click", () => renderKeybar(true));
      s.append(b);
      bar.append(s);
      return;
    }
    if (!open && keyDismissed) {
      const s = el("div", "keystatus");
      const b = el("button", "linkbtn", "Add a Comic Vine key to look up any series"); b.type = "button";
      b.addEventListener("click", () => renderKeybar(true));
      s.append(b);
      bar.append(s);
      return;
    }
    const p = el("form", "keypanel");
    p.append(el("div", "ktitle", cvKey ? "Change your Comic Vine API key" : "Look up any Marvel series, even brand-new ones"));
    const help = el("p", null, "Get a free API key at ");
    const a = el("a", null, "comicvine.gamespot.com/api"); a.href = "https://comicvine.gamespot.com/api/"; a.target = "_blank"; a.rel = "noopener";
    help.append(a, document.createTextNode(" (sign in, then copy the key it shows you). The key is saved only on this device."));
    p.append(help);
    const row = el("div", "krow");
    const inp = el("input"); inp.id = "cvKey"; inp.placeholder = "Paste your API key"; inp.autocomplete = "off"; inp.spellcheck = false; inp.value = cvKey;
    inp.setAttribute("aria-label", "Comic Vine API key");
    const save = el("button", "btn primary", "Save key"); save.type = "submit";
    row.append(inp, save);
    if (cvKey) {
      const rm = el("button", "btn", "Remove"); rm.type = "button"; rm.addEventListener("click", () => setKey(""));
      const cancel = el("button", "btn", "Cancel"); cancel.type = "button"; cancel.addEventListener("click", () => renderKeybar(false));
      row.append(rm, cancel);
    } else {
      const later = el("button", "btn", "Not now"); later.type = "button";
      later.addEventListener("click", () => { keyDismissed = true; try { localStorage.setItem(DISMISS_STORE, "1"); } catch (e) {} renderKeybar(false); });
      row.append(later);
    }
    p.append(row);
    p.addEventListener("submit", e => { e.preventDefault(); const k = inp.value.trim(); if (k) setKey(k); });
    bar.append(p);
  }

