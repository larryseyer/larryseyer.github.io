#!/usr/bin/env python3
"""Build pages/projects/larry-seyer-drums-osc.html from the app's OSC source.

    python3 tools/osc/build_osc_page.py [--src ~/AudioDevelopment/LarrySeyerDrums/src] [--check]

1. extract_osc.py reads every OSC address the app registers (read-only).
2. osc_descriptions.json supplies the wording and the page layout.
3. The page is written, unless --check is given (report only).

Exit status 1 when an address has no description, a description no longer
matches an address, or a runtime-conditional registration is not annotated.
Fix osc_descriptions.json and run again. Nothing is ever pushed.
"""
import argparse, hashlib, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import extract_osc  # noqa: E402

OUT = os.path.join(REPO, 'pages', 'projects', 'larry-seyer-drums-osc.html')
TEMPLATE = os.path.join(REPO, 'pages', 'projects', 'larry-seyer-drums-updates.html')
URL = 'https://larryseyer.com/pages/projects/larry-seyer-drums-osc.html'
IMG = 'https://larryseyer.com/images/projects/larry-seyer-drums-logo-black-1200.png?v=20261109'
ORDER = ['basics', 'transport', 'sync', 'midi', 'audio', 'click', 'player', 'synth', 'songs', 'timeline',
         'pills', 'editor', 'energy', 'sounds', 'slots', 'mixer', 'comp', 'tape', 'reverb', 'effects',
         'presets', 'settings', 'importexport', 'shortcuts', 'actions', 'ui', 'testing']
SOURCE_FILES = [
    'seyer-core/include/seyer/osc/ControlRegistry.h', 'seyer-plugin/osc/OscTransport.cpp',
    'seyer-plugin/PluginProcessor.cpp', 'seyer-plugin/osc/OscPublishersPhase2.cpp',
    'seyer-plugin/osc/OscPublishersPhase25.cpp', 'seyer-plugin/osc/OscPublishersConductor.cpp',
    'seyer-plugin/osc/OscPublishersKeystroke.cpp', 'seyer-plugin/osc/RegistrySelfTest.cpp',
    'seyer-plugin/quickpick/QuickPickService.cpp', 'seyer-plugin/settings/AppSettingsPresets.cpp',
    'seyer-plugin/keys/KeyBindingCatalog.h']
PRICE = re.compile(r'[$\u20ac\u00a3]\s*\d')


def h16(s):
    return hashlib.sha256(s.lower().encode()).hexdigest()[:16]


def banned_terms(text, hashes):
    """Words and word pairs whose hash is on the banned list (names are stored only as hashes)."""
    w = re.findall(r'[a-z0-9]+', text.lower())
    grams = set(w) | {a + ' ' + b for a, b in zip(w, w[1:])}
    return sorted(g for g in grams if h16(g) in hashes)


def esc(s):
    """Escape for HTML and use typographic apostrophes and dashes."""
    s = html.escape(s, quote=False)
    s = s.replace("'", '&rsquo;').replace(' -- ', ' &mdash; ')
    return s


def access(kind):
    return {'Command': 'Send', 'Writable': 'Set / read', 'Readable': 'Read', 'Reply': 'Reply'}[kind]


def argtype(kind, typ):
    if kind == 'Readable':
        return {'Bool': '0/1', 'None': '&mdash;'}.get(typ, typ.lower())
    return {'None': '&mdash;', 'Bool': 'int 0/1', 'Int': 'int', 'Float': 'float', 'String': 'string'}[typ]


def action_labels(src):
    t = open(os.path.join(src, 'seyer-plugin/keys/KeyBindingCatalog.h'), encoding='utf-8').read()
    start = t.index('kActions[] = {')
    end = t.index('};', start)
    return {m.group(1): (m.group(2), m.group(3))
            for m in re.finditer(r'\{\s*"([a-z_.0-9]+)",\s*"([^"]*)",\s*"([^"]*)"', t[start:end])}


