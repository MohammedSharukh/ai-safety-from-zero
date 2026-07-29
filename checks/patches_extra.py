"""patches_extra.py -- the last four patch records.

Split out of patches.py deliberately.  The main list had grown large enough that
appending to it by string surgery corrupted it twice; a separate module is the
honest fix.  patches.py imports EXTRA and concatenates.
"""

EXTRA = [
    dict(
        id='P-V6', mode='replace',
        anchor=(
            '**Ancestry not established.** Two research passes failed to date the earliest\n'
            'citable use of "defence in depth" in military doctrine, in nuclear safety, or in\n'
            'computer security, and failed to fix the metadata for the alignment sense of\n'
            '"model organism" or its biological original. This tour therefore names both as\n'
            'imports without dating either, which is weaker than the attribution discipline\n'
            'demands and is recorded as an open gap rather than smoothed over.'),
        marker='Ancestry, two thirds established',
        new=(
            '**Ancestry, two thirds established.** Two research passes failed to date either\n'
            'import; a third dated most of one. Defence in depth is trench doctrine of about\n'
            '1915 to 1917 and reactor-safety practice from 1958, reaching civilian reactors\n'
            'by 1965 -- but its earliest citable use in computer security specifically is\n'
            'still not fixed, and neither is the page in Anderson. The alignment sense of\n'
            'model organism is now dated to August 2023, while the biological original\n'
            'appears to have no single citable coiner. What remains open is recorded as\n'
            'open rather than smoothed over.')),

    dict(
        id='P-V7', mode='replace',
        anchor=(
            'the obfuscated-arguments\n'
            'post and that the obstruction remains open; cross-examination lifting debate to\n'
            'NEXP.'),
        marker='which is Barnes and Christiano rather than the 2018 paper',
        new=(
            'the obfuscated-arguments\n'
            'post and that the obstruction remains open; and the lift of debate to NEXP by\n'
            'cross-examination, which is Barnes and Christiano rather than the 2018 paper, a\n'
            'distinction a final verification round flagged as a risk and this tour now\n'
            'states explicitly.')),

    dict(
        id='P-V8', mode='replace',
        anchor=(
            'memory-flagged after two passes: the Erhan technical report number, the earliest\n'
            'citable use of "defence in depth" in any of its three domains, the metadata for\n'
            "model organisms of misalignment, Luce's choice axiom as stated in the original,\n"
            "the DPO derivation's assumptions, and a clean primary citation for\n"
            'Bradley-Terry shift-invariance, which this tour computes rather than cites.'),
        marker='A third pass cleared four of them outright',
        new=(
            'memory-flagged after two passes. A third pass cleared four of them outright --\n'
            "the Erhan technical report number, Luce's publisher and choice axiom, the DPO\n"
            "derivation's support assumption, and a citation for Bradley-Terry\n"
            'shift-invariance -- and cleared most of a fifth, dating defence in depth in\n'
            'military and nuclear practice while leaving its computer-security debut open.\n'
            'What survives three passes is small and specific: where defence in depth\n'
            'appears in Anderson, its earliest citable use in computer security, and who\n'
            'coined model organism in biology, which may have no single citable originator.')),

    dict(
        id='P-V10', mode='replace',
        anchor=(
            'Running total: **one false negative, three false positives, one false\n'
            'observation** -- and every visual claim in this document is bound to a phrase\n'
            'extracted from the page it describes.'),
        marker='Running total after the final proofread',
        new=(
            '**The final proofread added two more probe failures, both mine.** A contents\n'
            'check normalised the entry titles but not the pages it compared them against,\n'
            'and reported ten mismatches where there are none -- apostrophes, commas and\n'
            'dashes. A column detector looked for continuous vertical whitespace and\n'
            'concluded that a five-column table had one column, because wrapped cells leave\n'
            'no continuous gutter. Both were replaced: the first by normalising both sides\n'
            'identically and running a deliberately wrong pairing as a control, the second\n'
            'by reading the real column specification out of the generated LaTeX and\n'
            'confirming the header cells appear in the render in order.\n\n'
            'Running total after the final proofread: **two false negatives, four false\n'
            'positives, one false observation.** Not one of the seven was a defect in the\n'
            'document. Every one was a defect in the instrument pointed at it -- and every\n'
            'visual claim in this document is bound to a phrase extracted from the page it\n'
            'describes.')),

    dict(
        id='P-W1', mode='replace',
        anchor=(
            'memory-flagged still: where defence in depth appears in Anderson, its earliest\n'
            'citable use in computer security specifically, and who coined model organism in\n'
            'biology, which appears to have no single citable originator. computed-here:\n'
            'receipts 50-53.'),
        marker='defended in depth, with the American spelling',
        new=(
            'verified-secondary, cleared by a fourth pass: Anderson writes **defended in\n'
            'depth, with the American spelling**, in the Nuclear Command and Control chapter\n'
            'of all three editions -- chapter 11 section 5 page 237 in 2001, chapter 13\n'
            'section 5 page 425 in 2008, chapter 15 section 5 page 540 in 2020 -- describing\n'
            'how the nuclear enterprise layers armed guards, zero-notice inspections, tamper\n'
            'resistance and dual control. He uses the phrase descriptively and does not\n'
            'theorise it. And the term enters computing far later than the tour implies:\n'
            'the earliest firmly datable computer-security document is the NSA-sponsored\n'
            'Network Security Framework Release 1.0 of 22 May 1998, with the branded\n'
            'four-part strategy formalised in Information Assurance Technical Framework\n'
            'Release 2.0 of 31 August 1999. computed-here: receipts 50-53.')),

    dict(
        id='P-W2', mode='replace', supersedes='P-V6',
        anchor=(
            '**Ancestry, two thirds established.** Two research passes failed to date either\n'
            'import; a third dated most of one. Defence in depth is trench doctrine of about\n'
            '1915 to 1917 and reactor-safety practice from 1958, reaching civilian reactors by\n'
            '1965 -- but its earliest citable use in computer security specifically is still\n'
            'not fixed, and neither is the page in Anderson. The alignment sense of model\n'
            'organism is now dated to August 2023, while the biological original appears to\n'
            'have no single citable coiner. What remains open is recorded as open.'),
        marker='Ancestry, established, and later than this chapter assumed',
        new=(
            '**Ancestry, established, and later than this chapter assumed.** Four passes\n'
            'settled both imports. Defence in depth is trench doctrine of about 1915 to\n'
            '1917 and reactor-safety practice from 1958, reaching civilian reactors by 1965\n'
            '-- and it reaches *computing* only in 1998, in the NSA-sponsored Network\n'
            'Security Framework, with the branded strategy formalised in 1999. That is\n'
            'later than this chapter implied by calling it an import security engineering\n'
            'had long had: it is demonstrably absent from the eight design principles of\n'
            'Saltzer and Schroeder in 1975, and the widely repeated attribution to a 1995\n'
            'NIST handbook is an error for a 2001 one. Model organism, in biology, has no\n'
            'single coiner at all -- the historians who studied the question find a\n'
            'retrospective category that gained currency in the 1980s and was formalised by\n'
            'an NIH designation in 1990. Its alignment sense dates to August 2023. Both\n'
            'imports are now dated; what is newly interesting is that one of them is\n'
            'younger than half this tour.')),

    dict(
        id='P-W3', mode='replace',
        anchor=(
            'memory-flagged after two passes. A third pass cleared four of them outright --\n'
            "the Erhan technical report number, Luce's publisher and choice axiom, the DPO\n"
            "derivation's support assumption, and a citation for Bradley-Terry\n"
            'shift-invariance -- and cleared most of a fifth, dating defence in depth in\n'
            'military and nuclear practice while leaving its computer-security debut open.\n'
            'What survives three passes is small and specific: where defence in depth\n'
            'appears in Anderson, its earliest citable use in computer security, and who\n'
            'coined model organism in biology, which may have no single citable originator.'),
        marker='the memory-flagged list is now empty',
        new=(
            'memory-flagged after two passes. A third pass cleared four of them outright --\n'
            "the Erhan technical report number, Luce's publisher and choice axiom, the DPO\n"
            "derivation's support assumption, and a citation for Bradley-Terry\n"
            'shift-invariance. A fourth pass, given the three survivors and nothing else to\n'
            'do, closed all three: the page in Anderson, the debut of defence in depth in\n'
            'computing, and the coinage of model organism, the last of which is settled as a\n'
            'well-evidenced negative -- there is no coiner, and the historians who looked\n'
            'say so. **So the memory-flagged list is now empty.** That is worth stating\n'
            'precisely, because it does not mean the tour is free of error. It means every\n'
            'fact in it has been looked at by someone, and the ones that could not be\n'
            'settled were removed rather than dressed up.')),

    dict(
        id='P-W4', mode='replace', supersedes='P-W3',
        anchor=(
            'say so. **So the memory-flagged list is now empty.** That is worth stating\n'
            'precisely, because it does not mean the tour is free of error. It means every\n'
            'fact in it has been looked at by someone, and the ones that could not be\n'
            'settled were removed rather than dressed up.'),
        marker='one flag survives that was never on that list',
        new=(
            'say so. **So that list is now empty** -- and a census run to confirm it found\n'
            'the sentence overclaiming, which is worth reporting rather than quietly\n'
            'fixing. **Exactly one flag survives that was never on that list:** the earliest\n'
            'clear statement of the evolution analogy, in Chapter 6, which no pass has\n'
            'dated. Two further items are recorded not as flags but as persistent\n'
            'negatives, which is a different thing: no pass found a pre-2019 use of inner\n'
            'alignment, and no coiner exists for model organism in biology. So the honest\n'
            'statement is not that the tour is free of error. It is that every fact in it\n'
            'has been looked at, the one that could not be settled is named, and the ones\n'
            'that came back empty are labelled empty rather than dressed as answers.')),

    dict(
        id='P-V9', mode='after',
        anchor=(
            'Running total: **one false negative, three false positives, one false\n'
            'observation** -- and every visual claim in this document is bound to a phrase\n'
            'extracted from the page it describes.'),
        marker='## The final external round',
        new=(
            '\n\n## The final external round\n\n'
            'A last verification pass was run against the finished PDF rather than against\n'
            'the source, because what shipped is what matters. It audited roughly fifty\n'
            'bibliographic assertions, fourteen folklore verdicts, forty printed life spans\n'
            'and seven event dates.\n\n'
            'It raised **two alerts, and only one was live.** The live one was a wrong issue\n'
            'number for Bostrom 2012, printed as 22(1) where the correct citation is\n'
            '22(2), pp. 71-85; it is corrected in the bibliography, and the superseded\n'
            'number now appears only inside its own correction. The second alert suspected\n'
            'that this document attributed the lift of debate to NEXP to the 2018 debate\n'
            'paper rather than to Barnes and Christiano. **It did not.** A search found zero\n'
            'sentences bundling the two, and the NEXP result was already carried as\n'
            'verified-secondary, separately from the primary-verified attribution. Patching\n'
            'would have damaged a correct passage.\n\n'
            'That is two alerts triaged, one live and one false, against five false\n'
            'positives in ten alerts on a previous run. The discipline that matters is not\n'
            'the rate; it is that no alert is acted on before the exact printed string has\n'
            'been read.\n\n'
            'The round also confirmed the two citations most likely to be flagged wrongly by\n'
            'a re-checker. The direct-preference-optimisation author order printed here\n'
            'matches the official proceedings, while one major index inverts it. And the\n'
            'warning that Candes, Romberg and Tao at 52(2) is a different paper from Candes\n'
            'and Tao at 52(12) is itself correct. Both would have been corrected into error\n'
            'by a pass that trusted secondary indices.')),
]
