#!/usr/bin/env python3
"""Build the Larry Seyer Drums beta tester manual from Markdown.

    python3 tools/manual/build_manual.py
    python3 tools/manual/build_manual.py --check    # report only; do not write
    python3 tools/manual/build_manual.py --strict   # write, but exit 1 on warnings

Source lives in tools/manual/content/. Output is written to
pages/projects/larry-seyer-drums-manual/. There are no third-party
Python dependencies; the Markdown converter is in this file.

Chapter titles are read from each file's front matter (or its first
# heading). They are never hardcoded here.

Nothing is ever pushed by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DEFAULT_SRC = os.path.join(HERE, 'content')
DEFAULT_OUT = os.path.join(REPO, 'pages', 'projects', 'larry-seyer-drums-manual')
HASHES_PATH = os.path.join(HERE, 'banned_hashes.json')
SITE = 'https://larryseyer.com'
URL_BASE = SITE + '/pages/projects/larry-seyer-drums-manual'
IMG = SITE + '/images/projects/larry-seyer-drums-logo-black-1200.png?v=20261109'
TOUCH = '../../../images/projects/larry-seyer-drums-touch-icon.png?v=20261109'
PRICE = re.compile(r'[$€£]\s*\d')
CHAPTER_NAME = re.compile(r'^(\d+)-(.+)\.md$', re.I)

# Asset paths are one directory deeper than pages/projects/*.html.
HEADER = '''  <!-- Header -->
  <header class="header">
    <div class="container">
      <a href="../../../index.html" class="logo">Larry Seyer</a>
      <button class="nav-toggle" aria-label="Toggle navigation">&#9776;</button>
      <nav class="nav">
        <a href="../../work.html">Work</a>
        <a href="../../clients.html">Clients</a>
        <a href="../../work.html#press">Press</a>
        <a href="../../projects.html" class="active">Projects</a>
        <a href="../../music.html">Music</a>
        <a href="../../live.html">Live</a>
        <a href="../../kits.html">Drum Kits</a>
        <a href="../../connect.html">Connect</a>
      </nav>
    </div>
  </header>
'''

FOOTER = '''  <!-- Footer -->
  <footer class="footer">
    <div class="container">
      <p>&copy; <span id="year">2025</span> Larry Seyer. All rights reserved.</p>
      <div class="social-links">
        <a href="/pages/press.html">Press kit</a>
        <a href="https://github.com/larryseyer" target="_blank" rel="noopener noreferrer">GitHub</a>
        <a href="https://www.youtube.com/@larryseyer" target="_blank" rel="noopener noreferrer">YouTube</a>
        <a href="https://www.facebook.com/LarrySeyerOfficialPage" target="_blank" rel="noopener noreferrer">Facebook</a>
        <a href="https://rumble.com/c/larryseyer" target="_blank" rel="noopener noreferrer">Rumble</a>
        <a href="https://open.spotify.com/artist/43rLqZlw7co7eyccfN9zRj" target="_blank" rel="noopener noreferrer">Spotify</a>
        <a href="https://music.apple.com/us/artist/larry-seyer/20363332" target="_blank" rel="noopener noreferrer">Apple Music</a>
        <a href="https://music.amazon.com/artists/B00137FA36/larry-seyer" target="_blank" rel="noopener noreferrer">Amazon Music</a>
        <a href="https://music.youtube.com/@larryseyer" target="_blank" rel="noopener noreferrer">YouTube Music</a>
        <a href="https://suno.com/@larryseyer?page=songs" target="_blank" rel="noopener noreferrer">Suno</a>
        <a href="https://www.linkedin.com/in/larryseyer" target="_blank" rel="noopener noreferrer">LinkedIn</a>
      </div>
    </div>
  </footer>

  <script src="../../../js/main.js"></script>
  <script src="manual.js"></script>
'''

BETA_NOTICE = (
    '<aside class="manual-notice" role="note">'
    '<p class="kicker">Beta</p>'
    '<p>This is a temporary guide for Larry Seyer Drums beta testers, until '
    'the tutorial videos are ready. Details may change as the beta continues.</p>'
    '</aside>'
)

PLACEHOLDER_NOTICE = (
    '<aside class="manual-placeholder" role="status">'
    '<p class="kicker">Content coming soon</p>'
    '<p>This chapter is a stub so the manual&rsquo;s layout, navigation and '
    'search can be previewed. Approved text will replace this placeholder.</p>'
    '</aside>'
)


def h16(s: str) -> str:
    return hashlib.sha256(s.lower().encode()).hexdigest()[:16]


def typography(s: str) -> str:
    """Escape for HTML and use typographic apostrophes and dashes."""
    s = html.escape(s, quote=False)
    s = s.replace("'", '&rsquo;')
    s = s.replace(' -- ', ' &mdash; ')
    return s


def typography_keep_entities(s: str) -> str:
    """Like typography(), but allow already-written &rsquo; / &mdash; / &amp; in source."""
    placeholders = []

    def stash(m):
        placeholders.append(m.group(0))
        return '\x00E%d\x00' % (len(placeholders) - 1)

    s = re.sub(r'&(?:[a-zA-Z][a-zA-Z0-9]+|#\d+|#x[0-9a-fA-F]+);', stash, s)
    s = typography(s)
    for i, ent in enumerate(placeholders):
        s = s.replace('\x00E%d\x00' % i, ent)
    return s


def slugify(text: str) -> str:
    text = html.unescape(re.sub(r'&(?:rsquo|apos|#39|#x27);', '', text, flags=re.I))
    text = text.lower()
    text = text.replace("'", '').replace('\u2019', '')
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'section'


def unique_id(base: str, used: set) -> str:
    slug = slugify(base)
    candidate = slug
    n = 2
    while candidate in used:
        candidate = '%s-%d' % (slug, n)
        n += 1
    used.add(candidate)
    return candidate


def load_hashes() -> dict:
    if not os.path.isfile(HASHES_PATH):
        return {}
    data = json.load(open(HASHES_PATH, encoding='utf-8'))
    return data.get('hashes') or {}


def banned_terms(text: str, hashes: dict) -> list:
    w = re.findall(r"[a-z0-9]+", text.lower())
    grams = set(w) | {a + ' ' + b for a, b in zip(w, w[1:])}
    return sorted(g for g in grams if h16(g) in hashes)


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith('---'):
        return {}, text
    # Allow a leading BOM already stripped by the reader.
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}, text
    meta = {}
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end = i
            break
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip().lower()
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        if key == 'placeholder':
            meta[key] = val.lower() in ('true', 'yes', '1')
        else:
            meta[key] = val
    if end is None:
        return {}, text
    body = '\n'.join(lines[end + 1:])
    if body.startswith('\n'):
        body = body[1:]
    return meta, body


def extract_leading_h1(body: str) -> tuple[Optional[str], str]:
    """If the body starts with a # heading, return (title, rest)."""
    m = re.match(r'(?:\s*<!--.*?-->\s*)*^\s*#\s+(.+?)\s*$', body, re.M | re.S)
    # Simpler line-based scan that skips comments and blanks.
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith('<!--'):
            while i < len(lines) and '-->' not in lines[i]:
                i += 1
            i += 1
            continue
        break
    if i < len(lines):
        m = re.match(r'^#\s+(.+?)\s*$', lines[i])
        if m:
            title = m.group(1).strip()
            rest = '\n'.join(lines[:i] + lines[i + 1:])
            if rest.startswith('\n'):
                rest = rest[1:]
            return title, rest
    return None, body


