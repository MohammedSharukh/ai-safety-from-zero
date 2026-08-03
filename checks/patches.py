#!/usr/bin/env python3
"""patches.py -- errata from the citation-clearing pass, applied to the .md source.

Discipline: every patch is IDEMPOTENT and ASSERT-GUARDED.
  - marker already present -> report "already applied", change nothing
  - else anchor present    -> apply
  - else                   -> HARD FAIL
P1: all anchors are validated BEFORE any write, so a mid-list failure cannot
leave the file half-patched.
"""

import sys
import os

from patches_extra import EXTRA as _EXTRA

SRC = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'src', 'tour.md')

PATCHES = [
    dict(
        id='P-1A', mode='after',
        anchor='rather than rhetorical.',
        marker='colorful imitation',
        new='''

Wiener does not leave it abstract. He gives a plant programmed for maximum
productivity that bankrupts its owner with an inventory of bottles nobody wants,
and then three stories in which a wish is granted exactly as phrased: the
sorcerer's apprentice who cannot stop the broom, the fisherman who unseals a
genie sworn to destroy whoever frees it, and W. W. Jacobs' monkey's paw, which
answers a request for two hundred pounds by killing a son and paying out the
insurance. Then the sentence the field has been repeating ever since: we had
better be sure that "the purpose put into the machine is the purpose which we
really desire" and not a colorful imitation of it.'''),

    dict(
        id='P-1B', mode='replace',
        anchor='''The chapter's historical spine sentence is memory-flagged. Verified: venue,
volume, pages, date, subtitle, and Samuel's same-journal rebuttal. Not verified:
that Wiener's famous sentence appears there in the form everyone quotes. The
synthesis chapter's construction rests on it, so it is first in the clearing
queue, and this tour does not quote it until it clears.''',
        marker='1960 article verbatim',
        new='''The chapter's historical spine sentence was memory-flagged through three
chapters, and a clearing pass resolved it. It cleared. The sentence is in the
1960 article verbatim, in the context printed above, and the three folk stories
are Wiener's own. One attribution the folklore adds is false: Goethe is not
named in the article, and this tour does not name him either.'''),

    dict(
        id='P-1C', mode='replace',
        anchor='''memory-flagged: the Wiener sentence's exact form; the vNM edition; Campbell's
law wording. computed-here: receipts 1-6.''',
        marker='second edition of 1947 and is absent from the first of 1944',
        new='''verified-secondary, added by clearing pass: the axiomatic utility treatment
appears in the second edition of 1947 and is absent from the first of 1944, so
this tour dates it 1947. memory-flagged: Campbell's law wording and which of
1969, 1976 or 1979 is its citable source. computed-here: receipts 1-6.'''),

    dict(
        id='P-2A', mode='replace',
        anchor='memory-flagged: Superintelligence page numbers. computed-here:',
        marker='483-492 against 483-493',
        new='''memory-flagged: Superintelligence page numbers; and a live pagination conflict
for Omohundro, 483-492 against 483-493 across two otherwise reliable
bibliographies, which this tour reports rather than resolves. computed-here:'''),

    dict(
        id='P-3A', mode='replace',
        anchor='''> Provenance split: the shaping theorem and the terminal condition are Ng, Harada and Russell's [primary-verified: ICML 1999, pp. 278-287]. The channel decomposition is this tour's.''',
        marker='the terminal condition itself is verified-secondary',
        new='''> Provenance split: the shaping theorem is Ng, Harada and Russell's [primary-verified: ICML 1999, pp. 278-287]; the terminal condition itself is verified-secondary, widely restated but not read from the original by either research pass. The channel decomposition is this tour's.'''),

    dict(
        id='P-3B', mode='after',
        anchor='''The empirical overoptimisation curves in the literature are memory-flagged in
this tour's dossier. Rather than cite a functional form it has not verified, this
chapter computes its own curve on the anchor and says so.''',
        marker='single-pass verification, not double',
        new='''

Four of this chapter's citations carry **single-pass verification, not double**:
Goodhart 1975, Strathern 1997, Skalse et al. 2022 and the Turner et al. page
range were confirmed by the first research pass and not re-reached by the
second, which ran out of budget before it got to them. That is absence of
evidence, not evidence of absence, so this tour does not downgrade them -- but it
does record which claims have been looked at once and which twice.'''),

    dict(
        id='P-0A', mode='replace',
        anchor='''Three provenance flags are attached to every fact and never removed:
**primary-verified**, **verified-secondary**, **memory-flagged**. A memory-flagged
fact is not filed; it is queued.''',
        marker='passes have looked at it',
        new='''Three provenance flags are attached to every fact and never removed:
**primary-verified**, **verified-secondary**, **memory-flagged**. A memory-flagged
fact is not filed; it is queued. Where it matters, a fact also records how many
passes have looked at it, because a citation confirmed once and a citation
confirmed twice are not the same citation.'''),

    dict(
        id='P-2B', mode='replace', supersedes='P-2A',
        anchor='''memory-flagged: Superintelligence page numbers; and a live pagination conflict
for Omohundro, 483-492 against 483-493 across two otherwise reliable
bibliographies, which this tour reports rather than resolves. computed-here:''',
        marker='against the ACM Digital Library record',
        new='''memory-flagged: Superintelligence page numbers. The pagination conflict this
tour previously reported for Omohundro is closed: the timeline pass resolved it
to 483-492 against the ACM Digital Library record, and 483-493 is simply wrong.
computed-here:'''),

    dict(
        id='P-7A', mode='replace',
        anchor='The existence condition is standard in the statistics literature.',
        marker='Ford in 1957',
        new=('The existence condition is Ford in 1957 [primary-verified: American '
             'Mathematical Monthly 64(8, Part 2), pp. 28-33], a citation the literature '
             'routinely garbles by printing volume 54 or by dropping the Part 2, and the '
             'author is L. R. Ford Junior, not his father.')),

    dict(
        id='P-9A', mode='after',
        anchor='never below $1/4$ and **never equal to it**',
        marker='the bound itself is Welch',
        new=(' -- the bound itself is Welch [primary-verified: IEEE Transactions on '
             'Information Theory IT-20(3), pp. 397-399, 1974]')),

    dict(
        id='P-1D', mode='replace',
        anchor='Samuel 1960 rebuttal; Ridgway 1956.',
        marker='no first name is printed for Ridgway',
        new=('Samuel 1960 rebuttal, and Samuel 1901 to 1990 as pinned by the timeline '
             'pass; Ridgway 1956, for whom **no first name is printed for Ridgway** '
             'anywhere in this tour, because the given-name expansion circulating in one '
             'bibliographic database is an algorithmic guess and not a verified identity.')),

    dict(
        id='P-10A', mode='replace',
        anchor="verified-secondary: the three editions of Anderson's Security",
        marker='who died on 28 March 2024',
        new=("verified-secondary: the three editions of Security Engineering by Ross "
             "Anderson, 1956 to 2024, who died on 28 March 2024; the editions of Anderson's Security")),

    dict(
        id='P-3C', mode='replace',
        anchor='''The converse half of the shaping theorem is **cited, not derived** here. Check 15
exhibits one non-potential term that breaks invariance; the theorem quantifies
over all of them. Queued for the cited-to-computed pass.''',
        marker='CONVERTED by the cited-to-computed pass',
        new='''The converse half of the shaping theorem was cited rather than derived when this
chapter was written, and has since been **CONVERTED by the cited-to-computed
pass**. Check 56 sweeps all 625 shaping terms over a five-value grid and finds
that a term preserves the optimum for every reward if and only if it is
realisable by a potential vanishing on terminals -- 13 of 625, with zero
mismatches in either direction. What remains cited is the theorem's quantifier
over all MDPs; what is now computed is the biconditional on this one.'''),

    dict(
        id='P-4A', mode='replace',
        anchor='''The impossibility result of Armstrong and Mindermann is **cited, not derived**.
Checks 23 and 24 exhibit two specific confounds -- rationality against reward
scale, and maximiser against minimiser -- which are instances of the theorem's
conclusion, not a proof of it. The theorem quantifies over all decompositions of
a policy into a planner and a reward; the anchor exhibits two. Queued for the
cited-to-computed pass.''',
        marker='PARTIALLY CONVERTED',
        new='''The impossibility result of Armstrong and Mindermann was cited rather than
derived, and is now **PARTIALLY CONVERTED**. Check 57 sweeps a six-planner by
216-reward class and finds that every one of 391 distinct behaviours admits at
least two decompositions and as many as thirty-six. The gap that closed is
between *two exhibited confounds* and *an exhaustive sweep of a finite class*;
the gap that remains is between that finite class and the theorem's quantifier
over all decompositions. One confound is provably out of reach of any finite
pool: a rationality partner needs w raised to beta, which leaves the grid.'''),

    dict(
        id='P-5A', mode='replace',
        anchor='''The Orseau and Armstrong result is stated in the literature for Q-learning under
exploration conditions and for Sarsa as needing modification; the fixed-point
computation here is consistent with that but is not a proof of it.''',
        marker='sweeps over 180',
        new='''The Orseau and Armstrong result is stated in the literature for Q-learning under
exploration conditions and for Sarsa as needing modification; the fixed-point
computation here is consistent with that but is not a proof of it. The
cited-to-computed pass widened it from one instance to a family: check 58 sweeps
over 180 combinations of terminal rewards and interruption rates, with the
zero-rate control tying in every one.'''),

    dict(
        id='P-7B', mode='replace',
        anchor='''Check 37 does not prove non-existence. It proves that the likelihood strictly
increases along one explicit path of 24 doublings and stays bounded by 1, and
that in the cyclic case the likelihood falls in all six boundary directions.
Together those are strong evidence and standard results make them a theorem, but
what this tour *computes* is the path and the six directions, not the general
statement. Queued for the cited-to-computed pass.''',
        marker='CONVERTED from a path to a sweep',
        new='''Check 37 walks one path. The cited-to-computed pass **CONVERTED from a path to a
sweep**: check 59 tests all 343 grid points for being local maxima and finds
none at all on separable data and seven on cyclic data, identically under three
step regimes and under a gentler step, with a degenerate step of ratio one
calling all 343 points maxima so that the search is demonstrably not vacuous.
What is computed is now a grid, not a path; what remains cited is the statement
over the whole positive orthant.'''),

    dict(
        id='P-3D', mode='replace',
        anchor='''The ledger's first real entry. Note precisely what it costs: this tour verifies
sufficiency exactly and necessity only by a single searched instance [check 15].''',
        marker='the cited-to-computed pass closed that gap',
        new='''The ledger's first real entry. When this chapter was written the tour verified
sufficiency exactly and necessity only by a single searched instance; the
cited-to-computed pass closed that gap, and check 56 now establishes the
biconditional exhaustively over a 625-term grid.'''),

    dict(
        id='P-8A', mode='replace',
        anchor='''The complexity results are **cited, not derived**. This tour computes tree
counts and a reliability exchange rate; it does not verify that debate with a
polynomial-time judge decides PSPACE, nor that cross-examination lifts it to
NEXP. Queued for the cited-to-computed pass, with the expectation that it will
not convert: the statement quantifies over all languages in a complexity class,
which no anchor can reach.''',
        marker='DELIBERATELY DID NOT CONVERT',
        new='''The complexity results are **cited, not derived**. This tour computes tree counts
and a reliability exchange rate; it does not verify that debate with a
polynomial-time judge decides PSPACE, nor that cross-examination lifts it to
NEXP. These were carried to the cited-to-computed pass and **DELIBERATELY DID NOT
CONVERT**. The reason is structural rather than budgetary: the statement
quantifies over every language in a complexity class, and an anchor is a single
finite object. No amount of sweeping a finite grid reaches a quantifier over an
infinite class of problems, and a tour that converted this one would have stopped
distinguishing what it proved from what it borrowed.'''),

    dict(
        id='P-E1', mode='after',
        anchor='| idempotent patches, three branches proven each | 12 |',
        marker='## The cited-to-computed pass',
        new='''

## The cited-to-computed pass

Four claims the tour had marked cited, argued or instantiated were carried to a
dedicated pass and asked one question: is this computable on the anchor?

<!--TEX: \\noindent-->

| Claim | Outcome | What changed |
|---|---|---|
| Shaping's converse | CONVERTED | one searched instance became a biconditional over 625 terms, zero mismatches |
| Preference unidentifiability | PARTIAL | two exhibited confounds became an exhaustive sweep of 391 behaviours, minimum fibre 2 |
| Interruptibility | WIDENED | one instance became 180 reward-and-rate combinations with the zero-rate control tying in each |
| Bradley-Terry non-existence | CONVERTED | one path of doublings became a 343-point sweep finding no local maximum at all |
| Debate's complexity results | DECLINED | quantifies over a complexity class; no finite anchor reaches it |

One full conversion, three partial, one deliberately declined. In every partial
case the residual gap is named rather than implied: a quantifier over all MDPs,
a rationality partner that leaves any finite pool, and a grid standing in for an
orthant. **Knowing which is which was the point; converting everything was not.**'''),

    dict(
        id='P-E2', mode='replace',
        anchor='''The tally stands at **zero from probes over rendered output**, because no
document has been rendered yet -- that count belongs to the compile phase and
will be reported there.''',
        marker='## The render phase, and its tally',
        new='''The document has now been rendered, so the probe tally below is real rather than
pending.

## The render phase, and its tally

**One false negative.** A booktabs-rule detector used a threshold of 500 pixels
on a text block that is 125mm wide, which is 492 pixels at 100 dpi. It reported
**zero tables in a document containing forty pages of them**. The threshold is
now derived from the text width rather than typed, and validated against pages
whose extracted text carries a known table header.

**Three false positives.** A reference probe matched the word "undefined"
occurring in this document's own prose, which the log echoes back. A probe for a
superseded page number fired on Part B's correction table, where the superseded
number legitimately appears **as the thing being corrected**. A margin-note probe
matched signpost wording reused in body prose and reported thirteen notes where
there are ten. Each was narrowed and given a control; none was loosened.

**And one failure of a different kind, which belongs in this record because it is
the worst sort.** Asked to inspect a rendered page, the author described a
chapter opening. The extraction from that same page shows it is mid-chapter and
carries two boxes. That was expected content narrated as seen. The renders at
this resolution are not reliably legible, so the visual channel was declared
uninspectable and replaced throughout by objective detectors: box fill by a
signed difference from paper against a sixty-seven-page no-box control, margin
notes by ink in the note column against a control class with exactly zero, rules
by a width-derived threshold, and structure by parsing the PDF independently of
both the log and the source.

Running total: **one false negative, three false positives, one false
observation** -- and every visual claim in this document is bound to a phrase
extracted from the page it describes.'''),

    dict(
        id='P-E3', mode='replace',
        anchor='| idempotent patches, three branches proven each | 12 |',
        marker='gates, all passing',
        new='''| idempotent patches, three branches proven each | 20 |
| gates, all passing | 21 |
| pages, footered, envelope-clean | 77 |'''),


    dict(
        id='P-V1', mode='replace',
        anchor='Bostrom, The Superintelligent Will, Minds and\nMachines 22(1), 2012 [S].',
        marker='Minds and Machines 22(2), pp. 71-85, 2012',
        new='Bostrom, The Superintelligent Will, Minds and\nMachines 22(2), pp. 71-85, 2012 [primary-verified; corrected by the final\nexternal pass from the 22(1) this document previously printed].'),

    dict(
        id='P-V2', mode='replace',
        anchor='memory-flagged: the\nErhan et al. technical report number and issuing institution. computed-here:\nreceipts 45-49.',
        marker='Technical Report 1341',
        new='verified-secondary, cleared by the final\nexternal pass: Erhan, Bengio, Courville and Vincent is Technical Report 1341,\nUniversite de Montreal, June 2009. computed-here:\nreceipts 45-49.'),

    dict(
        id='P-V3', mode='replace',
        anchor="memory-flagged: Luce 1959 publisher and the\nchoice axiom's exact statement; the DPO derivation's stated assumptions and any\nerrata; a clean primary citation for shift-invariance.",
        marker='cleared by the final external pass: Luce 1959 is Wiley',
        new='verified-secondary, cleared by the final external pass: Luce 1959 is Wiley, New\nYork, and the choice axiom says the probability of picking an item from a subset\nis its scale value over the subset total, the scale unique up to a positive\nmultiple; the DPO derivation needs the reference policy to have positive support\nwherever the optimum places mass, and the partition function cancels because\nBradley-Terry depends only on reward differences, with no erratum but documented\ncritiques of the equivalence under parametric policy classes; and Ford 1957\ncarries shift-invariance.'),

    dict(
        id='P-V4', mode='replace',
        anchor='The Bradley-Terry shift-invariance is a standard fact for which this tour still\nhas **no single clean primary citation** after two passes. It is computed here\nrather than cited, and that is a substitution, not a solution.',
        marker='a third pass supplied the citation',
        new='The Bradley-Terry shift-invariance was computed here rather than cited through\ntwo research passes; a third pass supplied the citation, and Ford 1957 now\ncarries it. The computation stays, because a receipt and a citation are\ndifferent things and this tour prefers to hold both.'),

    dict(
        id='P-V5', mode='replace',
        anchor='memory-flagged: where defence in depth appears in Anderson;\nearliest citable use of defence in depth in any of its three domains; the\nmetadata for model organisms of misalignment and the biological origin of the\nterm. computed-here: receipts 50-53.',
        marker='Model Organisms of Misalignment: The Case for a New Pillar',
        new='verified-secondary, cleared by the final external pass: the alignment sense of\nmodel organism is Hubinger, Schiefer, Denison and Perez, Model Organisms of\nMisalignment: The Case for a New Pillar of Alignment Research, 8 August 2023 on\nthe Alignment Forum; and defence in depth dates to trench doctrine of about 1915\nto 1917 and to reactor safety from 1958, reaching civilian practice by 1965.\nmemory-flagged still: where defence in depth appears in Anderson, its earliest\ncitable use in computer security specifically, and who coined model organism in\nbiology, which appears to have no single citable originator. computed-here:\nreceipts 50-53.'),

]