def build(src):
    recs, unresolved = extract_osc.extract(src)
    data = json.load(open(os.path.join(HERE, 'osc_descriptions.json'), encoding='utf-8'))
    problems = ['UNRESOLVED %s %s' % u for u in unresolved]
    withheld = data['withheld']
    collapse = [(re.compile(a), b) for a, b in data['collapse']]
    labels = action_labels(src)

    fam = {f['id']: f for f in data['families']}
    sec = {s['id']: s for s in data['sections']}
    fam_hits = {k: {} for k in fam}      # leaf -> {base: rec}
    sec_hits = {k: {} for k in sec}      # key -> [recs]
    actions = []
    withheld_seen = []
    bases = sorted(((b, k) for k, f in fam.items() for b in f['bases']), key=lambda x: -len(x[0]))
    row_owner = {}
    for k, s in sec.items():
        for a in s['rows']:
            if a in row_owner:
                problems.append('DUPLICATE description %s' % a)
            row_owner[a] = k

    for r in recs:
        a = r['address']
        if h16(a) in withheld:
            withheld_seen.append(a)
            continue
        if a.startswith('/drums/action/'):
            actions.append(r)
            continue
        key = a
        for rx, rep in collapse:
            if rx.match(a):
                key = rx.sub(rep, a)
                r = dict(r, value=rx.match(a).group(2))
                break
        if key in row_owner:
            sec_hits[row_owner[key]].setdefault(key, []).append(r)
            continue
        for b, k in bases:
            if a.startswith(b):
                leaf = a[len(b):]
                if leaf in fam[k]['rows']:
                    fam_hits[k].setdefault(leaf, {})[b] = r
                    break
        else:
            problems.append('NO DESCRIPTION %s (%s %s, %s)' % (a, r['kind'], r['type'], r['site']))

    for k, f in fam.items():
        for leaf in f['rows']:
            if leaf not in fam_hits[k]:
                problems.append('STALE description %s: %s' % (k, leaf))
        for leaf, hit in fam_hits[k].items():
            for b, r in hit.items():
                if 'cond' in r and 'reviewed' not in f.get('notes', {}).get(leaf, {}):
                    problems.append('UNANNOTATED runtime condition %s%s: %s' % (b, leaf, r['cond']))
    for k, s in sec.items():
        for a in s['rows']:
            if a not in sec_hits[k]:
                problems.append('STALE description %s' % a)
            elif any('cond' in r for r in sec_hits[k][a]):
                problems.append('UNANNOTATED runtime condition %s' % a)
    for k in withheld:
        if k not in {h16(a) for a in withheld_seen}:
            problems.append('STALE withheld entry %s' % k)
    for r in actions:
        if r['address'][len('/drums/action/'):] not in labels:
            problems.append('NO LABEL for %s' % r['address'])

    # ---- render ----
    out, toc, count = [], [], 0

    def table(head, rows):
        o = ['        <div class="osc-table-wrap">', '        <table class="osc-table">',
             '          <thead><tr>' + ''.join('<th>%s</th>' % h for h in head) + '</tr></thead>', '          <tbody>']
        for cells in rows:
            o.append('            <tr>' + ''.join('<td>%s</td>' % c for c in cells) + '</tr>')
        o += ['          </tbody>', '        </table>', '        </div>']
        return o

    for sid in ORDER:
        if sid == 'actions':
            rows = []
            for r in sorted(actions, key=lambda r: (labels.get(r['address'][14:], ('', ''))[0], r['address'])):
                cat, name = labels.get(r['address'][14:], ('', ''))
                rows.append(['<code>%s</code>' % esc(r['address']), esc(cat), esc(name) + '.'])
            count += len(rows)
            toc.append(('actions', 'Actions'))
            out += ['        <h2 id="osc-actions">Actions</h2>',
                    '        <p>Every command that has a keyboard shortcut can be triggered over OSC. Send any integer (for example 1) to run it.</p>']
            out += table(['Address', 'Area', 'Action'], rows)
            continue
        if sid in fam:
            f = fam[sid]
            multi = len(f['bases']) > 1
            toc.append((sid, f['title']))
            out += ['        <h2 id="osc-%s">%s</h2>' % (sid, esc(f['title'])), '        <p>%s</p>' % esc(f['intro'])]
            out.append('        <p>Address prefixes: ' + ', '.join(
                '<code>%s</code>' % esc(b) for b in f['bases']) + '. Add a parameter from the table below to a prefix.</p>')
            rows = []
            for leaf, desc in f['rows'].items():
                hit = fam_hits[sid].get(leaf)
                if not hit:
                    continue
                r = next(iter(hit.values()))
                applies = [b for b in f['bases'] if b in hit and b not in f.get('notes', {}).get(leaf, {}).get('exclude', [])]
                count += len(applies)
                cells = ['<code>%s</code>' % esc(leaf), argtype(r['kind'], r['type']), access(r['kind']), esc(desc)]
                if multi:
                    only = f.get('only', {}).get(leaf)
                    cells.insert(3, esc(only) if only else ('All' if len(applies) == len(f['bases'])
                                 else ', '.join(esc(f['bases'][b]) for b in applies)))
                rows.append(cells)
            head = ['Parameter', 'Argument', 'Access'] + (['Applies to'] if multi else []) + ['Description']
            out += table(head, rows)
            continue
        s = sec[sid]
        toc.append((sid, s['title']))
        out += ['        <h2 id="osc-%s">%s</h2>' % (sid, esc(s['title'])), '        <p>%s</p>' % esc(s['intro'])]
        rows = []
        for a, desc in s['rows'].items():
            hits = sec_hits[sid].get(a)
            if not hits:
                continue
            r = hits[0]
            vals = sorted({h['value'] for h in hits if 'value' in h})
            if '{values}' in desc:
                desc = desc.replace('{values}', ', '.join(vals))
            count += len(hits)
            rows.append(['<code>%s</code>' % esc(a), argtype(r['kind'], r['type']), access(r['kind']), esc(desc)])
        out += table(['Address', 'Argument', 'Access', 'Description'], rows)

    body = '\n'.join(out)
    hashes = set(data.get('banned_hashes', []))
    for line in body.split('\n'):
        text = re.sub(r'<[^>]+>', ' ', line)
        bad = banned_terms(text, hashes)
        if bad or PRICE.search(text):
            problems.append('BANNED WORD %s in page text: %s' % (bad or 'price', line.strip()[:120]))
    return body, toc, count, len(recs), problems, withheld_seen