def strip_comments(text: str) -> str:
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


# ---------- Markdown converter ----------

@dataclass
class Heading:
    level: int
    text: str
    id: str
    plain: str


@dataclass
class Converted:
    html: str
    headings: list
    plain_sections: list  # dicts: id, title, text, level
    warnings: list


def split_fence_blocks(text: str) -> list:
    """Return a list of ('text'|'code', value, lang?)."""
    parts = []
    pattern = re.compile(r'^```([^\n`]*)\n(.*?)(?:\n```|\n```$|```$)', re.M | re.S)
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            parts.append(('text', text[pos:m.start()], None))
        parts.append(('code', m.group(2), (m.group(1) or '').strip()))
        pos = m.end()
        if pos < len(text) and text[pos] == '\n':
            pos += 1
    if pos < len(text):
        parts.append(('text', text[pos:], None))
    return parts or [('text', text, None)]


def collect_ref_links(text: str) -> tuple[str, dict]:
    refs = {}

    def keep(m):
        refs[m.group(1).lower()] = (m.group(2).strip(), (m.group(3) or '').strip())
        return ''

    text = re.sub(
        r'^\s*\[([^\]]+)\]:\s+(\S+)(?:\s+"([^"]*)")?\s*$',
        keep,
        text,
        flags=re.M,
    )
    return text, refs


def rewrite_md_href(href: str, slugs_by_file: dict) -> str:
    if not href or href.startswith(('#', 'mailto:', 'http://', 'https://', '/')):
        return href
    path, frag = (href.split('#', 1) + [''])[:2]
    frag = ('#' + frag) if frag else ''
    base = os.path.basename(path)
    if base in slugs_by_file:
        return slugs_by_file[base] + '.html' + frag
    if base.endswith('.md'):
        # Unknown chapter file; still drop the extension rather than 404 as .md
        slug = re.sub(r'^\d+-', '', base[:-3])
        return slug + '.html' + frag
    return href


