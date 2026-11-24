/* Source file. Copied to the manual pages by tools/manual/build_manual.py. */
/* Larry Seyer Drums beta tester manual: search, copy-link, mobile contents, device switch. */
(function (root) {
  'use strict';

  var STOP = {
    a: 1, an: 1, the: 1, and: 1, or: 1, of: 1, to: 1, in: 1, on: 1, for: 1,
    is: 1, it: 1, this: 1, that: 1, with: 1, at: 1, as: 1, be: 1, by: 1
  };

  function tokenize(text) {
    if (!text) return [];
    var words = String(text).toLowerCase().match(/[a-z0-9]+/g) || [];
    var out = [];
    var seen = Object.create(null);
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if (STOP[w] || seen[w]) continue;
      seen[w] = 1;
      out.push(w);
    }
    return out;
  }

  function haystack(parts) {
    return parts.filter(Boolean).join('\n').toLowerCase();
  }

  function snippetAround(text, terms, limit) {
    limit = limit || 140;
    if (!text) return '';
    var lower = text.toLowerCase();
    var idx = -1;
    for (var i = 0; i < terms.length; i++) {
      idx = lower.indexOf(terms[i]);
      if (idx !== -1) break;
    }
    if (idx === -1) {
      return text.length > limit ? text.slice(0, limit).trim() + '\u2026' : text;
    }
    var start = Math.max(0, idx - 40);
    var end = Math.min(text.length, start + limit);
    var cut = text.slice(start, end).trim();
    if (start > 0) cut = '\u2026' + cut;
    if (end < text.length) cut = cut + '\u2026';
    return cut;
  }

  function highlight(text, terms) {
    if (!text) return '';
    var escape = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };
    var escaped = String(text).replace(/[&<>"]/g, function (ch) { return escape[ch]; });
    if (!terms || !terms.length) return escaped;
    var pattern = terms.map(function (t) {
      return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }).join('|');
    if (!pattern) return escaped;
    return escaped.replace(new RegExp('(' + pattern + ')', 'gi'), '<mark>$1</mark>');
  }

  function search(index, query, limit) {
    limit = limit || 10;
    var terms = tokenize(query);
    if (!terms.length || !index || !index.pages) return [];
    var hits = [];
    for (var p = 0; p < index.pages.length; p++) {
      var page = index.pages[p];
      var sections = page.sections || [];
      // Score the page title / summary as a whole-page hit.
      var titleBlob = haystack([page.title, page.summary]);
      var titleScore = 0;
      var titleMiss = false;
      for (var t = 0; t < terms.length; t++) {
        if (titleBlob.indexOf(terms[t]) !== -1) titleScore += 10;
        else titleMiss = true;
      }
      if (titleScore && !titleMiss) {
        hits.push({
          url: page.url,
          title: page.title,
          chapter: page.title,
          number: page.number,
          snippet: page.summary || page.title,
          score: titleScore + (page.number === 0 ? 1 : 0)
        });
      }
      for (var s = 0; s < sections.length; s++) {
        var sec = sections[s];
        var blob = haystack([page.title, page.summary, sec.title, sec.text]);
        var score = 0;
        var miss = false;
        for (var k = 0; k < terms.length; k++) {
          var term = terms[k];
          if (blob.indexOf(term) === -1) { miss = true; break; }
          if (page.title && page.title.toLowerCase().indexOf(term) !== -1) score += 8;
          if (sec.title && sec.title.toLowerCase().indexOf(term) !== -1) score += 5;
          score += 1;
        }
        if (miss || !score) continue;
        var url = page.url + (sec.id ? '#' + sec.id : '');
        hits.push({
          url: url,
          title: sec.title || page.title,
          chapter: page.title,
          number: page.number,
          snippet: snippetAround(sec.text || sec.title || page.summary || '', terms),
          score: score
        });
      }
    }
    hits.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      if (a.number !== b.number) return a.number - b.number;
      return a.title.localeCompare(b.title);
    });
    // Drop near-duplicate URLs (title hit + first section of same page).
    var seen = Object.create(null);
    var unique = [];
    for (var i = 0; i < hits.length; i++) {
      if (seen[hits[i].url]) continue;
      seen[hits[i].url] = 1;
      unique.push(hits[i]);
      if (unique.length >= limit) break;
    }
    return unique;
  }

  var api = { tokenize: tokenize, search: search, highlight: highlight, snippetAround: snippetAround };
  root.ManualSearch = api;

  if (typeof document === 'undefined') return;

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  ready(function () {
    var body = document.body;
    if (!body || !body.classList.contains('manual')) return;

    var toggle = document.querySelector('.manual-toc-toggle');
    var sidebar = document.querySelector('.manual-sidebar');
    var backdrop = document.querySelector('.manual-backdrop');
    function setToc(open) {
      body.classList.toggle('manual-toc-open', open);
      if (toggle) {
        toggle.setAttribute('aria-expanded', String(open));
        var label = toggle.querySelector('.manual-toc-toggle__label');
        if (label) label.textContent = open ? 'Close contents' : 'Contents';
        else toggle.textContent = open ? 'Close contents' : 'Contents';
      }
    }
    if (toggle && sidebar) {
      toggle.addEventListener('click', function () {
        setToc(!body.classList.contains('manual-toc-open'));
      });
      if (backdrop) backdrop.addEventListener('click', function () { setToc(false); });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') setToc(false);
      });
      sidebar.querySelectorAll('a').forEach(function (a) {
        a.addEventListener('click', function () { setToc(false); });
      });
    }

    var deviceKey = 'lsd-manual-device';
    var deviceSwitch = document.querySelector('.manual-device-switch');
    function currentDevice() {
      var value = document.documentElement.getAttribute('data-manual-device');
      if (value === 'iphone' || value === 'mac') return value;
      try { value = localStorage.getItem(deviceKey); } catch (e) { value = null; }
      if (value === 'iphone' || value === 'mac') return value;
      var phone = /iPhone|iPod/i.test(navigator.userAgent || '');
      var narrow = window.matchMedia && window.matchMedia('(max-width: 600px)').matches;
      return (phone || narrow) ? 'iphone' : 'mac';
    }
    function setDevice(value) {
      if (value !== 'iphone' && value !== 'mac') return;
      document.documentElement.setAttribute('data-manual-device', value);
      try { localStorage.setItem(deviceKey, value); } catch (e) {}
      if (!deviceSwitch) return;
      deviceSwitch.querySelectorAll('[data-device]').forEach(function (btn) {
        btn.setAttribute('aria-pressed', String(btn.getAttribute('data-device') === value));
      });
    }
    if (deviceSwitch) {
      setDevice(currentDevice());
      deviceSwitch.querySelectorAll('[data-device]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          setDevice(btn.getAttribute('data-device'));
        });
      });
    }

    document.querySelectorAll('.manual-copy-link').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = btn.getAttribute('data-anchor');
        if (!id) return;
        var url = location.href.split('#')[0] + '#' + id;
        var done = function () {
          var prev = btn.textContent;
          btn.classList.add('is-copied');
          btn.textContent = 'Copied';
          setTimeout(function () {
            btn.classList.remove('is-copied');
            btn.textContent = prev;
          }, 1500);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(done).catch(function () {
            window.prompt('Copy this link:', url);
          });
        } else {
          window.prompt('Copy this link:', url);
        }
      });
    });

    var form = document.querySelector('.manual-search');
    if (!form) return;
    var input = form.querySelector('input[type="search"]');
    var results = form.querySelector('.manual-search-results');
    var empty = form.querySelector('.manual-search-empty');
    var status = form.querySelector('.manual-search-status');
    if (!input || !results) return;

    var indexCache = null;
    var indexPromise = null;
    function loadIndex() {
      if (indexCache) return Promise.resolve(indexCache);
      if (indexPromise) return indexPromise;
      var src = form.getAttribute('data-index') || 'search-index.json';
      indexPromise = fetch(src).then(function (res) {
        if (!res.ok) throw new Error('search index missing');
        return res.json();
      }).then(function (data) {
        indexCache = data;
        return data;
      });
      return indexPromise;
    }

    var timer = null;
    function render(query) {
      var q = (query || '').trim();
      results.innerHTML = '';
      results.classList.add('is-idle');
      if (empty) empty.hidden = true;
      if (status) status.textContent = '';
      if (!q) return;
      loadIndex().then(function (index) {
        var hits = search(index, q, 8);
        results.classList.remove('is-idle');
        if (!hits.length) {
          if (empty) {
            empty.hidden = false;
            empty.textContent = 'No matches for \u201c' + q + '\u201d.';
          }
          if (status) status.textContent = 'No matches.';
          return;
        }
        if (empty) empty.hidden = true;
        hits.forEach(function (hit) {
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = hit.url;
          var chap = document.createElement('span');
          chap.className = 'manual-search-chapter';
          chap.textContent = hit.chapter;
          var title = document.createElement('span');
          title.innerHTML = highlight(hit.title, tokenize(q));
          a.appendChild(chap);
          a.appendChild(title);
          if (hit.snippet && hit.snippet !== hit.title) {
            var sn = document.createElement('span');
            sn.className = 'manual-search-snippet';
            sn.innerHTML = highlight(hit.snippet, tokenize(q));
            a.appendChild(sn);
          }
          li.appendChild(a);
          results.appendChild(li);
        });
        if (status) status.textContent = hits.length + ' match' + (hits.length === 1 ? '' : 'es') + '.';
      }).catch(function () {
        if (empty) {
          empty.hidden = false;
          empty.textContent = 'Search is unavailable right now.';
        }
        if (status) status.textContent = 'Search is unavailable.';
      });
    }

    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () { render(input.value); }, 120);
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      clearTimeout(timer);
      render(input.value);
    });
    input.addEventListener('focus', function () { loadIndex(); });
  });
})(typeof window !== 'undefined' ? window : globalThis);