def page(body, toc, count):
    t = open(TEMPLATE, encoding='utf-8').read()
    header = t[t.index('<body>') + len('<body>'):t.index('<main>')]
    footer = t[t.index('</main>') + len('</main>'):]
    desc = ('Complete OSC command reference for Larry Seyer Drums, The Drum DAW by Larry Seyer: '
            'transport, players, songs, mixer, effects and more.')
    toc_html = '\n'.join('          <li><a href="#osc-%s">%s</a></li>' % (i, esc(n)) for i, n in toc)
    src_list = '\n'.join('       src/' + f for f in SOURCE_FILES)
    return '''<!DOCTYPE html>
<html lang="en">
<!--
  GENERATED FILE. Do not edit by hand.
  This page is generated from the OSC source code of the Larry Seyer Drums app
  and must be kept in sync with it. Regenerate with:
       python3 tools/osc/build_osc_page.py
  Wording lives in tools/osc/osc_descriptions.json. Addresses are read from:
%s
       (and every other source file that registers a ControlEntry)
-->
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-TS207FNV53"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-TS207FNV53');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="%s">
  <meta property="og:title" content="Larry Seyer Drums OSC Reference - Larry Seyer">
  <meta property="og:description" content="Every OSC command Larry Seyer Drums understands, with a short description of each.">
  <meta property="og:image" content="%s">
  <meta property="og:image:alt" content="Larry Seyer Drums logo">
  <meta property="og:url" content="%s">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:image" content="%s">
  <meta name="twitter:image:alt" content="Larry Seyer Drums logo">
  <title>Larry Seyer Drums OSC Reference - Larry Seyer</title>
  <link rel="canonical" href="%s">
  <link rel="stylesheet" href="../../css/style.css">
  <link rel="icon" type="image/x-icon" href="../../favicon.ico">
  <link rel="apple-touch-icon" href="../../images/projects/larry-seyer-drums-touch-icon.png?v=20261109">
  <style>
    .osc-table-wrap { overflow-x: auto; margin: 1rem 0 2rem; }
    .osc-table { width: 100%%; border-collapse: collapse; font-size: .92rem; }
    .osc-table th, .osc-table td { text-align: left; vertical-align: top; padding: .45rem .6rem; border-bottom: 1px solid rgba(128,128,128,.3); }
    .osc-table th { white-space: nowrap; }
    .osc-table td:first-child code { white-space: nowrap; }
    .osc-toc { columns: 2 220px; margin: 1rem 0 2rem; }
  </style>
</head>
<body>%s<main>
    <section class="section" id="osc">
      <div class="container">
        <h1>Larry Seyer Drums OSC Reference</h1>
        <p class="mb-md">Larry Seyer Drums has a complete OSC (Open Sound Control) implementation for controlling virtually every aspect of its operation from another app, a control surface, a script or another computer. This page lists all %d commands. <a href="larry-seyer-drums.html">Back to Larry Seyer Drums</a>.</p>

        <h2 id="osc-connecting">Connecting</h2>
        <ul class="features">
          <li><strong>On by default</strong>OSC control is on in every version. Turn it off or change the port in App Settings &rarr; OSC Control.</li>
          <li><strong>Receive port</strong>Larry Seyer Drums listens for OSC over UDP on port 9100 by default (9200 is the alternative in App Settings). It listens on every network interface, so it can be reached from another device on the same network.</li>
          <li><strong>Replies</strong>Answers are sent back over UDP to port 9101 (the receive port plus one) on the same computer.</li>
          <li><strong>Reading a value</strong>Send an address with no argument and Larry Seyer Drums replies with its current value. Sending a value sets it and the new value comes back as confirmation.</li>
          <li><strong>Live updates</strong>Readable values that change are sent automatically, up to 30 times a second, and a full set of current values is sent when OSC starts.</li>
          <li><strong>Argument types</strong>Arguments are 32-bit integers, 32-bit floats or strings. On/off values are sent and received as the integers 0 and 1. Addresses must match exactly; wildcard patterns are not used.</li>
          <li><strong>Numbering</strong>Players and song lanes are numbered 1-4 where the address says <code>&lt;1-4&gt;</code>. Everything else (mixer channels, buses, effect returns, slots, pills and energy levels) counts from 0. A range such as <code>&lt;0-95&gt;</code> means one address for each number.</li>
        </ul>

        <h2 id="osc-contents">Contents</h2>
        <ul class="osc-toc">
%s
        </ul>

%s
      </div>
    </section>
  </main>%s''' % (src_list, desc, IMG, URL, IMG, URL, header, count, toc_html, body, footer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=extract_osc.DEFAULT_SRC)
    ap.add_argument('--check', action='store_true', help='report only; do not write the page')
    a = ap.parse_args()
    body, toc, count, nrec, problems, withheld = build(os.path.expanduser(a.src))
    if not problems:
        full = page(body, toc, count)
        bad = banned_terms(re.sub(r'<[^>]+>', ' ', full[full.index('<body>'):]), set(
            json.load(open(os.path.join(HERE, 'osc_descriptions.json'), encoding='utf-8')).get('banned_hashes', [])))
        if bad:
            problems.append('BANNED WORD %s in the page' % bad)
    for p in problems:
        print(p, file=sys.stderr)
    print('%d address templates read, %d commands published, %d withheld, %d problems'
          % (nrec, count, len(withheld), len(problems)), file=sys.stderr)
    if problems:
        sys.exit(1)
    if not a.check:
        open(OUT, 'w', encoding='utf-8').write(full)
        print('wrote %s' % os.path.relpath(OUT, REPO), file=sys.stderr)


if __name__ == '__main__':
    main()