def inline(text: str, refs: dict, slugs_by_file: dict, used_ids: set, warnings: list, src_name: str) -> str:
    parts = []
    pos = 0
    # Image, link, code, autolink. Process left to right.
    token = re.compile(
        r'(?P<code>`+)(?P<body>.*?)(?P=code)'
        r'|(?P<img>!\[(?P<ialt>[^\]]*)\]\((?P<isrc>[^)\s]+)(?:\s+"(?P<title>[^"]*)")?\))'
        r'|(?P<link>\[(?P<ltext>[^\]]+)\]\((?P<lhref>[^)\s]+)(?:\s+"(?P<ltitle>[^"]*)")?\))'
        r'|(?P<rlink>\[(?P<rtext>[^\]]+)\]\[(?P<rid>[^\]]*)\])'
        r'|(?P<auto><(?P<aurl>https?://[^>\s]+)>)'
    )

    def style(s: str) -> str:
        s = typography_keep_entities(s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'__(.+?)__', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
        s = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<em>\1</em>', s)
        return s

    for m in token.finditer(text):
        if m.start() > pos:
            parts.append(style(text[pos:m.start()]))
        if m.group('code') is not None:
            parts.append('<code>%s</code>' % html.escape(m.group('body'), quote=False))
        elif m.group('img') is not None:
            src = m.group('isrc').strip()
            alt = m.group('ialt') or ''
            title = m.group('title')
            if src.startswith('../') or src.startswith('/') and not src.startswith('/images/'):
                if src.startswith('../'):
                    warnings.append('%s: image path climbs out of the content folder: %s' % (src_name, src))
            if not alt.strip():
                warnings.append('%s: image is missing alt text (%s)' % (src_name, src))
            img = '<img src="%s" alt="%s"%s>' % (
                html.escape(src, quote=True),
                html.escape(alt, quote=True),
                (' title="%s"' % html.escape(title, quote=True)) if title else '',
            )
            if title:
                parts.append('<figure>%s<figcaption>%s</figcaption></figure>' % (img, typography_keep_entities(title)))
            else:
                parts.append(img)
        elif m.group('link') is not None:
            href = rewrite_md_href(m.group('lhref').strip(), slugs_by_file)
            label = inline(m.group('ltext'), refs, slugs_by_file, used_ids, warnings, src_name)
            # Avoid infinite recursion on nested oddities: label is already simple.
            parts.append('<a href="%s">%s</a>' % (html.escape(href, quote=True), label))
        elif m.group('rlink') is not None:
            rid = (m.group('rid') or m.group('rtext')).strip().lower()
            dest = refs.get(rid)
            if dest:
                href = rewrite_md_href(dest[0], slugs_by_file)
                label = typography_keep_entities(m.group('rtext'))
                parts.append('<a href="%s">%s</a>' % (html.escape(href, quote=True), label))
            else:
                parts.append(style(m.group(0)))
        elif m.group('auto') is not None:
            url = m.group('aurl')
            parts.append('<a href="%s">%s</a>' % (html.escape(url, quote=True), html.escape(url, quote=False)))
        pos = m.end()
    if pos < len(text):
        parts.append(style(text[pos:]))
    return ''.join(parts)


def _heading_html(level: int, ident: str, inner: str) -> str:
    return (
        '<h%d id="%s"><a class="manual-heading-anchor" href="#%s">%s</a>'
        '<button type="button" class="manual-copy-link" data-anchor="%s" '
        'aria-label="Copy link to this section">#</button></h%d>'
        % (level, ident, ident, inner, ident, level)
    )


def convert_blocks(text: str, refs: dict, slugs_by_file: dict, used_ids: set,
                   warnings: list, src_name: str) -> tuple[str, list]:
    headings = []
    lines = text.splitlines()
    out = []
    i = 0

    def flush_para(buf):
        if buf:
            para = inline(' '.join(buf), refs, slugs_by_file, used_ids, warnings, src_name)
            out.append('<p>%s</p>' % para)
            buf.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        hm = re.match(r'^(#{2,4})\s+(.+?)\s*#*\s*$', stripped)
        if hm:
            level = len(hm.group(1))
            raw = hm.group(2).strip()
            ident = unique_id(raw, used_ids)
            inner = inline(raw, refs, slugs_by_file, used_ids, warnings, src_name)
            plain = re.sub(r'<[^>]+>', '', inner)
            headings.append(Heading(level, inner, ident, html.unescape(plain.replace('&rsquo;', "'"))))
            out.append(_heading_html(level, ident, inner))
            i += 1
            continue

        # A leftover h1 in the body is rendered as h2 so the page keeps a single h1.
        if re.match(r'^#\s+', stripped):
            raw = re.sub(r'^#\s+', '', stripped).strip()
            ident = unique_id(raw, used_ids)
            inner = inline(raw, refs, slugs_by_file, used_ids, warnings, src_name)
            plain = re.sub(r'<[^>]+>', '', inner)
            headings.append(Heading(2, inner, ident, html.unescape(plain.replace('&rsquo;', "'"))))
            out.append(_heading_html(2, ident, inner))
            i += 1
            continue

        dm = re.match(r'^:::\s*(iphone|mac)\s*$', stripped, re.I)
        if dm:
            kind = dm.group(1).lower()
            i += 1
            inner_lines = []
            closed = False
            while i < len(lines):
                if re.match(r'^:::\s*$', lines[i].strip()):
                    closed = True
                    i += 1
                    break
                if re.match(r'^:::\s+\S+', lines[i].strip()):
                    break
                inner_lines.append(lines[i])
                i += 1
            if not closed:
                warnings.append('%s: unclosed device block (:::%s)' % (src_name, kind))
            inner_html, inner_heads = convert_blocks(
                '\n'.join(inner_lines).strip(), refs, slugs_by_file, used_ids, warnings, src_name
            )
            headings.extend(inner_heads)
            label = 'On iPhone' if kind == 'iphone' else 'On Mac and iPad'
            out.append(
                '<div class="manual-device-block" data-device="%s">'
                '<p class="manual-device-label">%s</p>%s</div>'
                % (kind, typography(label), inner_html)
            )
            continue

        unknown = re.match(r'^:::\s+(\S+)', stripped)
        if unknown:
            warnings.append(
                '%s: unknown device block (:::%s); use iphone or mac' % (src_name, unknown.group(1))
            )
            i += 1
            continue

        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', stripped):
            out.append('<hr>')
            i += 1
            continue

        if '|' in line and i + 1 < len(lines) and re.match(r'^\s*\|?\s*:?-{3,}', lines[i + 1]):
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            out.append(_render_table(table_lines, refs, slugs_by_file, used_ids, warnings, src_name))
            continue

        if stripped.startswith('>'):
            quote = []
            while i < len(lines) and (lines[i].strip().startswith('>') or (quote and lines[i].strip() == '')):
                q = lines[i].strip()
                if q.startswith('>'):
                    q = re.sub(r'^>\s?', '', q)
                quote.append(q)
                i += 1
            inner_html, _ = convert_blocks('\n'.join(quote).strip(), refs, slugs_by_file, used_ids, warnings, src_name)
            out.append('<blockquote>%s</blockquote>' % inner_html)
            continue

        ulm = re.match(r'^(\s*)([-*+])\s+(.+)$', line)
        olm = re.match(r'^(\s*)(\d+)[.)]\s+(.+)$', line)
        if ulm or olm:
            i = _render_list(lines, i, out, refs, slugs_by_file, used_ids, warnings, src_name)
            continue

        buf = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r'^(#{1,4}\s|```|:::(?:\s|$)|(-{3,}|\*{3,}|_{3,})$|\s*[-*+]\s|\s*\d+[.)]\s|>)', lines[i]
        ) and not ( '|' in lines[i] and i + 1 < len(lines) and re.match(r'^\s*\|?\s*:?-{3,}', lines[i + 1])):
            buf.append(lines[i].strip())
            i += 1
        flush_para(buf)

    return '\n'.join(out), headings


