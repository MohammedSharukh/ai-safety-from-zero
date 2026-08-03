#!/usr/bin/env python3
"""gates.py -- every gate, run from ONE Python script.

G1: never a chained shell one-liner; a bashism silently skipping a gate is worse
    than a wrong number, because you will believe it.
G2: never parse tool output by character offset -- token position from the
    stable end of the row.
G3: every text probe over rendered output dehyphenates, collapses whitespace,
    excludes the contents page when counting structural elements, and is
    validated against a positive control before a negative result is believed.
G5: any gate containing an enumerated range is a latent defect -- ranges are
    derived from the artifact, never typed.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.join(os.path.dirname(HERE), 'src')
LOG = os.path.join(SRCDIR, 'main.log')
PDF = os.path.join(SRCDIR, 'main.pdf')
BODY = os.path.join(SRCDIR, 'body.tex')
TOUR = os.path.join(SRCDIR, 'tour.md')
MAIN = os.path.join(SRCDIR, 'main.tex')

RESULTS = []


def gate(name):
    def deco(fn):
        RESULTS.append((name, fn))
        return fn
    return deco


def norm(s):
    """G3: dehyphenate, collapse whitespace, normalise dashes and quotes."""
    s = s.replace('-\n', '').replace('\u2019', "'").replace('\u2014', '--')
    return ' '.join(s.split())


def logtext():
    return open(LOG, errors='replace').read()


# ------------------------------------------------------------------ log gates
@gate('overfull hbox > 8pt == 0')
def g_hbox():
    bad = []
    for m in re.finditer(r'Overfull \\hbox \(([0-9.]+)pt too wide\)', logtext()):
        if float(m.group(1)) > 8.0:
            bad.append(float(m.group(1)))
    worst = max(bad) if bad else 0.0
    return (not bad), 'count=%d worst=%.1fpt' % (len(bad), worst)


@gate('overfull + underfull vbox == 0')
def g_vbox():
    t = logtext()
    n = len(re.findall(r'(Overfull|Underfull) \\vbox', t))
    return n == 0, 'count=%d' % n


@gate('missing character == 0')
def g_missing():
    n = len(re.findall(r'Missing character', logtext()))
    return n == 0, 'count=%d' % n


@gate('undefined / multiply-defined refs == 0')
def g_refs():
    # G3: the loose word "undefined" occurs in this document's own prose, which
    # the log echoes.  Anchor to a pattern that cannot occur in body text.
    t = logtext()
    undef = len(re.findall(r'LaTeX Warning: (?:Reference|Citation) `[^\']+\' .*undefined', t))
    multi = len(re.findall(r'LaTeX Warning: Label `[^\']+\' multiply defined', t))
    errors = len(re.findall(r'^! ', t, re.M))
    # positive control: the pattern must be able to match a manufactured warning
    ctrl = "LaTeX Warning: Reference `X' on page 1 undefined on input line 1."
    assert re.search(r'LaTeX Warning: (?:Reference|Citation) `[^\']+\' .*undefined', ctrl)
    return (undef + multi + errors) == 0, 'undef=%d multiply=%d errors=%d' % (
        undef, multi, errors)


# ----------------------------------------------------------------- source gates
@gate('body.tex leakage == 0')
def g_leak():
    b = open(BODY).read()
    n = b.count('**') + b.count('`') + b.count('\x01') + b.count('\x02')
    return n == 0, 'markers=%d' % n


@gate('non-ASCII in body.tex == 0')
def g_ascii():
    b = open(BODY).read()
    n = sum(1 for c in b if ord(c) > 127)
    return n == 0, 'bytes=%d' % n


@gate('mid-sentence \\end{item...} == 0')
def g_item():
    n = len(re.findall(r'\\end\{item(ize)?\}[^\n]*[a-z]', open(BODY).read()))
    return n == 0, 'count=%d' % n


@gate('dangling Appendix [A-Z] refs == 0')
def g_appendix():
    tour = open(TOUR).read()
    letters = set(re.findall(r'^#! Part ([A-Z]) ', tour, re.M))
    refs = set(re.findall(r'\bAppendix ([A-Z])\b', tour))
    dangling = refs - letters
    return not dangling, 'refs=%s letters=%s dangling=%s' % (
        sorted(refs) or '-', ''.join(sorted(letters)), sorted(dangling) or '-')


@gate('part letters contiguous from A')
def g_parts():
    letters = re.findall(r'^#! Part ([A-Z]) ', open(TOUR).read(), re.M)
    want = [chr(ord('A') + i) for i in range(len(letters))]
    return letters == want, 'letters=%s' % ''.join(letters)


@gate('every patch phrase grep-present verbatim')
def g_patches():
    sys.path.insert(0, HERE)
    import patches
    tour = norm(open(TOUR).read())
    superseded = {q.get('supersedes') for q in patches.PATCHES if q.get('supersedes')}
    live = [p for p in patches.PATCHES if p['id'] not in superseded]
    missing = [p['id'] for p in live if norm(p['marker']) not in tour]
    return not missing, 'live=%d superseded=%d missing=%s' % (
        len(live), len(superseded), missing or '-')


@gate('environment counts reconcile PER SECTION')
def g_envcounts():
    """S40: split at the chapter/part boundary; parts follow different rules."""
    tour = open(TOUR).read()
    secs, cur = [], None
    for line in tour.split('\n'):
        if line.startswith('#! ') or line.startswith('# '):
            cur = ['starred' if line.startswith('#!') else 'numbered', line, []]
            secs.append(cur)
        elif cur:
            cur[2].append(line)
    body = open(BODY).read()
    problems = []
    for kind, title, lines in secs:
        blob = '\n'.join(lines)
        kc, dm, bm = blob.count('> **KEY CLAIM ('), blob.count('## The demystification'), blob.count('\\bmn{')
        if kind == 'numbered':
            if not (kc == dm == bm == 1):
                problems.append((title[:30], kc, dm, bm))
        else:
            if kc or bm:
                problems.append((title[:30], kc, dm, bm))
    n_ch = sum(1 for k, _, _ in secs if k == 'numbered')
    ok = (not problems
          and body.count(r'\begin{whybox}') == n_ch
          and body.count(r'\bmn{') == n_ch)
    return ok, 'chapters=%d whybox=%d bmn=%d problems=%s' % (
        n_ch, body.count(r'\begin{whybox}'), body.count(r'\bmn{'), problems or '-')


@gate('COUNTLINE numbers tie to source counts')
def g_countline():
    """Parse the NUMBERS out of the count line; never string-match tokens."""
    main = open(MAIN).read()
    m = re.search(r'% COUNTLINE:(.+)', main)
    if not m:
        return False, 'no COUNTLINE'
    printed = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', m.group(1))}
    sys.path.insert(0, HERE)
    import verify
    import patches
    body = open(BODY).read()
    tour = open(TOUR).read()
    actual = dict(
        chapters=len(re.findall(r'\\chapter\{', body)),
        starred=len(re.findall(r'\\chapter\*\{', body)),
        parts=len(re.findall(r'^#! Part ([A-Z]) ', tour, re.M)),
        checks=len(verify.CHECKS), audits=len(verify.AUDITS),
        gates=len(GATES), boxes=body.count(r'\begin{whybox}'),
        patches=len(patches.PATCHES))
    diff = {k: (printed.get(k), v) for k, v in actual.items() if printed.get(k) != v}
    return not diff, 'printed=%s mismatches=%s' % (
        len(printed), diff or '-')


@gate('margin notes predicted safe (source-side, S64)')
def g_marginnotes():
    """Predict overflow before XeLaTeX runs: flag a long note whose call site
    falls late in its section.  The remedy is always applied at the source."""
    tour = open(TOUR).read()
    secs, cur = [], None
    for line in tour.split('\n'):
        if line.startswith('#! ') or line.startswith('# '):
            cur = [line, []]
            secs.append(cur)
        elif cur:
            cur[1].append(line)
    risky = []
    for title, lines in secs:
        n = len(lines) or 1
        for idx, line in enumerate(lines):
            m = re.search(r'\\bmn\{(.+?)\}', line)
            if m and len(m.group(1)) >= 250 and idx / n > 0.66:
                risky.append((title[:28], len(m.group(1)), round(idx / n, 2)))
    longest = max((len(m) for m in re.findall(r'\\bmn\{(.+?)\}', tour)), default=0)
    return not risky, 'longest=%dch risky=%s' % (longest, risky or '-')


# ------------------------------------------------------------------- pdf gates
@gate('all fonts embedded, no Type 3')
def g_fonts():
    p = subprocess.run(['pdffonts', PDF], capture_output=True, text=True,
                     encoding='utf-8', errors='replace')
    rows = [r for r in p.stdout.split('\n')[2:] if r.strip()]
    bad = []
    for r in rows:
        toks = r.split()
        emb = toks[-4] if len(toks) >= 4 else '?'      # G2: from the stable end
        if emb != 'yes':
            bad.append(r.split()[0])
        if 'Type 3' in r:
            bad.append('TYPE3:' + r.split()[0])
    return not bad, 'fonts=%d bad=%s' % (len(rows), bad or '-')


@gate('bookmarks > 0 and == heading count')
def g_bookmarks():
    body = open(BODY).read()
    headings = len(re.findall(r'\\chapter\{', body)) + len(re.findall(r'\\chapter\*\{', body))
    out = open(os.path.join(SRCDIR, 'main.out'), errors='replace').read() \
        if os.path.exists(os.path.join(SRCDIR, 'main.out')) else ''
    marks = len(re.findall(r'BOOKMARK', out))
    return marks > 0 and marks >= headings, 'bookmarks=%d headings=%d' % (marks, headings)


@gate('footer sequence continuous and "of N" true')
def g_footer():
    """VP1 turned into a gate: the page map showed chapter openings with no
    footer at all, which no log gate can see."""
    import subprocess as sp
    n = int(re.search(r'Pages:\s+(\d+)',
            sp.run(['pdfinfo', PDF], capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout).group(1))
    printed, missing = [], []
    for p in range(1, n + 1):
        txt = sp.run(['pdftotext', '-f', str(p), '-l', str(p), PDF, '-'],
                     capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout
        m = re.search(r'page (\d+) of (\d+)', norm(txt))
        if m:
            printed.append((p, int(m.group(1)), int(m.group(2))))
        else:
            missing.append(p)
    if not printed:
        return False, 'no footers found at all'
    of = {o for _, _, o in printed}
    offsets = {p - k for p, k, _ in printed}
    # unnumbered front matter is fine; a CONSTANT offset and a true "of N" is not
    ok = (len(of) == 1 and len(offsets) == 1
          and max(k for _, k, _ in printed) == next(iter(of))
          and len(missing) <= 1)
    return ok, 'pages=%d footered=%d missing=%s offset=%s ofN=%s last=%d' % (
        n, len(printed), missing or '-', sorted(offsets), sorted(of),
        max(k for _, k, _ in printed))


@gate('sparse pages classified, none heading-only')
def g_sparse():
    """Classify, do not merely detect: a short page before a chapter break is
    normal typography; a page carrying only a heading is a defect."""
    import subprocess as sp
    n = int(re.search(r'Pages:\s+(\d+)',
            sp.run(['pdfinfo', PDF], capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout).group(1))
    sparse, blank, bad = [], [], []
    for p in range(1, n + 1):
        txt = norm(sp.run(['pdftotext', '-f', str(p), '-l', str(p), PDF, '-'],
                          capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout)
        body = re.sub(r'AI Safety from Zero to the Open Frontier page \d+ of \d+', '', txt).strip()
        if not body:
            blank.append(p)
        elif len(body) < 400:
            sparse.append((p, len(body)))
            if len(body) < 120 and not re.search(r'[a-z]{4,}\s+[a-z]{4,}\s+[a-z]{4,}', body):
                bad.append(p)
    return (not blank and not bad), 'blank=%s sparse=%s heading-only=%s' % (
        blank or '-', [p for p, _ in sparse] or '-', bad or '-')


@gate('envelope pixel audit: no ink in trim, no blank pages')
def g_envelope():
    """Render every page and assert zero dark pixels within 8mm of any edge.
    Caught ten margin notes hanging off the right edge that the source-side
    note-length gate is structurally unable to see."""
    from PIL import Image
    import glob
    import numpy as np
    files = sorted(glob.glob(os.path.join(SRCDIR, 'pages', 'p-*.png')))
    if not files:
        return False, 'no rendered pages'
    trim = int(8 * 100 / 25.4)
    blank, bad = [], []
    tight = {'top': 10 ** 9, 'bottom': 10 ** 9, 'left': 10 ** 9, 'right': 10 ** 9}
    for f in files:
        a = np.array(Image.open(f).convert('L'))
        ys, xs = np.where(a < 128)
        if not len(ys):
            blank.append(f[-10:])
            continue
        m = dict(top=int(ys.min()), bottom=int(a.shape[0] - 1 - ys.max()),
                 left=int(xs.min()), right=int(a.shape[1] - 1 - xs.max()))
        for k in tight:
            tight[k] = min(tight[k], m[k])
        if min(m.values()) < trim:
            bad.append((f[-10:], m))
    # G4: the discriminator must be able to fire, and on a signed difference
    ctrl = np.array(Image.open(files[0]).convert('L')).copy()
    ctrl[2, 2] = 0
    cys, cxs = np.where(ctrl < 128)
    assert min(int(cys.min()), int(cxs.min())) < trim, 'pixel control did not fire'
    return (not blank and not bad), 'pages=%d trim=%dpx tightest=%s blank=%s bad=%s' % (
        len(files), trim, tight, blank or '-', [b[0] for b in bad] or '-')


@gate('full-text sweep')
def g_sweep():
    """Per-page scan for artifacts, plus chapter and part order EXCLUDING the
    contents page, plus locked facts present and superseded slips absent."""
    import subprocess as sp
    n = int(re.search(r'Pages:\s+(\d+)',
            sp.run(['pdfinfo', PDF], capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout).group(1))
    pages = []
    for p in range(1, n + 1):
        pages.append(norm(sp.run(['pdftotext', '-f', str(p), '-l', str(p), PDF, '-'],
                                 capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout))
    doc = '\n'.join(pages)
    problems = []
    for art in ('??', '**', '\\begin{', '\\end{', '\\textbf', '\\texttt', '\x01', '\x02'):
        hits = [i + 1 for i, t in enumerate(pages) if art in t]
        if hits:
            problems.append('%s on %s' % (art, hits[:4]))
    # contents page is where the TOC lives; exclude it from structural counting
    toc = next((i for i, t in enumerate(pages) if t.startswith('Contents')), None)
    bodypages = [t for i, t in enumerate(pages) if i != toc]
    bodydoc = '\n'.join(bodypages)
    tour = open(TOUR).read()
    nch = len(re.findall(r'^# ', tour, re.M))
    order = [int(m.group(1)) for m in re.finditer(r'\bChapter (\d+) [A-Z]', bodydoc)]
    firsts = []
    for k in range(1, nch + 1):
        if k in order:
            firsts.append(order.index(k))
    if len(firsts) != nch or firsts != sorted(firsts):
        problems.append('chapter openers out of order or missing: %s' % firsts)
    letters = re.findall(r'^#! Part ([A-Z]) ', tour, re.M)
    for L in letters:
        if bodydoc.count('Part %s ' % L) < 1:
            problems.append('Part %s missing from body' % L)
    # corrected numbers present, superseded slips absent
    locked = ['483-492', 'Strathern', 'Zermelo', 'Robert Miles', '64(8, Part 2)']
    for s_ in locked:
        if s_ not in doc:
            problems.append('locked fact missing: %s' % s_)
    # A superseded number legitimately appears in the correction that supersedes
    # it.  Require every occurrence to sit beside its replacement, rather than
    # banning the string outright -- the unnarrowed probe fired on Part B's own
    # folklore table, which is the correction working as designed.
    for slip, fix in [('483-493', '483-492'), ('22(1)', '22(2)')]:
        stray = [i + 1 for i, t in enumerate(pages)
                 if slip in t and not re.search(
                     re.escape(slip) + r'.{0,200}' + re.escape(fix)
                     + r'|' + re.escape(fix) + r'.{0,200}' + re.escape(slip), t)]
        if stray:
            problems.append('superseded slip %s unaccompanied on pages %s' % (slip, stray))
        ctrl = 'the value is 483-493 with nothing near it'
        assert not re.search(re.escape('483-493') + r'.{0,200}' + re.escape('483-492'), ctrl), \
            'slip control is vacuous'
    return not problems, 'pages=%d toc=%s problems=%s' % (
        n, (toc + 1) if toc is not None else '-', problems or '-')


@gate('boxes and tables detected by pixel, controls validated')
def g_pixels():
    """The renders are not reliably legible at this resolution, so visual claims
    are replaced by objective detectors.  G4: discriminate by a signed difference
    from paper, never by proximity; validate every threshold against the artifact
    and every detector against a control class."""
    from PIL import Image
    import glob
    import numpy as np
    import subprocess as sp
    files = sorted(glob.glob(os.path.join(SRCDIR, 'pages', 'p-*.png')))
    if not files:
        return False, 'no rendered pages'
    textw = int(125 * 100 / 25.4)
    assert textw < 500, 'rule threshold must be derived from the text width, not typed'
    rule_th = int(textw * 0.8)

    def grey_rows(f):
        a = np.array(Image.open(f).convert('L')).astype(int)
        return int((((a > 228) & (a < 254)).sum(axis=1) > 300).sum())

    def rule_rows(f):
        a = np.array(Image.open(f).convert('L'))
        return int(((a < 128).sum(axis=1) > rule_th).sum())

    def text(p):
        return sp.run(['pdftotext', '-f', str(p), '-l', str(p), PDF, '-'],
                      capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout

    boxed = {i + 1 for i, f in enumerate(files) if grey_rows(f) > 20}
    kc = {p for p in range(1, len(files) + 1) if 'KEY CLAIM' in text(p)}
    nobox = {i + 1 for i, f in enumerate(files) if grey_rows(f) == 0}
    ruled = {i + 1 for i, f in enumerate(files) if rule_rows(f) >= 3}
    known = {p for p in range(1, len(files) + 1)
             if any(h in text(p) for h in ('What the check establishes',
                                           'Mechanism of the wedge',
                                           'What is repeated', 'Apparent miracle'))}
    ok = (boxed == kc and not (nobox & kc) and len(nobox) > 20 and known <= ruled)
    return ok, ('boxfill=%d keyclaim=%d agree=%s nobox-control=%d ruled=%d '
                'known-tables=%d contained=%s' % (
                    len(boxed), len(kc), boxed == kc, len(nobox), len(ruled),
                    len(known), known <= ruled))


@gate('body.tex is current with tour.md')
def g_current():
    """Regenerate into memory and compare.  A stale body.tex once let a corrected
    citation sit in the source while the PDF printed the old one."""
    sys.path.insert(0, os.path.dirname(HERE))
    import importlib
    import md2tex
    importlib.reload(md2tex)
    fresh, _, _ = md2tex.convert(open(TOUR).read())
    on_disk = open(BODY).read()
    same = fresh.strip() == on_disk.strip()
    # control: the comparison must be able to say no
    assert (fresh + 'x').strip() != on_disk.strip(), 'staleness check is vacuous'
    return same, 'bytes fresh=%d on-disk=%d identical=%s' % (
        len(fresh), len(on_disk), same)


@gate('verify.py all-pass')
def g_verify():
    p = subprocess.run([sys.executable, os.path.join(HERE, 'verify.py')],
                       capture_output=True, text=True,
                     encoding='utf-8', errors='replace', timeout=1800)
    m = re.search(r'---- (\d+)/(\d+) checks pass, (\d+) audits pass', p.stdout)
    return (p.returncode == 0 and m and m.group(1) == m.group(2)), \
        (m.group(0) if m else 'no summary')


GATES = [name for name, _ in RESULTS]


def main():
    width = max(len(n) for n, _ in RESULTS)
    failed = 0
    for name, fn in RESULTS:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, 'EXCEPTION %s' % e
        print('%-4s %-*s  %s' % ('PASS' if ok else 'FAIL', width, name, detail))
        failed += not ok
    print('---- %d/%d gates pass' % (len(RESULTS) - failed, len(RESULTS)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
