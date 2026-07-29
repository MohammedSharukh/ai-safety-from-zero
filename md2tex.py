#!/usr/bin/env python3
"""md2tex.py -- tour.md to body.tex.

Standing trap ledger, each item earned by a defect on some previous run:
  C1 absorb lazy continuations: lists, tables, quotes AND plain prose paragraphs
  C2 adjustbox is horizontal -- wrap with \\par
  C3 protect $...$ and gate it ASCII-only
  C4 code spans holding URLs become \\url{}
  C5 \\noindent before every \\begin{tabularx}
  L3 marginnote, never \\marginpar (the source emits \\bmn via TEX passthrough)
  L5 tables with >= 5 columns get \\scriptsize and tabcolsep 3pt
  M2 \\lvert G\\rvert in table cells
  T1 tabularx cannot break across pages, so CHUNK TABLES HERE, header repeated

Output gates run BEFORE any LaTeX does: leaked markup, sentinel bytes or a
single non-ASCII byte in body.tex is a hard failure.
"""

import re
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'tour.md')
OUT = os.path.join(HERE, 'body.tex')

MATH = '\x01MATH%d\x01'
RAW = '\x02RAW%d\x02'
ROWS_PER_CHUNK = 9           # T1: budget so a chunk also fits under a heading


def protect(text, store_math, store_raw):
    """C3 + passthrough protection, done before any escaping."""
    def _raw(m):
        body = m.group(1).strip()
        # The original defect: an ASCII arrow inside a passthrough contained the
        # comment terminator, so the match stopped early and left \begin{verbatim}
        # open, swallowing the rest of the document into monospace.  Checking the
        # captured body for "-->" cannot catch that -- the capture is already
        # truncated.  Check BALANCE instead, which is what actually broke.
        opens = re.findall(r'\\begin\{([a-zA-Z*]+)\}', body)
        closes = re.findall(r'\\end\{([a-zA-Z*]+)\}', body)
        assert sorted(opens) == sorted(closes), (
            'unbalanced environment in TEX passthrough: opened %s closed %s in %r'
            % (opens, closes, body[:70]))
        store_raw.append(body)
        return RAW % (len(store_raw) - 1)
    text = re.sub(r'<!--TEX:(.*?)-->', _raw, text, flags=re.S)

    def _math(m):
        body = m.group(0)
        assert all(ord(c) < 128 for c in body), 'non-ASCII inside math: %r' % body
        store_math.append(body)
        return MATH % (len(store_math) - 1)
    text = re.sub(r'\$[^$\n]*\$', _math, text)
    return text


def escape(text):
    """LaTeX specials in plain prose.  Math and passthroughs are already hidden."""
    for a, b in (('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'),
                 ('#', r'\#'), ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
                 ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}'),
                 ('$', r'\$')):
        text = text.replace(a, b)
    return text


def inline(text):
    """Bold, italic, code spans.  C4: a code span holding a URL becomes \\url{}."""
    def _code(m):
        s = m.group(1)
        if s.startswith('http') or '://' in s:
            return r'\url{%s}' % s
        return r'\texttt{%s}' % s
    text = re.sub(r'`([^`\n]+)`', _code, text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text, flags=re.S)
    text = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\*)', r'\\emph{\1}', text)
    return text


def restore(text, store_math, store_raw):
    for i, m in enumerate(store_math):
        text = text.replace(MATH % i, m)
    for i, r in enumerate(store_raw):
        text = text.replace(RAW % i, r)
    return text


def table_block(rows):
    """T1: chunk, repeat the header, and size by column count (L5)."""
    header, body = rows[0], rows[2:]
    ncol = len(header)
    # Derive which columns may stay natural-width: a column whose every cell is
    # short is 'l', everything else wraps.  Typing a colspec is what produced a
    # 6174pt overfull box on the first build.
    widths = []
    for c in range(ncol):
        widths.append(max([len(header[c])] + [len(r[c]) for r in body if len(r) > c]))
    colspec = ''.join('l' if w <= 8 else 'X' for w in widths)
    if 'X' not in colspec:
        colspec = ''.join('X' if i == widths.index(max(widths)) else 'l'
                          for i in range(ncol))
    small = ncol >= 5
    out = []
    for start in range(0, len(body), ROWS_PER_CHUNK):
        chunk = body[start:start + ROWS_PER_CHUNK]
        if small:
            out.append(r'{\scriptsize\setlength{\tabcolsep}{3pt}')
        out.append(r'\noindent')                                   # C5
        out.append(r'\begin{tabularx}{\textwidth}{%s}' % colspec)
        out.append(r'\toprule')
        out.append(' & '.join(header) + r' \\')
        out.append(r'\midrule')
        for r in chunk:
            cells = (r + [''] * ncol)[:ncol]
            out.append(' & '.join(cells) + r' \\')
        out.append(r'\bottomrule')
        out.append(r'\end{tabularx}')
        if small:
            out.append('}')
        out.append(r'\par\medskip')                                # C2
    return out