def _split_row(row: str) -> list:
    row = row.strip()
    if row.startswith('|'):
        row = row[1:]
    if row.endswith('|'):
        row = row[:-1]
    return [c.strip() for c in row.split('|')]


def _render_table(table_lines, refs, slugs_by_file, used_ids, warnings, src_name) -> str:
    if len(table_lines) < 2:
        return ''
    headers = _split_row(table_lines[0])
    rows = []
    for line in table_lines[2:]:
        if re.match(r'^\s*\|?\s*:?-{3,}', line):
            continue
        cells = _split_row(line)
        # Pad / trim to header width
        if len(cells) < len(headers):
            cells += [''] * (len(headers) - len(cells))
        rows.append(cells[:len(headers)])
    th = ''.join('<th>%s</th>' % inline(h, refs, slugs_by_file, used_ids, warnings, src_name) for h in headers)
    body = []
    for cells in rows:
        tds = ''.join('<td>%s</td>' % inline(c, refs, slugs_by_file, used_ids, warnings, src_name) for c in cells)
        body.append('<tr>%s</tr>' % tds)
    return (
        '<div class="manual-table-wrap"><table><thead><tr>%s</tr></thead>'
        '<tbody>%s</tbody></table></div>' % (th, ''.join(body))
    )


def _render_list(lines, i, out, refs, slugs_by_file, used_ids, warnings, src_name) -> int:
    def kind_and_indent(line):
        m = re.match(r'^(\s*)([-*+])\s+(.+)$', line)
        if m:
            return 'ul', len(m.group(1).replace('\t', '    ')), m.group(3)
        m = re.match(r'^(\s*)(\d+)[.)]\s+(.+)$', line)
        if m:
            return 'ol', len(m.group(1).replace('\t', '    ')), m.group(3)
        return None, None, None

    first_kind, base, _ = kind_and_indent(lines[i])
    items = []
    while i < len(lines):
        kind, indent, text = kind_and_indent(lines[i])
        if kind and indent is not None and indent <= base and not (kind == first_kind and indent == base) and indent < base:
            break
        if kind and indent == base:
            items.append((kind, [text]))
            i += 1
            # continuation lines
            while i < len(lines):
                nxt = lines[i]
                k2, ind2, t2 = kind_and_indent(nxt)
                if not nxt.strip():
                    # peek: blank then still a child or continuation
                    if i + 1 < len(lines):
                        k3, ind3, _ = kind_and_indent(lines[i + 1])
                        if k3 and ind3 is not None and ind3 > base:
                            i += 1
                            continue
                    break
                if k2 is None and (nxt.startswith(' ' * (base + 2)) or nxt.startswith('\t')):
                    items[-1][1].append(nxt.strip())
                    i += 1
                    continue
                if k2 and ind2 is not None and ind2 > base:
                    # nested list: consume as raw lines into a sub-block
                    nested = []
                    while i < len(lines):
                        k4, ind4, _ = kind_and_indent(lines[i]) if lines[i].strip() else (None, None, None)
                        if not lines[i].strip():
                            # keep blanks inside the nest only if the next line is still nested
                            if i + 1 < len(lines):
                                k5, ind5, _ = kind_and_indent(lines[i + 1])
                                if k5 and ind5 is not None and ind5 > base:
                                    nested.append('')
                                    i += 1
                                    continue
                            break
                        if k4 and ind4 is not None and ind4 > base:
                            nested.append(lines[i])
                            i += 1
                            continue
                        if k4 and ind4 is not None and ind4 <= base:
                            break
                        if lines[i].startswith(' ' * (base + 2)) or lines[i].startswith('\t'):
                            nested.append(lines[i])
                            i += 1
                            continue
                        break
                    items[-1][1].append('__NEST__\n' + '\n'.join(nested))
                    continue
                break
            continue
        break

    # All top-level items should share first_kind; mixed lists split naturally.
    chunks = ['<%s>' % first_kind]
    for kind, parts in items:
        nest_html = ''
        text_parts = []
        for part in parts:
            if part.startswith('__NEST__\n'):
                sub, _ = convert_blocks(part[len('__NEST__\n'):], refs, slugs_by_file, used_ids, warnings, src_name)
                nest_html += sub
            else:
                text_parts.append(part)
        label = inline(' '.join(text_parts), refs, slugs_by_file, used_ids, warnings, src_name)
        chunks.append('<li>%s%s</li>' % (label, nest_html))
    chunks.append('</%s>' % first_kind)
    out.append(''.join(chunks))
    return i


