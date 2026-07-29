#!/usr/bin/env python3
"""Mutation self-test.  DATA mutations only -- corrupting the object under
test.  Weakening an assertion is a GATE mutation, proves nothing, and is not
scored here (M1).  Every mutant runs under a timeout (M2) and its outcome is
classified as ASSERT / CRASH / TIMEOUT / SURVIVED (M3)."""

import subprocess
import sys
import tempfile
import os

SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify.py')).read()

MUTANTS = [
    ("R_DEMO terminal reward bot: 2 -> 1",
     "R_DEMO = {'A': F(3), 'B': F(0), 'bot': F(2)}",
     "R_DEMO = {'A': F(3), 'B': F(0), 'bot': F(1)}"),
    ("discount GAMMA_HALF: 1/2 -> 1/3",
     "GAMMA_HALF = F(1, 2)",
     "GAMMA_HALF = F(1, 3)"),
    ("wall direction (1,1,-2) -> (1,1,-3)",
     "dirs = [(1, 1, -2), (-2, 1, 1), (1, -2, 1)]",
     "dirs = [(1, 1, -3), (-2, 1, 1), (1, -2, 1)]"),
    ("MDP depth of the off-branch: 1 -> 2",
     "    return 1 if pi[0] == 'off' else 2",
     "    return 2 if pi[0] == 'off' else 2"),
    ("negative-control scaling -1 -> +1 (neuters the K4 control)",
     "        r2 = {t: F(-1) * r[t] for t in TERMINALS}",
     "        r2 = {t: F(1) * r[t] for t in TERMINALS}"),
    ("rank counter loses a terminal: permutations(T) -> permutations(T[:-1])",
     "    for p in permutations(T):",
     "    for p in permutations(T[:-1]):"),
    ("swap transposition bot<->t0 becomes identity",
     "        a[idx['bot']], a[idx['t0']] = a[idx['t0']], a[idx['bot']]",
     "        a[idx['bot']], a[idx['t0']] = a[idx['bot']], a[idx['t0']]"),
    ("DEPTHS_FLAT off-branch 1 -> 3 (breaks depth equalisation)",
     "DEPTHS_FLAT = {'off': 1, 'on': 1}",
     "DEPTHS_FLAT = {'off': 3, 'on': 1}"),
    ("shaping sign: gamma*phi(next) - phi(cur) -> + phi(cur)",
     "        f = gamma * phi.get(sp, F(0)) - phi.get(s, F(0))",
     "        f = gamma * phi.get(sp, F(0)) + phi.get(s, F(0))"),
    ("wedge table: flood true value -60 -> +60 (removes the decoupling)",
     "WEDGE_TABLE = [(F(j), F(j)) for j in range(49)] + [(F(-60), F(60))]",
     "WEDGE_TABLE = [(F(j), F(j)) for j in range(49)] + [(F(60), F(60))]"),
    ("best-of-n rank formula: j^n - (j-1)^n -> j^n",
     "        p = F(rank ** n - (rank - 1) ** n, k ** n)",
     "        p = F(rank ** n, k ** n)"),
    ("cone test: >= becomes > (breaks closure at ties)",
     "    return all(r[winner] >= r[t] for t in TERMINALS)",
     "    return all(r[winner] > r[t] for t in TERMINALS)"),
    ("Luce exponent: w**beta -> w*beta (breaks the confound identity)",
     "    num = {t: w[t] ** beta for t in TERMINALS}",
     "    num = {t: w[t] * beta for t in TERMINALS}"),
    ("proportionality test drops its second cross-product",
     "    return a[0] * b[1] == a[1] * b[0] and a[0] * b[2] == a[2] * b[0]",
     "    return a[0] * b[1] == a[1] * b[0]"),
    ("H's rule inverted: presses when U > 0",
     "        h_presses = u < 0                 # H is rational and knows U",
     "        h_presses = u > 0                 # H is rational and knows U"),
    ("Sarsa fixed point ignores the interruption",
     "    sarsa = {'l': (1 - q) * rA + q * rZ, 'r': rA}",
     "    sarsa = {'l': rA, 'r': rA}"),
    ("deference threshold uses min instead of max of the two tails",
     "        closed = max(up, -dn) / absmass",
     "        closed = min(up, -dn) / absmass"),
    ("test configuration stops decorrelating (TEST_GOOD -> TRAIN_GOOD)",
     "TEST_GOOD, TEST_BAD = (1, 0, 0), (0, 1, 1)      # feature 1 still true, 2 and 3 flip",
     "TEST_GOOD, TEST_BAD = (1, 1, 1), (0, 0, 0)      # feature 1 still true, 2 and 3 flip"),
    ("preference becomes non-strict (ties count as correct)",
     "    return dot(w, good) > dot(w, bad)",
     "    return dot(w, good) >= dot(w, bad)"),
    ("Ford connectivity checks only singletons, not both split sizes",
     "    for r in (1, 2):",
     "    for r in (1,):"),
    ("BT probability inverted: v_i/(v_i+v_j) -> v_j/(v_i+v_j)",
     "            L *= (v[i] / (v[i] + v[j])) ** c",
     "            L *= (v[j] / (v[i] + v[j])) ** c"),
    ("DPO: drop the reference division from one side of the ratio",
     "        ratio_j = pi[j] / ref[j]",
     "        ratio_j = pi[j]"),
    ("judge comparison inverted at the leaf",
     "    return 'honest' if tree[target] < claim else 'dishonest'",
     "    return 'honest' if tree[target] > claim else 'dishonest'"),
    ("unverifiable leaves silently ignored",
     "    if target in unverifiable:\n        return 'draw'",
     "    if False:\n        return 'draw'"),
    ("PGR denominator uses the floor instead of the gap",
     "        return (w2s - floor) / (ceiling - floor), floor",
     "        return (w2s - floor) / ceiling, floor"),
    ("frame projection uses the wrong divisor (3 -> 2)",
     "        m = sum(v) / 3",
     "        m = sum(v) / 2"),
    ("ReLU decode dropped: negative interference now counts",
     "        per = F(1, 4) * (2 * p * p * (1 - p)) + p ** 3",
     "        per = F(1, 4) * (2 * p * p) + p ** 3"),
    ("frame vector 3 duplicated onto vector 2 (kills the collision structure)",
     "        out.append(tuple(c - m for c in v))",
     "        out.append(tuple(c - m for c in v) if v[2] == 0 else (F(0), F(1), F(-1)))"),
    ("attack score distribution flattened (monitor loses all lift)",
     "ATTACK = [F(1, 32), F(3, 32), F(1, 8), F(1, 4), F(1, 2)]",
     "ATTACK = [F(1, 2), F(1, 4), F(1, 8), F(3, 32), F(1, 32)]"),
    ("correlated-failure model drops the shared-outcome term",
     "        fail5 = rho * (1 - m) + (1 - rho) * (1 - m) ** 5",
     "        fail5 = (1 - rho) * (1 - m) ** 5"),
    ("trigger configuration made identical to a training configuration",
     "    trigger = ((0, 1, 1), (1, 0, 0))          # the reversed test configuration",
     "    trigger = ((1, 1, 1), (0, 0, 0))          # the reversed test configuration"),
    ("count audit: box opener loosened back to the bare phrase",
     "    opener = '> **KEY CLAIM ('",
     "    opener = 'KEY CLAIM'"),
    ("count audit: heading splitter stops distinguishing starred from numbered",
     "        elif line.startswith('# '):",
     "        elif line.startswith('#'):"),
    ("timeline clause (a): a row transposed out of order",
     '    (1957, None, "Ford Jr, existence condition for the paired-comparison MLE", "P"),',
     '    (1857, None, "Ford Jr, existence condition for the paired-comparison MLE", "P"),'),
    ("timeline clause (b): an era band left interleaving",
     '    (2000, 2014, "Pre-institutional modern era", False),',
     '    (2000, 2015, "Pre-institutional modern era", False),'),
    ("timeline clause (c): a life span running backwards",
     '("Turing", 1912, 1954)',
     '("Turing", 1954, 1912)'),
    ("timeline clause (d): written after published",
     '    (1989, 1985, "Goldwasser, Micali and Rackoff, journal version", "P"),',
     '    (1989, 1995, "Goldwasser, Micali and Rackoff, journal version", "P"),'),
    ("conversion 1: realisability drops the equal-branch constraint",
     "        if extra[('m', 't0')] != extra[('m', 't1')]:",
     "        if extra[('m', 't0')] != extra[('m', 't0')]:"),
    ("conversion 2: weight pool loses closure under the confound orbit",
     "    pool = [F(1), F(2), F(3), F(4), F(6), F(12)]",
     "    pool = [F(1), F(2), F(3), F(4), F(6), F(11)]"),
    ("conversion 4: step ratio degenerates to 1 (no move is ever tried)",
     "    RATIO = F(3, 2)",
     "    RATIO = F(1, 1)"),
]


