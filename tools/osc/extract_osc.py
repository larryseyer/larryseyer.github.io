#!/usr/bin/env python3
"""Extract the Larry Seyer Drums OSC address list from the app's C++ source.

Reads every OSC registration site (`ControlEntry{<address>, Kind::<kind>,
OscArg::Type::<type>, ...}`) in the app's src/ tree and resolves the address
expression into one or more address templates. Loop indices become ranges
such as <0-95>; helper functions and lambdas are followed back to their call
sites, so every leaf a helper registers is listed under every base it is
registered on.

Usage:
  python3 tools/osc/extract_osc.py [--src PATH] [--json OUT] [--unresolved]

--src defaults to ~/AudioDevelopment/LarrySeyerDrums/src.
Output (stdout or --json): a list of {"address","kind","type","site"} records.
Exit status 2 when any address could not be resolved (printed to stderr).
"""
import argparse
import json
import os
import re
import sys

DEFAULT_SRC = os.path.expanduser("~/AudioDevelopment/LarrySeyerDrums/src")

# ── text helpers ─────────────────────────────────────────────────────────

def mask_comments(t):
    """Blank // and /* */ comments (same length, newlines kept). Strings kept."""
    out = list(t)
    i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c == '"' or c == "'":
            q = c
            i += 1
            while i < n and t[i] != q:
                i += 2 if t[i] == '\\' else 1
            i += 1
        elif t.startswith('//', i):
            j = t.find('\n', i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = ' '
            i = j
        elif t.startswith('/*', i):
            j = t.find('*/', i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != '\n':
                    out[k] = ' '
            i = j
        else:
            i += 1
    return ''.join(out)


def blank_strings(t):
    """Replace string/char literal contents with 'x' so braces inside are inert."""
    out = list(t)
    i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c == '"' or c == "'":
            q = c
            i += 1
            while i < n and t[i] != q:
                if t[i] == '\\':
                    out[i] = 'x'
                    if i + 1 < n:
                        out[i + 1] = 'x'
                    i += 2
                    continue
                if t[i] != '\n':
                    out[i] = 'x'
                i += 1
            i += 1
        else:
            i += 1
    return ''.join(out)


def match_close(code, open_pos, o='{', c='}'):
    depth = 0
    for i in range(open_pos, len(code)):
        if code[i] == o:
            depth += 1
        elif code[i] == c:
            depth -= 1
            if depth == 0:
                return i
    return len(code) - 1


def split_top(expr, sep):
    """Split on `sep` at paren/brace/bracket depth 0, outside string literals."""
    parts, depth, cur, i = [], 0, '', 0
    while i < len(expr):
        ch = expr[i]
        if ch == '"':
            j = i + 1
            while j < len(expr) and expr[j] != '"':
                j += 2 if expr[j] == '\\' else 1
            cur += expr[i:j + 1]
            i = j + 1
            continue
        if ch in '([{<' and not (ch == '<' and sep == ','):
            depth += 1
        elif ch in ')]}>' and not (ch == '>' and sep == ','):
            depth -= 1
        if ch in '([{':
            pass
        if depth == 0 and expr.startswith(sep, i):
            parts.append(cur)
            cur = ''
            i += len(sep)
            continue
        cur += ch
        i += 1
    parts.append(cur)
    return [p.strip() for p in parts]


def split_args(expr):
    """Split call arguments on top-level commas (parens/braces/brackets only)."""
    parts, depth, cur, i = [], 0, '', 0
    while i < len(expr):
        ch = expr[i]
        if ch == '"':
            j = i + 1
            while j < len(expr) and expr[j] != '"':
                j += 2 if expr[j] == '\\' else 1
            cur += expr[i:j + 1]
            i = j + 1
            continue
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        if depth == 0 and ch == ',':
            parts.append(cur.strip())
            cur = ''
            i += 1
            continue
        cur += ch
        i += 1
    if cur.strip():
        parts.append(cur.strip())
    return parts


def strip_parens(e):
    e = e.strip()
    while e.startswith('(') and match_close(e, 0, '(', ')') == len(e) - 1:
        e = e[1:-1].strip()
    return e

# ── model ────────────────────────────────────────────────────────────────

class Callable:
    def __init__(self, f, name, params, start, body_open, body_close, is_lambda):
        self.file, self.name, self.params = f, name, params
        self.start, self.open, self.close = start, body_open, body_close
        self.is_lambda = is_lambda
        self.parent = None


class SrcFile:
    def __init__(self, path, rel):
        self.path, self.rel = path, rel
        raw = open(path, encoding='utf-8', errors='ignore').read()
        self.text = mask_comments(raw)      # strings intact
        self.code = blank_strings(self.text)  # strings blanked
        self.callables = []

    def line(self, pos):
        return self.text.count('\n', 0, pos) + 1


PARAM_NAME = re.compile(r'([A-Za-z_]\w*)\s*(?:=\s*[^,]*)?$')


def param_names(plist):
    names = []
    for p in split_args(plist):
        p = re.sub(r'\[\s*\d*\s*\]$', '', p.strip())
        m = PARAM_NAME.search(p)
        names.append(m.group(1) if m else '')
    return names


FUNC_RE = re.compile(
    r'(?m)^(?:template\s*<[^;{}]*>\s*)?(?:[\w:<>,\*&]+\s+)+\**&?([\w:~]+)\s*\(([^;{}]*)\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?\{')
LAMBDA_HEAD_RE = re.compile(r'\bauto\s+(\w+)\s*=\s*\[[^\]]*\]\s*\(')


def index_callables(sf):
    code = sf.code
    for m in FUNC_RE.finditer(code):
        name = m.group(1).split('::')[-1]
        if name in ('if', 'for', 'while', 'switch', 'return'):
            continue
        o = m.end() - 1
        sf.callables.append(Callable(sf, name, param_names(m.group(2)), m.start(), o,
                                     match_close(code, o), False))
    for m in LAMBDA_HEAD_RE.finditer(code):
        po = m.end() - 1
        pc = match_close(code, po, '(', ')')
        rest = re.match(r'\s*(?:mutable\s*)?(?:->\s*[^{;]+)?\{', code[pc + 1:])
        if not rest:
            continue
        o = pc + rest.end()
        sf.callables.append(Callable(sf, m.group(1), param_names(sf.text[po + 1:pc]), m.start(), o,
                                     match_close(code, o), True))
    for c in sf.callables:
        best = None
        for d in sf.callables:
            if d is c:
                continue
            if d.open < c.start and c.close <= d.close:
                if best is None or d.open > best.open:
                    best = d
        c.parent = best


def innermost(sf, pos):
    best = None
    for c in sf.callables:
        if c.open < pos < c.close and (best is None or c.open > best.open):
            best = c
    return best

# ── resolver ─────────────────────────────────────────────────────────────

class Resolver:
    def __init__(self, files, constants):
        self.files = files
        self.constants = constants
        self.unresolved = []
        self.ambiguous = set()

    # Every call of `callee` (by name) -> (file, pos_of_args_start, args_text)
    def call_sites(self, callee):
        sites = []
        pat = re.compile(r'(?<![\w.>:])' + re.escape(callee.name) + r'\s*(?:<[^;(){}]*>)?\s*\(')
        if callee.is_lambda:
            scope = [(callee.file, callee.close, callee.parent.close if callee.parent else len(callee.file.code))]
        else:
            scope = [(f, 0, len(f.code)) for f in self.files]
        for f, a, b in scope:
            for m in pat.finditer(f.code, a, b):
                # skip the definition itself
                if not callee.is_lambda and f is callee.file and m.start() <= callee.open <= m.end() + 400 and abs(m.start() - callee.start) < 400:
                    continue
                po = m.end() - 1
                pc = match_close(f.code, po, '(', ')')
                args = split_args(f.text[po + 1:pc])
                sites.append((f, m.start(), args))
        return sites

    def loop_range(self, f, pos, var):
        pat = re.compile(r'for\s*\(\s*(?:int|size_t|auto|std::size_t)\s+' + re.escape(var) +
                         r'\s*=\s*([^;]+);\s*' + re.escape(var) + r'\s*(<=|<)\s*([^;]+);')
        best = None
        for m in pat.finditer(f.code, 0, pos):
            best = m
        if not best:
            return None
        lo = self.const(f.text[best.start(1):best.end(1)])
        hi = self.const(f.text[best.start(3):best.end(3)])
        if lo is None or hi is None:
            return None
        if best.group(2) == '<':
            hi -= 1
        return lo, hi

    def const(self, e):
        e = e.strip()
        e = re.sub(r'static_cast<\w+>\((.*)\)', r'\1', e)
        if re.fullmatch(r'-?\d+', e):
            return int(e)
        m = re.fullmatch(r'([\w:]+)\s*([-+])\s*(\d+)', e)
        if m:
            b = self.const(m.group(1))
            return None if b is None else (b + int(m.group(3)) if m.group(2) == '+' else b - int(m.group(3)))
        segs = e.split('::')
        name, quals = segs[-1], [q.lower() for q in segs[:-1] if q]
        cands = None
        if len(segs) >= 2:
            cands = self.constants.get(segs[-2] + '::' + segs[-1])
        cands = cands or self.constants.get(name)
        if not cands:
            return None
        if len({v for _, v in cands}) == 1:
            return cands[0][1]
        def score(c):
            path = c[0].lower()
            return sum(1 for q in quals if q in path)
        best = max(cands, key=score)
        if score(best) == 0:
            self.ambiguous.add(e)
        return best[1]

    def placeholder(self, f, pos, e):
        e = strip_parens(e)
        m = re.fullmatch(r'(\w+)\s*(?:([-+])\s*(\d+))?', e)
        if m:
            r = self.loop_range(f, pos, m.group(1))
            if r:
                off = int(m.group(3) or 0) * (-1 if m.group(2) == '-' else 1)
                return ['<%d-%d>' % (r[0] + off, r[1] + off)]
        return ['<%s>' % e]

    def find_local(self, f, pos, cal, name):
        """Nearest preceding declaration `... name = RHS;` inside the callable chain."""
        pat = re.compile(r'(?:std::string|juce::String|auto|const\s+char\s*\*)\s*&?\s*\b' + re.escape(name) +
                         r'\s*=\s*([^;]+);')
        lo = cal.open if cal else 0
        # search the whole chain up to the outermost callable
        c = cal
        while c and c.parent:
            c = c.parent
        lo = c.open if c else 0
        best = None
        for m in pat.finditer(f.code, lo, pos):
            best = m
        if best:
            return best.start(1), f.text[best.start(1):best.end(1)]
        return None

    def resolve(self, expr, f, pos, cal, depth=0, overrides=None):
        if depth > 12:
            return None
        e = strip_parens(expr)
        # ternary
        q = split_top(e, '?')
        if len(q) == 2:
            ab = split_top(q[1], ':')
            if len(ab) == 2:
                a = self.resolve(ab[0], f, pos, cal, depth + 1)
                b = self.resolve(ab[1], f, pos, cal, depth + 1)
                if a is None or b is None:
                    return None
                return a + b
        terms = split_top(e, '+')
        out = ['']
        for t in terms:
            vals = self.term(t, f, pos, cal, depth)
            if vals is None:
                return None
            out = [o + v for o in out for v in vals]
        return out

    def term(self, t, f, pos, cal, depth):
        t = strip_parens(t)
        m = re.fullmatch(r'(.*)\.toStdString\(\)', t)
        if m:
            return self.resolve(m.group(1), f, pos, cal, depth + 1)
        if re.fullmatch(r'"(?:[^"\\]|\\.)*"(\s*"(?:[^"\\]|\\.)*")*', t):
            return [''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', t))]
        m = re.fullmatch(r'(?:std::string|juce::String)\s*\((.*)\)', t)
        if m:
            inner = m.group(1).strip()
            if inner.startswith('"'):
                return self.resolve(inner, f, pos, cal, depth + 1)
            r = self.ident(inner, f, pos, cal, depth)
            if r is not None:
                return r
            return self.placeholder(f, pos, inner)
        m = re.fullmatch(r'std::to_string\((.*)\)', t)
        if m:
            return self.placeholder(f, pos, m.group(1))
        m = re.fullmatch(r'([\w:]+)\s*\[[^\]]*\]\s*\.\s*(\w+)', t)
        if m:
            rows, fields = self.table(m.group(1).split('::')[-1], f, pos)
            if rows is None or m.group(2) not in fields:
                return None
            i = fields.index(m.group(2))
            return [r[i] for r in rows if i < len(r)]
        if re.fullmatch(r'[A-Za-z_]\w*(?:\.\w+)?(?:\.c_str\(\))?', t):
            return self.ident(t.replace('.c_str()', ''), f, pos, cal, depth)
        return None

    def ident(self, name, f, pos, cal, depth):
        if '.' in name:
            return self.member(name, f, pos, cal)
        # parameter of an enclosing callable?
        c = cal
        while c:
            if name in c.params:
                idx = c.params.index(name)
                vals = []
                for cf, cpos, args in self.call_sites(c):
                    if idx >= len(args):
                        continue
                    r = self.resolve(args[idx], cf, cpos, innermost(cf, cpos), depth + 1)
                    if r is None:
                        return None
                    vals += r
                return vals if vals else None
            # local declared inside this callable before pos?
            c = c.parent
        loc = self.find_local(f, pos, cal, name)
        if loc:
            lpos, rhs = loc
            return self.resolve(rhs, f, lpos, innermost(f, lpos), depth + 1)
        # structured binding / range-for over a literal list or table
        return self.range_for(name, f, pos)

    def range_for(self, name, f, pos):
        # for (const auto& [address, x] : { {"..", ..}, ... })
        pat = re.compile(r'for\s*\(\s*(?:const\s+)?auto\s*&?\s*\[\s*([\w\s,]+)\]\s*:\s*\{')
        best = None
        for m in pat.finditer(f.code, 0, pos):
            best = m
        if best:
            names = [x.strip() for x in best.group(1).split(',')]
            if name in names:
                o = best.end() - 1
                c = match_close(f.code, o)
                body = f.text[o + 1:c]
                idx = names.index(name)
                vals = []
                for grp in re.findall(r'\{([^{}]*)\}', body):
                    a = split_args(grp)
                    if idx < len(a) and a[idx].startswith('"'):
                        vals.append(a[idx].strip('"'))
                return vals or None
        return None

    def member(self, name, f, pos, cal):
        var, field = name.split('.', 1)
        # range-for over a table: for (const auto& var : TABLE)
        pat = re.compile(r'for\s*\(\s*(?:const\s+)?auto\s*&?\s*' + re.escape(var) + r'\s*:\s*([\w:]+)\s*\)')
        best = None
        for m in pat.finditer(f.code, 0, pos):
            best = m
        if not best:
            return None
        table = best.group(1).split('::')[-1]
        rows, fields = self.table(table, f, pos)
        if rows is None:
            return None
        if field not in fields:
            return None
        i = fields.index(field)
        return [r[i] for r in rows if i < len(r)]

    def table(self, table, f, pos):
        """Find `TYPE table[] = { {..}, .. };` (in this file first, then anywhere)."""
        files = [f] + [x for x in self.files if x is not f] + self.extra_files()
        for sf in files:
            m = re.search(r'\b(\w+)\s+' + re.escape(table) + r'\s*\[\s*\]\s*=\s*\{', sf.code)
            if not m:
                m = re.search(r'std::array<\s*(\w+)\s*,[^>]*>\s*' + re.escape(table) + r'\s*=\s*\{', sf.code)
            if not m:
                continue
            typ = m.group(1)
            o = m.end() - 1
            c = match_close(sf.code, o)
            body = sf.text[o + 1:c].strip()
            if body.startswith('{') and match_close(blank_strings(body), 0) == len(body) - 1 \
                    and body[1:].lstrip().startswith('{'):
                body = body[1:-1].strip()   # std::array's extra aggregate braces
            rows = []
            for grp in split_args(body):
                grp = grp.strip()
                if grp.startswith('{') and grp.endswith('}'):
                    rows.append([a.strip().strip('"') for a in split_args(grp[1:-1])])
            fields = self.struct_fields(typ, files)
            return rows, fields
        return None, None

    def struct_fields(self, typ, files):
        for sf in files:
            m = re.search(r'struct\s+' + re.escape(typ) + r'\s*\{', sf.code)
            if m:
                o = m.end() - 1
                c = match_close(sf.code, o)
                body = sf.code[o + 1:c]
                return re.findall(r'(\w+)\s*;', body)
        return []

    _extra = None

    def extra_files(self):
        return self._extra or []


ENTRY_RE = re.compile(r'\bControlEntry(?:\s+[A-Za-z_]\w*)?\s*\{')
REPLY_RE = re.compile(r'sendReply\(\s*"(/drums/[^"]+)"')
KIND_RE = re.compile(r'(?:seyer::osc::)?Kind::(\w+)')
TYPE_RE = re.compile(r'(?:seyer::osc::)?OscArg::Type::(\w+)')


def collect_constants(src):
    """Integer constants (constexpr/const/#define) -> {name: [(path, value)]}.
    Simple expressions such as `kNumPlayers * kSlotsPerPlayer` are evaluated
    from the others. A name defined in more than one place keeps every
    definition; Resolver.const picks by the qualifiers at the use site."""
    raw = []
    pat = re.compile(r'\b(?:constexpr|const)\s+(?:static\s+)?(?:inline\s+)?(?:int|size_t|std::size_t|unsigned|uint8_t|uint32_t|int8_t|int32_t|std::uint8_t|std::int32_t)\s+(k\w+|[A-Z_][A-Z0-9_]+)\s*=\s*([^;{}]+);')
    dpat = re.compile(r'#define\s+([A-Z_][A-Z0-9_]+)\s+(\d+)\b')
    epat = re.compile(r'\benum\s+(?:class\s+|struct\s+)?(\w+)\s*(?::\s*[\w:]+\s*)?\{([^{}]*)\}')
    for root, _, fs in os.walk(src):
        for fn in fs:
            if fn.endswith(('.h', '.hpp', '.cpp', '.mm')):
                path = os.path.join(root, fn)
                try:
                    t = mask_comments(open(path, encoding='utf-8', errors='ignore').read())
                except OSError:
                    continue
                for m in pat.finditer(t):
                    raw.append((m.group(1), path, m.group(2).strip()))
                for m in dpat.finditer(t):
                    raw.append((m.group(1), path, m.group(2)))
                for m in epat.finditer(t):
                    val = -1
                    for item in m.group(2).split(','):
                        item = item.strip()
                        if not item:
                            continue
                        nm = re.match(r'(\w+)\s*(?:=\s*(-?\d+))?', item)
                        if not nm:
                            break
                        val = int(nm.group(2)) if nm.group(2) else val + 1
                        raw.append((m.group(1) + '::' + nm.group(1), path, str(val)))
    consts = {}
    done = set()
    enum_keys = {k for k, _, _ in raw if '::' in k}
    for _ in range(8):
        for i, (k, path, e) in enumerate(raw):
            if i in done:
                continue
            ex = re.sub(r'static_cast<[\w:]+>', '', e)
            ex = re.sub(r'(?:\w+::)*(\w+::\w+)', lambda mm: mm.group(1) if mm.group(1) in enum_keys else mm.group(1).split('::')[-1], ex)
            names = re.findall(r'[A-Za-z_]\w*(?:::\w+)?', ex)
            if any(n not in consts for n in names):
                continue
            for n in sorted(set(names), key=len, reverse=True):
                # same-file definition first, else the first one found
                vals = consts[n]
                v = next((vv for pp, vv in vals if pp == path), vals[0][1])
                ex = re.sub(r'(?<![\w:])%s(?![\w:])' % re.escape(n), str(v), ex)
            if re.fullmatch(r'[\d\s+*/()-]+', ex):
                try:
                    consts.setdefault(k, []).append((path, int(eval(ex.replace('/', '//')))))
                    done.add(i)
                except Exception:
                    done.add(i)
    return consts


IF_RE = re.compile(r'\bif\s*(?:constexpr\s*)?\(')


def enclosing_ifs(sf, pos, cal):
    """Conditions of the if-blocks (inside the same callable) that wrap pos.
    A registration under one exists only when that condition holds at run
    time, which a static read cannot decide, so it is reported, not hidden."""
    if not hasattr(sf, '_ifs'):
        sf._ifs = []
        for m in IF_RE.finditer(sf.code):
            pc = match_close(sf.code, m.end() - 1, '(', ')')
            j = pc + 1
            while j < len(sf.code) and sf.code[j].isspace():
                j += 1
            if j < len(sf.code) and sf.code[j] == '{':
                sf._ifs.append((j, match_close(sf.code, j),
                                ' '.join(sf.text[m.end():pc].split())))
    return [c for o, e, c in sf._ifs if o < pos < e]


def extract(src):
    files = []
    tables = []
    for root, _, fs in os.walk(src):
        for fn in sorted(fs):
            if not fn.endswith(('.cpp', '.h', '.mm')):
                continue
            p = os.path.join(root, fn)
            t = open(p, encoding='utf-8', errors='ignore').read()
            if re.search(r'\bControlEntry(?:\s+\w+)?\s*\{', t):
                files.append(SrcFile(p, os.path.relpath(p, src)))
            elif re.search(r'\b\w+\s+k\w+\s*\[\s*\]\s*=\s*\{|std::array<\s*\w+\s*,[^>]*>\s*k\w+\s*=\s*\{', t):
                tables.append(p)
    for sf in files:
        index_callables(sf)
    res = Resolver(files, collect_constants(src))
    extra = []
    for p in tables:
        sf = SrcFile(p, os.path.relpath(p, src))
        extra.append(sf)
    res._extra = extra

    records = []
    for sf in files:
        if sf.rel.endswith('ControlRegistry.h'):
            continue
        for m in ENTRY_RE.finditer(sf.code):
            o = m.end() - 1
            c = match_close(sf.code, o)
            args = split_args(sf.text[o + 1:c])
            if len(args) < 2:
                continue
            km = KIND_RE.fullmatch(args[1].strip())
            if not km:
                continue
            tm = TYPE_RE.fullmatch(args[2].strip()) if len(args) > 2 else None
            site = '%s:%d' % (sf.rel, sf.line(m.start()))
            cal = innermost(sf, m.start())
            addrs = res.resolve(args[0], sf, m.start(), cal)
            if not addrs:
                res.unresolved.append((site, args[0]))
                continue
            cond = enclosing_ifs(sf, m.start(), cal)
            for a in addrs:
                r = {'address': a, 'kind': km.group(1),
                     'type': tm.group(1) if tm else 'None', 'site': site}
                if cond:
                    r['cond'] = cond
                records.append(r)
    # Reply-only addresses: sent straight back by a handler, never registered.
    for sf in files:
        for m in REPLY_RE.finditer(sf.text):
            records.append({'address': m.group(1), 'kind': 'Reply', 'type': 'String',
                            'site': '%s:%d' % (sf.rel, sf.line(m.start()))})
    # de-duplicate (same address registered once per loop pass is expected)
    seen, out = set(), []
    for r in records:
        k = (r['address'], r['kind'], r['type'])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    for e in sorted(res.ambiguous):
        print('AMBIGUOUS constant %s (several definitions, none matched the qualifiers)' % e, file=sys.stderr)
    return out, res.unresolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEFAULT_SRC)
    ap.add_argument('--json')
    ap.add_argument('--unresolved', action='store_true')
    a = ap.parse_args()
    recs, unresolved = extract(a.src)
    data = json.dumps(recs, indent=1)
    if a.json:
        open(a.json, 'w').write(data + '\n')
    elif not a.unresolved:
        for r in recs:
            print('%-70s %-9s %-7s %s' % (r['address'], r['kind'], r['type'], r['site']))
    for site, e in unresolved:
        print('UNRESOLVED %s  %s' % (site, ' '.join(e.split())), file=sys.stderr)
    print('%d addresses, %d unresolved sites' % (len(recs), len(unresolved)), file=sys.stderr)
    sys.exit(2 if unresolved else 0)


if __name__ == '__main__':
    main()