def convert_markdown(src: str, slugs_by_file: dict, src_name: str) -> Converted:
    warnings = []
    used_ids = set()
    chunks = []
    headings = []
    raw_for_refs = src
    # Reference links should be visible in text parts only.
    text_joined = []
    for kind, value, lang in split_fence_blocks(src):
        if kind == 'text':
            text_joined.append(value)
    _, refs = collect_ref_links('\n'.join(text_joined))

    for kind, value, lang in split_fence_blocks(src):
        if kind == 'code':
            chunks.append('<pre><code>%s</code></pre>' % html.escape(value, quote=False))
            continue
        value, _ = collect_ref_links(value)
        html_part, heads = convert_blocks(value, refs, slugs_by_file, used_ids, warnings, src_name)
        chunks.append(html_part)
        headings.extend(heads)

    html_out = '\n'.join(c for c in chunks if c)

    # Plain-text sections for the search index: body text under each heading,
    # plus a lead section for content before the first heading.
    plain_full = re.sub(r'<pre>.*?</pre>', ' ', html_out, flags=re.S)
    plain_full = re.sub(r'<[^>]+>', ' ', plain_full)
    plain_full = html.unescape(plain_full)
    plain_full = re.sub(r'\s+', ' ', plain_full).strip()

    sections = []
    parts = re.split(r'(<h[2-4] id="[^"]+"[\s\S]*?</h[2-4]>)', html_out)
    sections = []
    lead = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', parts[0]))).strip()
    sections.append({'id': '', 'title': '', 'text': lead, 'level': 0})
    for j in range(1, len(parts), 2):
        block = parts[j]
        body = parts[j + 1] if j + 1 < len(parts) else ''
        hm = re.match(r'<h([2-4]) id="([^"]+)"', block)
        if not hm:
            continue
        tm = re.search(r'class="manual-heading-anchor"[^>]*>(.*?)</a>', block)
        title = html.unescape(re.sub(r'<[^>]+>', '', tm.group(1) if tm else ''))
        text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body))).strip()
        sections.append({'id': hm.group(2), 'title': title, 'text': text, 'level': int(hm.group(1))})

    return Converted(html=html_out, headings=headings, plain_sections=sections, warnings=warnings)


# ---------- Pages ----------

@dataclass
class Chapter:
    number: int  # 0 = index
    slug: str
    filename: str  # source basename
    src_path: str
    title: str
    summary: str
    placeholder: bool
    body_md: str
    url: str
    converted: Optional[Converted] = None


def typographic_title(title: str) -> str:
    return typography_keep_entities(title)


def read_source(src_dir: str) -> tuple[Optional[Chapter], list, list]:
    warnings = []
    if not os.path.isdir(src_dir):
        raise SystemExit('content folder not found: %s' % src_dir)
    names = sorted(os.listdir(src_dir))
    index = None
    chapters = []
    slugs_seen = set()
    for name in names:
        path = os.path.join(src_dir, name)
        if not os.path.isfile(path) or not name.endswith('.md'):
            continue
        raw = open(path, encoding='utf-8-sig').read()
        meta, body = parse_front_matter(raw)
        body = body.replace('\r\n', '\n')
        h1, body = extract_leading_h1(body)
        title = (meta.get('title') or h1 or '').strip()
        if not title:
            warnings.append('%s: missing title (set front matter title: or a leading # heading)' % name)
            title = name
        summary = (meta.get('summary') or '').strip()
        placeholder = bool(meta.get('placeholder'))
        if name.lower() == 'index.md':
            index = Chapter(0, 'index', name, path, title, summary, placeholder, body, 'index.html')
            continue
        m = CHAPTER_NAME.match(name)
        if not m:
            warnings.append('%s: skipped; chapter files must be named NN-slug.md' % name)
            continue
        number = int(m.group(1))
        slug = m.group(2)
        if slug in slugs_seen:
            warnings.append('%s: duplicate slug "%s"' % (name, slug))
        slugs_seen.add(slug)
        chapters.append(Chapter(number, slug, name, path, title, summary, placeholder, body, slug + '.html'))
    chapters.sort(key=lambda c: (c.number, c.slug))
    if not index:
        warnings.append('index.md is missing; a contents page will still be generated with a default title')
        index = Chapter(0, 'index', 'index.md', os.path.join(src_dir, 'index.md'),
                        'Beta Tester Guide', '', False, '', 'index.html')
    return index, chapters, warnings


def slugs_map(index: Chapter, chapters: list) -> dict:
    mapping = {index.filename: 'index'}
    for ch in chapters:
        mapping[ch.filename] = ch.slug
        mapping[ch.slug + '.md'] = ch.slug
    return mapping


def scan_terms(chapter: Chapter, hashes: dict) -> list:
    warnings = []
    # Scan the raw markdown plus the resolved title/summary, not the HTML tags.
    text = '\n'.join([chapter.title, chapter.summary, strip_comments(chapter.body_md)])
    for i, line in enumerate(text.splitlines(), 1):
        bad = banned_terms(line, hashes)
        if bad:
            warnings.append('%s:%d: blocklisted term' % (chapter.filename, i))
        if PRICE.search(line):
            warnings.append('%s:%d: price-like token' % (chapter.filename, i))
    return warnings


def section_toc_html(headings: list) -> str:
    items = [h for h in headings if h.level in (2, 3)]
    if not items:
        return ''
    out = ['<ul class="manual-toc-sections">']
    for h in items:
        cls = ' class="manual-toc-h3"' if h.level == 3 else ''
        out.append('<li%s><a href="#%s">%s</a></li>' % (cls, h.id, h.text))
    out.append('</ul>')
    return '\n'.join(out)


