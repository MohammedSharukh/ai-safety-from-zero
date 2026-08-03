#!/usr/bin/env python3
"""build.py -- derive the counts, write main.tex, run XeLaTeX.

The count line is DERIVED COMPLETELY at write time.  Partial derivation is the
trap: deriving parts while hard-coding "10 chapters" prints a false count the
moment a unit is added.  Every number below comes from an artifact, and gates.py
parses the numbers back out of the COUNTLINE and ties them to source counts.
"""

import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRCDIR = os.path.join(HERE, 'src')
CHECKDIR = os.path.join(HERE, 'checks')


def derive():
    body = open(os.path.join(SRCDIR, 'body.tex')).read()
    tour = open(os.path.join(SRCDIR, 'tour.md')).read()
    sys.path.insert(0, CHECKDIR)
    import verify
    import gates as gatemod
    n = {}
    n['chapters'] = len(re.findall(r'\\chapter\{', body))
    n['starred'] = len(re.findall(r'\\chapter\*\{', body))
    n['parts'] = len(re.findall(r'^#! Part ([A-Z]) ', tour, re.M))
    n['checks'] = len(verify.CHECKS)
    n['audits'] = len(verify.AUDITS)
    n['gates'] = len(gatemod.GATES)
    n['boxes'] = body.count(r'\begin{whybox}')
    n['patches'] = len(__import__('patches').PATCHES)
    return n


TITLE = r"""%% COUNTLINE: chapters=%(chapters)d starred=%(starred)d parts=%(parts)d checks=%(checks)d audits=%(audits)d gates=%(gates)d boxes=%(boxes)d patches=%(patches)d
\begin{titlepage}
\centering
\vspace*{4cm}
{\Huge\bfseries AI Safety\par}
\vspace{6mm}
{\LARGE from Zero to the Open Frontier\par}
\vspace{18mm}
{\large a problem-driven tour, computed on one small object\par}
\vspace{16mm}
{\large Mohammed Sharukh A. (NoNTr1v1aL)\par}
\vspace{2mm}
{\small written in collaboration with Claude (Anthropic); see \emph{How this was written}\par}
\vfill
{\normalsize %(chapters)d chapters $\cdot$ %(starred)d starred sections $\cdot$ %(parts)d parts\par}
{\normalsize %(checks)d checks $\cdot$ %(audits)d standing audits $\cdot$ %(gates)d gates $\cdot$ %(patches)d idempotent patches\par}
\vspace{10mm}
{\small Every number in this document has a receipt in Part A.\par}
\vspace*{2cm}
\end{titlepage}
"""

PREAMBLE = r"""\documentclass[11pt,oneside,a4paper]{book}
\usepackage[a4paper,left=25mm,textwidth=125mm,marginparsep=7mm,marginparwidth=42mm,%
  top=30mm,bottom=30mm]{geometry}
%% 25 + 125 + 7 + 42 = 199mm of 210mm, leaving an 11mm right margin.  Centring the
%% text block instead left the note column hanging 6.5mm off the page edge, which
%% the source-side note-length gate cannot see and the envelope audit caught.
\usepackage{fontspec}
\setmainfont{Latin Modern Roman}
\setsansfont{Latin Modern Sans}
\setmonofont{Latin Modern Mono}
\usepackage{amsmath,amssymb}   % NOT unicode-math
\usepackage[most]{tcolorbox}   % L2: no dvipsnames anywhere near this
\usepackage{marginnote}        % L3: never \marginpar
\usepackage{xurl}              % L4
\usepackage{tabularx,booktabs,adjustbox}
\usepackage{lastpage,fancyhdr}
\usepackage[hidelinks]{hyperref}

\newtcolorbox{whybox}[1]{breakable,colback=black!3,colframe=black!55,
  fonttitle=\bfseries\small,title={#1},boxrule=0.5pt,left=3mm,right=3mm}
\newtcolorbox{whyboxnt}{breakable,colback=black!2,colframe=black!30,
  boxrule=0.4pt,left=3mm,right=3mm}

\newcommand{\bmn}[1]{\marginnote{\footnotesize\raggedright #1}}
\newcommand{\frontmattersetup}{\relax}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\footnotesize AI Safety from Zero to the Open Frontier
  \quad page \thepage\ of \pageref{LastPage}}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\footnotesize AI Safety from Zero to the Open Frontier
  \quad page \thepage\ of \pageref{LastPage}}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0.2pt}}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0.2pt}

\raggedbottom
\emergencystretch=2em
\setlength{\parskip}{0.4em}
\setlength{\parindent}{0pt}
\sloppy

\begin{document}
"""


def write_main(n):
    out = PREAMBLE + (TITLE % n) + "\n{\\setlength{\\parskip}{0pt}\\tableofcontents}\n\\clearpage\n\n" \
        + "\\input{body}\n\n\\end{document}\n"
    path = os.path.join(SRCDIR, 'main.tex')
    open(path, 'w').write(out)
    return path


def run_latex(passes=3):
    log = ''
    for k in range(passes):
        p = subprocess.run(['xelatex', '-interaction=nonstopmode', 'main.tex'],
                           cwd=SRCDIR, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=900)
        log = p.stdout
    return log


def main():
    # body.tex is generated from tour.md.  build.py did NOT regenerate it, so a
    # source change could silently fail to reach the PDF -- which is exactly what
    # happened once, and was caught only by a content gate on the rendered text.
    rc = subprocess.run([sys.executable, os.path.join(HERE, 'md2tex.py')],
                        cwd=HERE, capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    print(rc.stdout.strip() or rc.stderr.strip())
    if rc.returncode != 0:
        return 1
    n = derive()
    print('derived counts:', ' '.join('%s=%s' % kv for kv in sorted(n.items())))
    write_main(n)
    run_latex()
    pdf = os.path.join(SRCDIR, 'main.pdf')
    if not os.path.exists(pdf):
        print('BUILD FAILED: no main.pdf')
        return 1
    # The two pixel gates read src/pages/p-*.png at 100 dpi (gates.py's
    # trim constant is 8*100/25.4).  Nothing used to produce them, so
    # g_envelope and g_pixels were unreachable from any clone.
    pagedir = os.path.join(SRCDIR, 'pages')
    os.makedirs(pagedir, exist_ok=True)
    for stale in glob.glob(os.path.join(pagedir, 'p-*.png')):
        os.remove(stale)
    rr = subprocess.run(['pdftoppm', '-png', '-r', '100', pdf,
                         os.path.join(pagedir, 'p')],
                        capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    if rr.returncode != 0:
        print('WARNING: pdftoppm failed; the two pixel gates cannot run')
    else:
        print('rendered %d page rasters at 100 dpi'
              % len(glob.glob(os.path.join(pagedir, 'p-*.png'))))
    pages = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    m = re.search(r'Pages:\s+(\d+)', pages.stdout)
    print('main.pdf built: %d bytes, %s pages' % (os.path.getsize(pdf),
                                                  m.group(1) if m else '?'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