def convert(src):
    store_math, store_raw = [], []
    src = protect(src, store_math, store_raw)
    src = src.replace('<!--COUNT:chapter-->', '').replace('<!--COUNT:part-->', '')

    lines = src.split('\n')
    out, i = [], 0
    n_chapters = n_starred = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if not s:
            out.append('')
            i += 1
            continue

        if s.startswith('#! '):
            title = inline(escape(s[3:]))
            out.append(r'\chapter*{%s}' % title)
            out.append(r'\addcontentsline{toc}{chapter}{%s}' % title)
            out.append(r'\markboth{%s}{%s}' % (title, title))
            n_starred += 1
            i += 1
            continue
        if s.startswith('# '):
            title = inline(escape(s[2:]))
            out.append(r'\chapter{%s}' % title)
            n_chapters += 1
            i += 1
            continue
        if s.startswith('## '):
            out.append(r'\section*{%s}' % inline(escape(s[3:])))
            i += 1
            continue

        if s.startswith(RAW[0]):                                   # passthrough alone
            out.append(s)
            i += 1
            continue

        if s.startswith('|'):                                      # table
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append([inline(escape(c)) for c in cells])
                i += 1
            if len(rows) >= 2:
                out.extend(table_block(rows))
            continue

        if s.startswith('> '):                                     # blockquote -> box
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip())
                i += 1
            joined = '\n'.join(buf)
            m = re.match(r'\*\*(KEY CLAIM|AUDIT VERDICT)\s*\((.+?)\)\.\*\*\s*(.*)', joined, re.S)
            if m:
                title = inline(escape('%s (%s)' % (m.group(1), m.group(2))))
                out.append(r'\begin{whybox}{%s}' % title)
                out.append(inline(escape(m.group(3).strip())))
                out.append(r'\end{whybox}')
            else:
                out.append(r'\begin{whyboxnt}')
                out.append(inline(escape(joined)))
                out.append(r'\end{whyboxnt}')
            continue

        if re.match(r'^[-*] ', s) or re.match(r'^\d+\. ', s):      # list
            ordered = bool(re.match(r'^\d+\. ', s))
            env = 'enumerate' if ordered else 'itemize'
            out.append(r'\begin{%s}' % env)
            while i < len(lines):
                t = lines[i].strip()
                if re.match(r'^[-*] ', t) or re.match(r'^\d+\. ', t):
                    item = re.sub(r'^([-*]|\d+\.)\s+', '', t)
                    j = i + 1                                       # C1: lazy continuation
                    while (j < len(lines) and lines[j].strip()
                           and not re.match(r'^([-*] |\d+\. |#|\||>)', lines[j].strip())):
                        item += ' ' + lines[j].strip()
                        j += 1
                    out.append(r'\item ' + inline(escape(item)))
                    i = j
                elif not t:
                    break
                else:
                    break
            out.append(r'\end{%s}' % env)
            continue

        para = [s]                                                  # C1 for prose
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r'^(#|\||>|[-*] |\d+\. )', lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(inline(escape(' '.join(para))))
        out.append('')

    body = restore('\n'.join(out), store_math, store_raw)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body, n_chapters, n_starred


def gates(body):
    """Hard fail BEFORE XeLaTeX ever runs."""
    fails = []
    non_ascii = [(i + 1, l) for i, l in enumerate(body.split('\n'))
                 if any(ord(c) > 127 for c in l)]
    if non_ascii:
        fails.append('non-ASCII in body.tex at lines %s' % [n for n, _ in non_ascii[:5]])
    if '**' in body:
        fails.append('leaked bold markup: %d occurrences' % body.count('**'))
    if '`' in body:
        fails.append('leaked backtick: %d occurrences' % body.count('`'))
    for sent in ('\x01', '\x02'):
        if sent in body:
            fails.append('sentinel byte %r survived restore' % sent)
    if re.search(r'\\end\{item(ize)?\}[^\n]*[a-z]', body):
        fails.append('mid-sentence \\end{item...}')
    if r'\marginpar' in body:
        fails.append('L3: \\marginpar used instead of marginnote')
    return fails


def main():
    src = open(SRC).read()
    body, n_ch, n_st = convert(src)
    fails = gates(body)
    if fails:
        for f in fails:
            print('GATE FAIL:', f)
        return 1
    open(OUT, 'w').write(body)
    print('body.tex written: %d bytes, %d chapters, %d starred, all output gates pass'
          % (len(body), n_ch, n_st))
    return 0


if __name__ == '__main__':
    sys.exit(main())