def sidebar_html(index: Chapter, chapters: list, current: Chapter, show_sections: bool) -> str:
    items = []
    # Contents link
    cur = ' aria-current="page"' if current.number == 0 else ''
    items.append('<li><a href="index.html"%s>Contents</a></li>' % cur)
    for ch in chapters:
        cur = ' aria-current="page"' if ch.slug == current.slug else ''
        sub = ''
        if show_sections and ch.slug == current.slug and ch.converted:
            sub = section_toc_html(ch.converted.headings)
        items.append(
            '<li><a href="%s"%s><span class="manual-toc-num">%02d</span>%s</a>%s</li>'
            % (ch.url, cur, ch.number, typographic_title(ch.title), sub)
        )
    return '''      <aside class="manual-sidebar" id="manual-toc">
        <p class="manual-sidebar__label">This guide</p>
        <form class="manual-search" role="search" data-index="search-index.json" action="#" method="get">
          <label class="visually-hidden" for="manual-q" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)">Search this guide</label>
          <input id="manual-q" type="search" name="q" placeholder="Search this guide" autocomplete="off">
          <div class="manual-search-status" role="status" aria-live="polite"></div>
          <ul class="manual-search-results is-idle"></ul>
          <p class="manual-search-empty" hidden></p>
        </form>
        <nav aria-label="Guide contents">
          <ul class="manual-toc">
            %s
          </ul>
        </nav>
      </aside>''' % '\n            '.join(items)


def pager_html(chapters: list, current: Chapter) -> str:
    if current.number == 0:
        if not chapters:
            return ''
        first = chapters[0]
        return (
            '<nav class="manual-pager" aria-label="Chapter">'
            '<a rel="next" href="%s"><span class="manual-pager-dir">Next</span>'
            '<span>%s %s</span></a></nav>'
            % (first.url, '%02d' % first.number, typographic_title(first.title))
        )
    idx = next((i for i, c in enumerate(chapters) if c.slug == current.slug), None)
    if idx is None:
        return ''
    prev = chapters[idx - 1] if idx > 0 else None
    nxt = chapters[idx + 1] if idx + 1 < len(chapters) else None
    parts = ['<nav class="manual-pager" aria-label="Chapter">']
    if prev:
        parts.append(
            '<a rel="prev" href="%s"><span class="manual-pager-dir">Previous</span>'
            '<span>%s %s</span></a>' % (prev.url, '%02d' % prev.number, typographic_title(prev.title))
        )
    else:
        parts.append(
            '<a rel="prev" href="index.html"><span class="manual-pager-dir">Previous</span>'
            '<span>Contents</span></a>'
        )
    if nxt:
        parts.append(
            '<a rel="next" href="%s"><span class="manual-pager-dir">Next</span>'
            '<span>%s %s</span></a>' % (nxt.url, '%02d' % nxt.number, typographic_title(nxt.title))
        )
    parts.append('</nav>')
    return ''.join(parts)


def page_head(title: str, description: str, canonical: str) -> str:
    desc = typographic_title(description or title)
    # Strip tags from meta
    desc = re.sub(r'<[^>]+>', '', desc)
    full_title = typographic_title(title)
    if 'Larry Seyer Drums' not in html.unescape(re.sub(r'&(?:rsquo|amp);', "'", full_title)):
        shown = full_title + ' - Larry Seyer Drums'
    else:
        shown = full_title + ' - Larry Seyer'
    return f'''<!DOCTYPE html>
<html lang="en">
<!--
  GENERATED FILE. Do not edit by hand.
  Regenerate with: python3 tools/manual/build_manual.py
  Source Markdown lives in tools/manual/content/.
-->
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-TS207FNV53"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-TS207FNV53');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{html.escape(re.sub(r'<[^>]+>', '', desc), quote=True)}">
  <meta property="og:title" content="{html.escape(re.sub(r'<[^>]+>', '', shown), quote=True)}">
  <meta property="og:description" content="{html.escape(re.sub(r'<[^>]+>', '', desc), quote=True)}">
  <meta property="og:image" content="{IMG}">
  <meta property="og:image:alt" content="Larry Seyer Drums logo">
  <meta property="og:url" content="{canonical}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:image" content="{IMG}">
  <meta name="twitter:image:alt" content="Larry Seyer Drums logo">
  <title>{shown}</title>
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="../../../css/style.css">
  <link rel="stylesheet" href="manual.css">
  <link rel="icon" type="image/x-icon" href="../../../favicon.ico">
  <link rel="apple-touch-icon" href="{TOUCH}">
  <script>
    (function () {{
      try {{
        var key = 'lsd-manual-device';
        var value = localStorage.getItem(key);
        if (value !== 'iphone' && value !== 'mac') {{
          var phone = /iPhone|iPod/i.test(navigator.userAgent || '');
          var narrow = window.matchMedia && window.matchMedia('(max-width: 600px)').matches;
          value = (phone || narrow) ? 'iphone' : 'mac';
        }}
        document.documentElement.setAttribute('data-manual-device', value);
      }} catch (e) {{}}
    }})();
  </script>
</head>
'''


def device_switch_html() -> str:
    return (
        '<div class="manual-device-switch" role="group" aria-label="Device view">\n'
        '  <button type="button" class="manual-device-switch__btn" data-device="iphone" '
        'aria-pressed="false">iPhone</button>\n'
        '  <button type="button" class="manual-device-switch__btn" data-device="mac" '
        'aria-pressed="false">Mac &amp; iPad</button>\n'
        '</div>\n'
    )