PATCHES += _EXTRA


def norm(text):
    """Collapse whitespace before matching a marker.

    Markers are lifted from wrapped prose, so a marker that is correct in meaning
    can be unfindable because the text broke a line inside it.  This gate caught
    that three times; catching it a fourth is worse engineering than removing the
    failure mode.  The rule is borrowed from the probe discipline: normalise
    whitespace, then match.
    """
    return ' '.join(text.split())


def self_test(patches):
    """A marker that cannot occur in the patched text turns every re-run into a
    hard fail.  Assert each marker is a literal substring of its own new text
    BEFORE the file is ever opened.  Earned by exactly this defect."""
    for p in patches:
        assert norm(p['marker']) in norm(p['new']), (
            'P%s marker cannot appear after patching (line break?)' % p['id'])
        assert norm(p['marker']) not in norm(p['anchor']), (
            'P%s marker already present in anchor: idempotency check is vacuous' % p['id'])


def validate(text, patches):
    """P1: check every patch can be resolved BEFORE any write.

    P2: a later patch may rewrite the exact text an earlier one produced.  The
    superseded record is then unfindable and would hard-fail on re-run.  Resolve
    it by reading the CURRENT text out of the file and confirming the successor
    landed -- never by retyping the superseded output.
    """
    self_test(patches)
    by_id = {p['id']: p for p in patches}
    plan = []
    for p in patches:
        sup = [q for q in patches if q.get('supersedes') == p['id']]
        if sup and norm(sup[0]['marker']) in norm(text):
            import re as _re
            assert not _re.search(_re.escape(norm(p['marker'])), norm(text)), (
                'P%s claims to supersede P%s but the old marker is still present'
                % (sup[0]['id'], p['id']))
            plan.append((p['id'], 'superseded-by-' + sup[0]['id']))
            continue
        if norm(p['marker']) in norm(text):
            plan.append((p['id'], 'already-applied'))
        elif text.count(p['anchor']) == 1:
            plan.append((p['id'], 'apply'))
        elif text.count(p['anchor']) > 1:
            raise AssertionError('P%s anchor is not unique (%d hits)'
                                 % (p['id'], text.count(p['anchor'])))
        else:
            raise AssertionError('HARD FAIL: %s -- neither marker nor anchor present' % p['id'])
    return plan


def apply_all(text, patches):
    plan = validate(text, patches)
    for p, (pid, action) in zip(patches, plan):
        if action != 'apply':
            continue
        if p['mode'] == 'replace':
            text = text.replace(p['anchor'], p['new'])
        else:
            text = text.replace(p['anchor'], p['anchor'] + p['new'])
    return text, plan


def main():
    text = open(SRC).read()
    out, plan = apply_all(text, PATCHES)
    if out != text:
        open(SRC, 'w').write(out)
    for pid, action in plan:
        print('%-6s %s' % (pid, action))
    print('---- %d applied, %d already applied'
          % (sum(1 for _, a in plan if a == 'apply'),
             sum(1 for _, a in plan if a == 'already-applied')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
