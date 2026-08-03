# AI Safety from Zero to the Open Frontier

**A problem-driven tour of AI safety, grounded in landmark original papers, in which
every number is computed on one five-state MDP and carries a receipt.**

*Mohammed Sharukh A. (NoNTr1v1aL)*

[**Read the book (PDF, 85 pages)**](./AI-Safety-from-Zero.pdf)

---

10 chapters · 6 parts · 59 numbered checks · 4 standing audits · 40 of 40 data
mutants killed · every printed number traceable to the code that produced it.

## What this is

Most introductions to AI safety are either a reading list or a set of intuitions.
This one picks a single small object — `KW`, a five-state deterministic MDP that was
asked for tea — and computes everything on it in exact rational arithmetic. Ten
chapters, ten different mechanisms by which what we measure and what we want come
apart:

| Ch | What we measure | What we want | Mechanism |
|---|---|---|---|
| 1 | the reward as written | the purpose | two of three dimensions are gauge |
| 2 | optimal value | tolerance for shutdown | more doors, not more desire |
| 3 | proxy return | true return | selection moves mass onto the tail |
| 4 | behaviour | the reward behind it | the cone's lineality |
| 5 | deference | corrigibility | it is EVPI, and vanishes with certainty |
| 6 | training performance | the learned objective | training pins one dimension of three |
| 7 | preference agreement | the latent score | consistent data has no interior optimum |
| 8 | the judge's verdict | the truth | one unverifiable leaf |
| 9 | a feature direction | the represented feature | silence and saturation are one vector |
| 10 | protocol safety | actual safety | depth is worth its independence |

None of the ten is a mistake anyone made. Each is a fact about the size of a set, the
rank of a map, or the lineality of a cone — which is why none can be fixed by being
more careful.

## What it does not claim

That the wedge is unavoidable. Nine of the ten mechanisms have a stated condition
under which they vanish. The claim is narrower and worse: **each condition is a thing
you would have to know you needed.**

The tour verifies its claims on anchors that between them have no learning, no
continuity, no time, and one agent. "Over the fence" names twelve areas it does not
cover — governance, fairness and near-term harms, multi-agent systems, formal
verification, agent foundations, moral status, misuse, brain-like approaches, scaling
laws, learning dynamics, continuous spaces, and non-stationarity — and marks three of
those as unplanned, meaning no research pass covered them at all.

What is on this side of the fence is exact. What that exactness is evidence *about* is
never claimed to be frontier models.

## Part B: what the field repeats, and what the sources say

The section most likely to be useful on its own. Received wisdom checked against
primary sources, including:

- Goodhart's famous sentence is **Strathern 1997**, not Goodhart 1975.
- Wiener does not name Goethe anywhere in the 1960 *Science* article.
- "Corrigibility" was named by **Robert Miles**, who is not an author on the 2015 paper.
- Q-learning is safely interruptible; **Sarsa is not**, without modification.
- Saltzer & Schroeder's eight design principles do **not** include defence in depth.
- *AI safety via debate* and *Risks from learned optimization* are arXiv-only; neither
  was peer-reviewed.

Every fact carries one of three provenance flags — `primary-verified`,
`verified-secondary`, `memory-flagged` — and they are never removed.

## Reproducing the checks

`verify.py` and `mutate.py` need no dependencies: Python 3 standard
library only. (`gates.py` additionally needs `numpy`, `Pillow` and
poppler -- see below.) Exact rational arithmetic and
exhaustive enumeration throughout; no result depends on a floating-point tolerance.

```bash
python checks/verify.py
```

Expected last line:

```
---- 59/59 checks pass, 4 audits pass
```

Each check prints the receipt text that appears in Part A, so any number in the book
can be traced to the line of output that produced it.

To reproduce the mutation testing — the suite deliberately corrupts its own input data
and confirms every corruption is caught:

```bash
python checks/mutate.py
```

Expected: `---- 40/40 data mutants killed`. `mutate.py` refuses to run if a mutant
edits an assertion rather than data, because weakening an assertion passes regardless
and proves nothing. That detector has fired on the author.

### The render gates need poppler

```bash
python checks/gates.py
```

Six of the 22 gates read the rendered PDF to check fonts, bookmarks,
footer continuity, margin ink and box detection. They require
`poppler-utils` (`pdfinfo`, `pdftotext`, `pdffonts`, `pdftoppm`), plus
`numpy` and `Pillow`, on
your `PATH`. **Without it those eleven fail with a file-not-found error rather than
skipping** — a missing dependency, not a defect in the document. The source-side gates
and the full check suite run without it. `gates.py` itself needs
poppler and a built PDF: run `python build.py` first, which also
renders `src/pages/`.

## How this was written

**This book was written by Mohammed Sharukh A. in collaboration with Claude
(Anthropic).** That is disclosed on the title page and in a section of its own,
because the book's method is provenance discipline and a document that flags every
citation while concealing its own authorship would fail its own standard.

I set the constraints, chose the anchor, directed the research passes and made the
editorial calls about what could and could not be claimed. Claude drafted prose, wrote
the verification suite and executed the passes. Part E records the failures found
along the way, including one worth naming: asked to inspect a rendered page, the
author described a chapter opening that was not there. The response was not to look
harder — it was to declare the visual channel uninspectable and replace it with
detectors bound to text extracted from the page.

**This is exposition, not original research.** The theory belongs to the authors cited
in Part F. What is mine is the framing, the anchor, and the verification discipline.

## Status and corrections

First public edition. Errors are expected and corrections are welcome — please open an
issue. Part E already records ten claims that died in construction because the prose
claimed more than the computation showed; that process does not stop at publication.

Known items carried at lower confidence:

- Four citations were confirmed by a single research pass and not re-reached
  (Goodhart 1975, Strathern 1997, and two paginations).
- The direct-preference-optimisation author order printed here matches the official
  proceedings; at least one major index inverts it. If you think it is wrong, check the
  proceedings rather than the index.
- Part E's `pages, footered, envelope-clean` row is stale and under-counts; it needs a
  render-gate run with poppler installed to settle.

## Contents of this repository

| Path | What |
|---|---|
| `AI-Safety-from-Zero.pdf` | The book |
| `src/tour.md` | **The prose source.** `body.tex` is generated from this |
| `src/main.tex` | Preamble and title page (hand-authored) |
| `src/body.tex` | Build artefact — generated by `md2tex.py`, do not edit |
| `checks/verify.py` | The 59 numbered checks and 4 standing audits |
| `checks/gates.py` | 22 structural and render gates |
| `checks/mutate.py` | Mutation testing over the check data |
| `checks/receipts.py` | Asserts every Part A row is the live receipt verbatim; `--write` regenerates the table from a suite run |
| `checks/patches.py`, `checks/patches_extra.py` | Idempotent source patches |
| `md2tex.py`, `build.py` | Transpiler and build pipeline |
| `CITATION.cff` | How to cite |

Building the PDF requires XeLaTeX (the title page uses `fontspec`).

## Licence

- **Book text and figures** — [CC BY 4.0](./LICENSE-TEXT.md). Share and adapt with
  attribution.
- **Code** (`checks/`, `md2tex.py`, `build.py`) — [MIT](./LICENSE).

Quoted passages from the cited literature remain the property of their authors and
publishers.