def wrap_page(head: str, sidebar: str, article: str) -> str:
    return (
        head + '<body class="manual">\n'
        '  <a class="skip-link" href="#manual-content">Skip to content</a>\n'
        + HEADER
        + '  <button type="button" class="manual-toc-toggle" aria-controls="manual-toc" aria-expanded="false">\n'
        + '    <span class="manual-toc-toggle__icon" aria-hidden="true">&#9776;</span>\n'
        + '    <span class="manual-toc-toggle__label">Contents</span>\n'
        + '  </button>\n'
        + '  <div class="manual-backdrop"></div>\n'
        + '  <div class="manual-shell">\n'
        + sidebar + '\n'
        + '    <article class="manual-article" id="manual-content">\n'
        + article
        + '\n    </article>\n'
        + '  </div>\n'
        + FOOTER
        + '\n</body>\n</html>\n'
    )


def index_article(index: Chapter, chapters: list) -> str:
    body = index.converted.html if index.converted else ''
    items = []
    for ch in chapters:
        summary = typographic_title(ch.summary) if ch.summary else ''
        extra = ' <span class="kicker">Stub</span>' if ch.placeholder else ''
        items.append(
            '<li><a href="%s"><span class="manual-toc-num">%02d</span>%s</a>%s'
            '%s</li>' % (
                ch.url, ch.number, typographic_title(ch.title), extra,
                ('<p>%s</p>' % summary) if summary else '',
            )
        )
    return (
        '<p class="manual-back"><a href="../larry-seyer-drums.html">&larr; Back to Larry Seyer Drums</a></p>\n'
        '<p class="kicker">Larry Seyer Drums</p>\n'
        '<h1>%s</h1>\n' % typographic_title(index.title)
        + BETA_NOTICE + '\n'
        + device_switch_html()
        + (PLACEHOLDER_NOTICE + '\n' if index.placeholder else '')
        + ('<div class="manual-content">\n%s\n</div>\n' % body if body else '')
        + '<ol class="manual-index-list">\n' + '\n'.join(items) + '\n</ol>\n'
        + pager_html(chapters, index)
    )


def chapter_article(ch: Chapter, chapters: list) -> str:
    body = ch.converted.html if ch.converted else ''
    return (
        '<p class="manual-back"><a href="index.html">&larr; All chapters</a> · '
        '<a href="../larry-seyer-drums.html">Larry Seyer Drums</a></p>\n'
        '<p class="kicker">Chapter %02d · Beta tester guide</p>\n'
        '<h1>%s</h1>\n' % (ch.number, typographic_title(ch.title))
        + BETA_NOTICE + '\n'
        + device_switch_html()
        + (PLACEHOLDER_NOTICE + '\n' if ch.placeholder else '')
        + '<div class="manual-content">\n%s\n</div>\n' % body
        + pager_html(chapters, ch)
    )


def build_search_index(index: Chapter, chapters: list) -> dict:
    pages = []

    def page_entry(ch: Chapter) -> dict:
        sections = []
        if ch.converted:
            for sec in ch.converted.plain_sections:
                if not sec['text'] and not sec['title']:
                    continue
                sections.append({
                    'id': sec['id'],
                    'title': sec['title'] or ch.title,
                    'text': sec['text'],
                })
        if not sections:
            sections.append({'id': '', 'title': ch.title, 'text': ch.summary or ''})
        return {
            'id': ch.slug,
            'title': ch.title,
            'url': ch.url,
            'number': ch.number,
            'summary': ch.summary,
            'sections': sections,
        }

    pages.append(page_entry(index))
    for ch in chapters:
        pages.append(page_entry(ch))
    return {'pages': pages}


def copy_assets(out_dir: str) -> int:
    """Copy hand-maintained CSS and JS from this folder into the output dir."""
    count = 0
    os.makedirs(out_dir, exist_ok=True)
    for name in ('manual.css', 'manual.js'):
        src = os.path.join(HERE, name)
        if not os.path.isfile(src):
            continue
        shutil.copy2(src, os.path.join(out_dir, name))
        count += 1
    return count


def copy_images(src_dir: str, out_dir: str) -> int:
    src = os.path.join(src_dir, 'images')
    dest = os.path.join(out_dir, 'images')
    if not os.path.isdir(src):
        return 0
    names = [n for n in os.listdir(src) if n != '.gitkeep' and not n.startswith('.')]
    if not names:
        return 0
    os.makedirs(dest, exist_ok=True)
    count = 0
    for name in names:
        s = os.path.join(src, name)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(dest, name))
            count += 1
    return count


def write_pages(out_dir: str, index: Chapter, chapters: list, search_index: dict, check_only: bool) -> list:
    written = []
    if check_only:
        return written
    os.makedirs(out_dir, exist_ok=True)
    pages = [(index, index_article(index, chapters))]
    for ch in chapters:
        pages.append((ch, chapter_article(ch, chapters)))
    for ch, article in pages:
        sidebar = sidebar_html(index, chapters, ch, show_sections=True)
        desc = ch.summary or ('Larry Seyer Drums beta tester guide: ' + ch.title)
        head = page_head(ch.title if ch.number == 0 else ch.title, desc, URL_BASE + '/' + ch.url)
        html_out = wrap_page(head, sidebar, article)
        path = os.path.join(out_dir, ch.url)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_out)
        written.append(os.path.relpath(path, REPO))
    idx_path = os.path.join(out_dir, 'search-index.json')
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
        f.write('\n')
    written.append(os.path.relpath(idx_path, REPO))
    return written