def classify(old, new):
    """M1: only DATA mutations are evidence.  A change to an assertion is a GATE
    mutation -- it will pass regardless and proves nothing.  Detect it rather than
    relying on the author to remember, since this is the most-repeated error there is."""
    o, n = old.strip(), new.strip()
    if o.startswith('assert') or n.startswith('assert'):
        return 'gate'
    return 'data'


HERE = os.path.dirname(os.path.abspath(__file__))


def run(text):
    # Write the mutant NEXT TO the real artifacts: a mutant that cannot find
    # tour.md crashes instead of failing an assertion, and M3 says a crash is
    # weaker evidence than a named assertion failure.
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, dir=HERE) as fh:
        fh.write(text)
        path = fh.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    finally:
        # mutants are written beside the real artifacts so they can find tour.md;
        # a kill between run and unlink therefore litters the working directory,
        # which the Phase 5 inventory caught.  Clean up unconditionally.
        try:
            os.unlink(path)
        except OSError:
            pass
    if p.returncode == 0:
        return "SURVIVED", ""
    err = p.stderr.strip().splitlines()
    tail = err[-1] if err else ""
    kind = "ASSERT" if "AssertionError" in p.stderr else "CRASH"
    return kind, tail[:110]


def main():
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    mutants = [m for m in MUTANTS if not only or any(o.lower() in m[0].lower() for o in only)]
    print("baseline:", run(SRC)[0], "(expect SURVIVED)")
    gates = [(n, o, w) for n, o, w in mutants if classify(o, w) == 'gate']
    assert not gates, ("GATE mutations are not evidence (M1); remove or relabel: "
                       + ", ".join(g[0] for g in gates))
    survived = []
    for name, old, new in mutants:
        assert classify(old, new) == 'data', name
        assert SRC.count(old) == 1, ("anchor not unique: " + name, SRC.count(old))
        kind, tail = run(SRC.replace(old, new))
        print("%-9s %-52s %s" % (kind, name, tail))
        if kind == "SURVIVED":
            survived.append(name)
    print("---- %d/%d data mutants killed" % (len(mutants) - len(survived), len(mutants)))
    if survived:
        print("SURVIVORS (gate is blind here):", survived)
    return 1 if survived else 0


if __name__ == '__main__':
    sys.exit(main())