def self_test() -> list:
    """Tiny converter sanity checks; failures are treated as build errors."""
    errors = []
    slugs = {'02-first-launch.md': 'first-launch'}
    md = (
        '## What\'s included\n\n'
        'See the [next chapter](02-first-launch.md#sound).\n\n'
        '- One\n- Two\n  - Nested\n\n'
        '| Key | Action |\n| --- | --- |\n| `Space` | Play |\n\n'
        'A dash -- like this.\n'
    )
    conv = convert_markdown(md, slugs, 'self-test.md')
    html_out = conv.html
    if 'id="whats-included"' not in html_out:
        errors.append('self-test: heading id for typographic apostrophe failed: ' + html_out[:400])
    if 'first-launch.html#sound' not in html_out:
        errors.append('self-test: .md chapter link was not rewritten')
    if '<ul>' not in html_out or '<li>Nested</li>' not in html_out:
        errors.append('self-test: nested list failed')
    if '<table>' not in html_out or '<code>Space</code>' not in html_out:
        errors.append('self-test: table or inline code failed')
    if '&mdash;' not in html_out or '&rsquo;' not in html_out:
        errors.append('self-test: typography failed: ' + html_out)
    # Price / hash helpers
    if not PRICE.search('costs $99 to unlock'):
        errors.append('self-test: price regex missed $99')

    device_md = (
        '## Layout\n\n'
        'Shared sentence.\n\n'
        '::: iphone\n'
        'Phone only text.\n\n'
        '![Phone shot](images/phone.png "Phone view")\n'
        ':::\n\n'
        '::: mac\n'
        'Mac and iPad only text.\n\n'
        '![Mac shot](images/mac.png "Mac view")\n'
        ':::\n'
    )
    device = convert_markdown(device_md, {}, 'self-test-device.md')
    dhtml = device.html
    if 'data-device="iphone"' not in dhtml or 'data-device="mac"' not in dhtml:
        errors.append('self-test: device blocks missing: ' + dhtml[:500])
    if 'On iPhone' not in dhtml or 'On Mac and iPad' not in dhtml:
        errors.append('self-test: device labels missing')
    if 'images/phone.png' not in dhtml or 'images/mac.png' not in dhtml:
        errors.append('self-test: device images missing')
    if 'Shared sentence.' not in dhtml:
        errors.append('self-test: shared text dropped from device chapter')
    # Search index must include both variants.
    texts = ' '.join(sec['text'] for sec in device.plain_sections)
    if 'Phone only text' not in texts or 'Mac and iPad only text' not in texts:
        errors.append('self-test: search text missed a device variant: ' + texts)
    if device.warnings:
        errors.append('self-test: unexpected device warnings: ' + '; '.join(device.warnings))

    bad = convert_markdown('::: watch\nnope\n:::\n', {}, 'self-test-device.md')
    if not any('unknown device block' in w for w in bad.warnings):
        errors.append('self-test: unknown device fence was not warned')

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description='Build the Larry Seyer Drums beta tester manual.')
    ap.add_argument('--src', default=DEFAULT_SRC, help='Markdown folder (default: tools/manual/content)')
    ap.add_argument('--out', default=DEFAULT_OUT, help='Output folder')
    ap.add_argument('--check', action='store_true', help='report only; do not write the pages')
    ap.add_argument('--strict', action='store_true', help='exit 1 when a wording warning is raised')
    ap.add_argument('--skip-self-test', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()

    src = os.path.abspath(os.path.expanduser(args.src))
    out = os.path.abspath(os.path.expanduser(args.out))
    hashes = load_hashes()
    warnings = []
    errors = []

    if not args.skip_self_test:
        errors.extend(self_test())

    index, chapters, src_warnings = read_source(src)
    warnings.extend(src_warnings)
    mapping = slugs_map(index, chapters)

    for ch in [index] + chapters:
        warnings.extend(scan_terms(ch, hashes))
        body = strip_comments(ch.body_md).strip('\n')
        ch.converted = convert_markdown(body, mapping, ch.filename)
        warnings.extend(ch.converted.warnings)

    if not chapters:
        errors.append('no chapter files found (expected NN-slug.md in %s)' % src)

    search_index = build_search_index(index, chapters)

    for msg in errors:
        print('ERROR: ' + msg, file=sys.stderr)
    for msg in warnings:
        print('WARNING: ' + msg, file=sys.stderr)

    if errors:
        return 1

    written = write_pages(out, index, chapters, search_index, check_only=args.check)
    nimg = 0 if args.check else copy_images(src, out)
    nassets = 0 if args.check else copy_assets(out)

    if args.check:
        print('check ok: %d chapters, %d warnings' % (len(chapters), len(warnings)), file=sys.stderr)
    else:
        for path in written:
            print('wrote %s' % path, file=sys.stderr)
        if nimg:
            print('copied %d image(s)' % nimg, file=sys.stderr)
        if nassets:
            print('copied %d asset(s)' % nassets, file=sys.stderr)
        print('built %d chapters, %d warnings' % (len(chapters), len(warnings)), file=sys.stderr)

    if warnings and (args.strict or args.check):
        # --check reports warnings and still exits 1 so a CI-style run is visible,
        # but wording warnings are not fatal unless --strict is also used? The
        # README says --check is report only and --strict fails on warnings.
        # Keep --check exit 0 when the only issues are warnings, 1 on errors.
        if args.strict:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
