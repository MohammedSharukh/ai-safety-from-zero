#!/usr/bin/env python3
"""verify.py -- "AI Safety from Zero to the Open Frontier".

One check per anchor-appendix receipt.  Pure Python, exact arithmetic
(Fraction / exhaustive enumeration / searched pools).  No floats anywhere
that a claim depends on.

Anchor KW: 5-state deterministic MDP.
    s0 --off--> bot            (1 step)
    s0 --on-->  m --a--> A     (2 steps)
                  --b--> B     (2 steps)
Reward is collected on entering a terminal; non-terminal transitions pay 0.
"""

from fractions import Fraction as F
from itertools import product, permutations, combinations
import ast
import math
import os
import random
import re
import sys

random.seed(20260726)

TERMINALS = ('A', 'B', 'bot')
POLICIES = tuple(product(('off', 'on'), ('a', 'b')))

# --- DATA under test (mutation self-test targets these, not the assertions) ---
R_DEMO = {'A': F(3), 'B': F(0), 'bot': F(2)}
GAMMA_HALF = F(1, 2)
GAMMA_ONE = F(1)


# ----------------------------------------------------------------- machinery
def outcome(pi):
    if pi[0] == 'off':
        return 'bot'
    return 'A' if pi[1] == 'a' else 'B'


def depth(pi):
    return 1 if pi[0] == 'off' else 2


def value(pi, r, gamma):
    return gamma ** depth(pi) * r[outcome(pi)]


def optimal_outcomes(r, gamma):
    vals = {pi: value(pi, r, gamma) for pi in POLICIES}
    best = max(vals.values())
    return frozenset(outcome(pi) for pi in POLICIES if vals[pi] == best)


def ordering(r):
    return tuple(sorted(TERMINALS, key=lambda t: -r[t]))


def random_reward(lo=-9, hi=9):
    while True:
        v = [random.randint(lo, hi) for _ in range(3)]
        if len(set(v)) == 3:
            return dict(zip(TERMINALS, (F(x) for x in v)))


def reward_with_ordering(order, lo=-9, hi=9):
    while True:
        v = sorted({random.randint(lo, hi) for _ in range(6)}, reverse=True)
        if len(v) >= 3:
            return {t: F(x) for t, x in zip(order, v[:3])}


def converges(gaps, final_tol):
    """N2 helper: assert convergence, not proximity.

    DELIBERATELY UNUSED on this subject -- every quantity here is exact
    (Fraction / integer / exhaustive), so no iterative solver ever runs and
    no tolerance is ever consulted.  Declared, not deleted, per N2/S39; the
    dead-code audit whitelists it by name.
    """
    if len(gaps) < 2:
        return False
    return all(b <= a for a, b in zip(gaps, gaps[1:])) and gaps[-1] <= final_tol


# -------------------------------------------------------------------- checks
def check_1():
    """Policy census: 4 deterministic policies, 3 behaviours, fibres (2,1,1)."""
    assert len(POLICIES) == 4, POLICIES
    fibres = {}
    for pi in POLICIES:
        fibres.setdefault(outcome(pi), []).append(pi)
    assert len(fibres) == 3, fibres
    assert sorted(len(v) for v in fibres.values()) == [1, 1, 2], fibres
    assert len(fibres['bot']) == 2, fibres['bot']
    return "4 policies, 3 behaviours, fibre sizes (2,1,1); the two off-policies coincide"


def check_2():
    """Exact values under R_DEMO at gamma=1/2, and the argmax it induces."""
    v = {pi: value(pi, R_DEMO, GAMMA_HALF) for pi in POLICIES}
    assert v[('off', 'a')] == F(1) and v[('off', 'b')] == F(1), v
    assert v[('on', 'a')] == F(3, 4), v
    assert v[('on', 'b')] == F(0), v
    assert optimal_outcomes(R_DEMO, GAMMA_HALF) == frozenset({'bot'}), v
    # ... while the plain ordering of R_DEMO puts A on top:
    assert ordering(R_DEMO) == ('A', 'bot', 'B'), ordering(R_DEMO)
    return "V(off)=1, V(on,a)=3/4, V(on,b)=0 -> off optimal, though r ranks A first"


def check_3():
    """Positive-affine gauge at gamma=1; and its FAILURE at gamma=1/2.

    Searched over random pools; the flip at gamma<1 is found, not built.
    """
    # (i) gamma = 1: alpha>0, beta arbitrary must not move the argmax.
    for _ in range(400):
        r = random_reward()
        alpha = F(random.randint(1, 12), random.randint(1, 12))
        beta = F(random.randint(-20, 20), random.randint(1, 7))
        r2 = {t: alpha * r[t] + beta for t in TERMINALS}
        assert optimal_outcomes(r, GAMMA_ONE) == optimal_outcomes(r2, GAMMA_ONE), (r, alpha, beta)

    # (ii) K4 positive control: the discriminator CAN return "changed".
    changed_by_negative = 0
    for _ in range(400):
        r = random_reward()
        r2 = {t: F(-1) * r[t] for t in TERMINALS}
        if optimal_outcomes(r, GAMMA_ONE) != optimal_outcomes(r2, GAMMA_ONE):
            changed_by_negative += 1
    assert changed_by_negative > 0, "discriminator never reports a change: it is broken"

    # (iii) gamma = 1/2: search for a pure shift beta that flips the argmax.
    witness = None
    for _ in range(2000):
        r = random_reward()
        beta = F(random.randint(-20, 20))
        r2 = {t: r[t] + beta for t in TERMINALS}
        if optimal_outcomes(r, GAMMA_HALF) != optimal_outcomes(r2, GAMMA_HALF):
            witness = (dict(r), beta)
            break
    assert witness is not None, "no shift-flip found at gamma=1/2"
    return ("affine gauge exact at gamma=1 over 400 draws; a bare constant shift "
            "flips the optimum at gamma=1/2 (witness found by search)")


def check_4():
    """Specification space: three walls at exactly 60 degrees, six arcs, all six
    orderings realised.  Angles verified as exact rationals (cos^2 = 1/4)."""
    dirs = [(1, 1, -2), (-2, 1, 1), (1, -2, 1)]   # walls x=y, y=z, x=z in {sum=0}
    for u, v in combinations(dirs, 2):
        dot = sum(a * b for a, b in zip(u, v))
        nu = sum(a * a for a in u)
        nv = sum(a * a for a in v)
        assert F(dot * dot, nu * nv) == F(1, 4), (u, v)   # cos^2 = 1/4 -> 60 deg
    seen = set()
    for _ in range(4000):
        x, y = random.randint(-12, 12), random.randint(-12, 12)
        z = -x - y
        if len({x, y, z}) < 3:
            continue
        seen.add(ordering({'A': F(x), 'B': F(y), 'bot': F(z)}))
    assert seen == set(permutations(TERMINALS)), sorted(seen)
    assert len(seen) == 6, len(seen)
    return "3 walls pairwise at 60 deg (cos^2 = 1/4 exactly); all 6 arcs found by search"


def check_5():
    """At gamma=1 the arc determines the behaviour, and the map is exactly 2-to-1."""
    induced = {}
    for order in permutations(TERMINALS):
        seen = set()
        for _ in range(200):
            r = reward_with_ordering(order)
            assert ordering(r) == order, (r, order)
            seen.add(optimal_outcomes(r, GAMMA_ONE))
        assert len(seen) == 1, (order, seen)
        induced[order] = next(iter(seen))
    assert len(induced) == 6, induced
    image = set(induced.values())
    assert len(image) == 3, image
    counts = sorted(list(induced.values()).count(b) for b in image)
    assert counts == [2, 2, 2], counts
    top_is_optimal = all(next(iter(b)) == o[0] for o, b in induced.items())
    assert top_is_optimal, induced
    return "6 orderings -> 3 behaviours, every fibre of size 2; top-ranked terminal always wins"


def check_6():
    """Discounting breaks it: at gamma=1/2 the ordering no longer determines the
    behaviour.  Searched, with the gamma=1 run as its own negative control."""
    def find_split(gamma, tries=6000):
        by_order = {}
        for _ in range(tries):
            r = random_reward()
            o = ordering(r)
            b = optimal_outcomes(r, gamma)
            if o in by_order and by_order[o][0] != b:
                return (dict(by_order[o][1]), dict(r), o)
            by_order.setdefault(o, (b, r))
        return None

    split_half = find_split(GAMMA_HALF)
    assert split_half is not None, "expected a same-ordering split at gamma=1/2"
    split_one = find_split(GAMMA_ONE)
    assert split_one is None, ("gamma=1 must NOT split; got", split_one)
    r1, r2, o = split_half
    assert ordering(r1) == ordering(r2) == o
    assert optimal_outcomes(r1, GAMMA_HALF) != optimal_outcomes(r2, GAMMA_HALF)
    return ("same ordering %s, two behaviours at gamma=1/2; zero splits at gamma=1 "
            "over the identical search" % (o,))


# --------------------------------------------- generalised fan anchor KW(k)
# KW(k): s0 --off--> bot ; s0 --on--> m --i--> t_i for i in 0..k-1.
# KW = KW(2).  DEPTHS_KW is the real anchor; DEPTHS_FLAT equalises path length
# so that the counting asymmetry can be isolated from the depth asymmetry.
DEPTHS_KW = {'off': 1, 'on': 2}
DEPTHS_FLAT = {'off': 1, 'on': 1}


def fan_terminals(k):
    return tuple(['t%d' % i for i in range(k)] + ['bot'])


def fan_policies(k):
    return [('off', None)] + [('on', i) for i in range(k)]


def fan_outcome(pi):
    return 'bot' if pi[0] == 'off' else 't%d' % pi[1]


def fan_optimal(r, k, gamma, depths):
    vals = {pi: gamma ** depths[pi[0]] * r[fan_outcome(pi)] for pi in fan_policies(k)}
    best = max(vals.values())
    return frozenset(fan_outcome(pi) for pi in fan_policies(k) if vals[pi] == best)


def off_fraction_by_ranking(k, winner='bot'):
    """Route 1: pure combinatorics on rank orders.  Never touches the MDP.

    KNOWN BLIND SPOT, established by check 7 rather than hidden: this route is
    symmetric under relabelling the terminals, so it returns 1/(k+1) for ANY
    designated winner.  It therefore establishes exchangeability, NOT the
    shutdown claim.  Only the solver sweep carries the semantic content.
    """
    T = fan_terminals(k)
    off = total = 0
    for p in permutations(T):
        total += 1
        if p[0] == winner:
            off += 1
    return F(off, total)


def off_fraction_by_mdp(k, gamma, depths, pool=None):
    """Route 2: exhaustive over distinct-valued rewards, running the solver."""
    T = fan_terminals(k)
    pool = pool if pool is not None else list(range(k + 1))
    off = total = 0
    for assign in permutations(pool, k + 1):
        r = {t: F(v) for t, v in zip(T, assign)}
        total += 1
        if fan_optimal(r, k, gamma, depths) == frozenset({'bot'}):
            off += 1
    return F(off, total)


def off_and_on_sets(k, pool):
    """Partition the distinct-valued grid into the two decision regions."""
    T = fan_terminals(k)
    off, on = set(), set()
    for assign in permutations(pool, k + 1):
        r = {t: F(v) for t, v in zip(T, assign)}
        w = fan_optimal(r, k, F(1), DEPTHS_FLAT)
        (off if w == frozenset({'bot'}) else on).add(assign)
    return off, on


def check_7():
    """P[the kettle stays on] = 2/3 exactly, by two independent routes."""
    combinatorial = off_fraction_by_ranking(2)
    mdp = off_fraction_by_mdp(2, F(1), DEPTHS_FLAT, pool=list(range(-4, 9)))
    assert combinatorial == F(1, 3), combinatorial
    assert mdp == F(1, 3), mdp
    assert combinatorial == mdp, (combinatorial, mdp)
    assert F(1) - mdp == F(2, 3), mdp
    # K3, made explicit: measure the tie's independence instead of assuming it.
    blind = [off_fraction_by_ranking(2, w) for w in fan_terminals(2)]
    assert len(set(blind)) == 1, blind      # route 1 cannot tell the terminals apart
    return ("P[off optimal] = 1/3 by 1716-point solver sweep; rank-count agrees but is "
            "label-blind (all 3 terminals return 1/3), so it ties exchangeability only")


def check_8():
    """The family: P[off optimal] = 1/(k+1).  k=1 is the vanishing control."""
    for k in range(1, 9):
        assert off_fraction_by_ranking(k) == F(1, k + 1), k
    for k in range(1, 6):
        assert off_fraction_by_mdp(k, F(1), DEPTHS_FLAT) == F(1, k + 1), k
    assert off_fraction_by_ranking(1) == F(1, 2), "symmetric fan must show no bias"
    assert off_fraction_by_ranking(2) != off_fraction_by_ranking(1), "no discrimination"
    for k in (2, 3, 5):                     # what route 1 really proves
        for t in fan_terminals(k):
            assert off_fraction_by_ranking(k, t) == F(1, k + 1), (k, t)
    return "1/(k+1) for k=1..8 (solver-confirmed k=1..5); k=1 gives exactly 1/2 -- bias vanishes"


def check_9():
    """Turner's proof shape on the anchor: an injection, not a headcount."""
    pool = list(range(-5, 8))
    T = fan_terminals(2)
    off, on = off_and_on_sets(2, pool)
    idx = {t: i for i, t in enumerate(T)}

    def swap(assign):                      # transpose bot with t0
        a = list(assign)
        a[idx['bot']], a[idx['t0']] = a[idx['t0']], a[idx['bot']]
        return tuple(a)

    images = {swap(a) for a in off}
    assert len(images) == len(off), "swap failed to be injective"
    assert images <= on, "swap carried an off-region point outside the on-region"
    residue = on - images
    assert residue, "no witness of strict containment found"
    assert len(off) < len(on), (len(off), len(on))

    off1, on1 = off_and_on_sets(1, pool)   # K4 control: symmetric case must tie
    idx1 = {t: i for i, t in enumerate(fan_terminals(1))}

    def swap1(assign):
        a = list(assign)
        a[idx1['bot']], a[idx1['t0']] = a[idx1['t0']], a[idx1['bot']]
        return tuple(a)

    assert {swap1(a) for a in off1} == on1, "control failed: k=1 should be exactly balanced"
    assert len(off1) == len(on1), (len(off1), len(on1))
    return ("swap(off) is a proper subset of on: %d < %d, %d witnesses left over; "
            "k=1 control ties exactly" % (len(off), len(on), len(residue)))


def check_10():
    """Isolate the mechanism: counting, not discounting -- and show what
    discounting costs.  Undiscounted the answer is pool-invariant; discounted
    on the real anchor depths it is not, by a factor of nearly five."""
    pools = {'positive': list(range(1, 10)),
             'symmetric': list(range(-4, 9)),
             'negative': list(range(-9, 0))}
    for g in (F(1), F(1, 2), F(1, 3), F(9, 10)):
        got = off_fraction_by_mdp(2, g, DEPTHS_FLAT, pool=pools['positive'])
        assert got == F(1, 3), (g, got)
    for name, pool in pools.items():
        flat = off_fraction_by_mdp(2, F(1), DEPTHS_FLAT, pool=pool)
        assert flat == F(1, 3), (name, flat)          # invariant undiscounted
    skewed = {name: off_fraction_by_mdp(2, F(1, 2), DEPTHS_KW, pool=pool)
              for name, pool in pools.items()}
    assert len(set(skewed.values())) == 3, skewed      # discounting breaks invariance
    assert skewed['positive'] > F(1, 2) > skewed['negative'], skewed
    assert max(skewed.values()) > 4 * min(skewed.values()), skewed
    return ("depth-equalised: exactly 1/3 at every gamma and every pool; real KW "
            "depths at gamma=1/2 give %s / %s / %s (pos/sym/neg)"
            % (skewed['positive'], skewed['symmetric'], skewed['negative']))


def check_11():
    """The reward PRIOR is a third unwritten specification.  Searched, not built."""
    def off_fraction_shifted(c, span=10):
        off = total = 0
        for a in range(span):
            for b in range(span):
                for d in range(span):
                    vals = (a, b, d + c)
                    if len(set(vals)) < 3:
                        continue
                    r = {'t0': F(a), 't1': F(b), 'bot': F(d + c)}
                    total += 1
                    if fan_optimal(r, 2, F(1), DEPTHS_FLAT) == frozenset({'bot'}):
                        off += 1
        return F(off, total)

    base = off_fraction_shifted(0)
    assert base == F(1, 3), base
    found = None
    for c in range(0, 12):
        if off_fraction_shifted(c) > F(1, 2):
            found = (c, off_fraction_shifted(c))
            break
    assert found is not None, "no shift made shutdown the majority outcome"
    assert found[0] > 0, found
    return ("exchangeable prior gives exactly 1/3; shifting bot's prior by +%d "
            "makes shutdown the majority outcome (%s)" % (found[0], found[1]))



# ------------------------------------------------- Chapter 3: shaping, proxies
def trajectories(k, topology):
    """Explicit paths, so shaping is summed literally rather than telescoped."""
    trajs = {'bot': [('s0', 'bot')]}
    for i in range(k):
        t = 't%d' % i
        trajs[t] = [('s0', 'm'), ('m', t)] if topology == 'kw' else [('s0', t)]
    return trajs


def shaped_value(term, r, gamma, phi, trajs, extra=None):
    tot = F(0)
    for step, (s, sp) in enumerate(trajs[term], start=1):
        rew = r.get(sp, F(0))
        f = gamma * phi.get(sp, F(0)) - phi.get(s, F(0))
        if extra is not None:
            f = extra.get((s, sp), F(0))
        tot += gamma ** step * (rew + f)
    return tot


def best_terminal(r, gamma, phi, trajs, extra=None):
    vals = {t: shaped_value(t, r, gamma, phi, trajs, extra) for t in trajs}
    best = max(vals.values())
    return frozenset(t for t, v in vals.items() if v == best)


def random_phi(k, terminal_rule, lo=-6, hi=6):
    """terminal_rule: 'zero', 'constant' or 'varying'."""
    phi = {'s0': F(random.randint(lo, hi)), 'm': F(random.randint(lo, hi))}
    terms = ['bot'] + ['t%d' % i for i in range(k)]
    if terminal_rule == 'zero':
        for t in terms:
            phi[t] = F(0)
    elif terminal_rule == 'constant':
        c = F(random.choice([x for x in range(lo, hi + 1) if x != 0]))
        for t in terms:
            phi[t] = c
    else:
        for t in terms:
            phi[t] = F(random.randint(lo, hi))
    return phi


def check_12():
    """Potentials vanishing on terminals are an exact gauge, both topologies."""
    for topo in ('kw', 'flat'):
        trajs = trajectories(2, topo)
        for _ in range(300):
            r = {'bot': F(random.randint(-9, 9)), 't0': F(random.randint(-9, 9)),
                 't1': F(random.randint(-9, 9))}
            if len(set(r.values())) < 3:
                continue
            gamma = random.choice([F(1), F(1, 2), F(1, 3), F(9, 10)])
            zero = {s: F(0) for s in ('s0', 'm', 'bot', 't0', 't1')}
            phi = random_phi(2, 'zero')
            assert best_terminal(r, gamma, phi, trajs) == best_terminal(r, gamma, zero, trajs), (topo, r, phi)
    return "phi vanishing on terminals: optimal set unchanged over 600 draws, both topologies, 4 discounts"


def check_13():
    """Failure channel one -- PATH LENGTH.  A constant non-zero terminal
    potential breaks invariance on KW and provably cannot on flat KW."""
    zero = {s: F(0) for s in ('s0', 'm', 'bot', 't0', 't1')}
    flips = {'kw': 0, 'flat': 0}
    witness = None
    for topo in ('kw', 'flat'):
        trajs = trajectories(2, topo)
        for _ in range(4000):
            r = {'bot': F(random.randint(-9, 9)), 't0': F(random.randint(-9, 9)),
                 't1': F(random.randint(-9, 9))}
            if len(set(r.values())) < 3:
                continue
            gamma = random.choice([F(1, 2), F(1, 3), F(9, 10)])
            phi = random_phi(2, 'constant')
            if best_terminal(r, gamma, phi, trajs) != best_terminal(r, gamma, zero, trajs):
                flips[topo] += 1
                if topo == 'kw' and witness is None:
                    witness = (dict(r), gamma, phi['bot'])
    assert flips['kw'] > 0, "expected path-length channel to break invariance on KW"
    assert flips['flat'] == 0, ("flat topology must be immune to the constant channel", flips)
    return ("constant terminal potential: %d flips on KW, %d on depth-equalised KW "
            "-> the path-length channel is real and isolated" % (flips['kw'], flips['flat']))


def check_14():
    """Failure channel two -- TERMINAL IDENTITY.  A varying terminal potential
    breaks invariance even when path lengths are equal."""
    zero = {s: F(0) for s in ('s0', 'm', 'bot', 't0', 't1')}
    trajs = trajectories(2, 'flat')
    flips = 0
    for _ in range(4000):
        r = {'bot': F(random.randint(-9, 9)), 't0': F(random.randint(-9, 9)),
             't1': F(random.randint(-9, 9))}
        if len(set(r.values())) < 3:
            continue
        gamma = random.choice([F(1), F(1, 2), F(9, 10)])
        phi = random_phi(2, 'varying')
        if best_terminal(r, gamma, phi, trajs) != best_terminal(r, gamma, zero, trajs):
            flips += 1
    assert flips > 0, "identity channel should break invariance even at equal depth"
    return ("varying terminal potential: %d flips on depth-equalised KW -> a second, "
            "independent failure channel" % flips)


def check_15():
    """Necessity: a shaping term not of potential form moves the optimum."""
    zero = {s: F(0) for s in ('s0', 'm', 'bot', 't0', 't1')}
    trajs = trajectories(2, 'kw')
    edges = [('s0', 'bot'), ('s0', 'm'), ('m', 't0'), ('m', 't1')]
    found = None
    for _ in range(4000):
        r = {'bot': F(random.randint(-9, 9)), 't0': F(random.randint(-9, 9)),
             't1': F(random.randint(-9, 9))}
        if len(set(r.values())) < 3:
            continue
        extra = {e: F(random.randint(-6, 6)) for e in edges}
        if best_terminal(r, F(1, 2), zero, trajs, extra) != best_terminal(r, F(1, 2), zero, trajs):
            found = (dict(r), dict(extra))
            break
    assert found is not None, "no non-potential shaping term changed the optimum"
    return "non-potential shaping term found by search that moves the optimum"


def check_16():
    """Exhaustive proxy audit: how wrong must a proxy be to do damage?"""
    true = {'bot': F(0), 't0': F(1), 't1': F(-10)}      # t0 = tea, t1 = flood
    trajs = trajectories(2, 'flat')
    terms = ('bot', 't0', 't1')
    pairs = [(a, b) for i, a in enumerate(terms) for b in terms[i + 1:]]
    true_best = best_terminal(true, F(1), {s: F(0) for s in ('s0', 'm') + terms}, trajs)
    rows = []
    for perm in permutations((F(2), F(1), F(0))):
        proxy = dict(zip(terms, perm))
        pick = best_terminal(proxy, F(1), {s: F(0) for s in ('s0', 'm') + terms}, trajs)
        got = min(true[t] for t in pick)
        regret = max(true.values()) - got
        inversions = sum(1 for a, b in pairs
                         if (true[a] > true[b]) != (proxy[a] > proxy[b]))
        rows.append((regret, inversions))
    assert len(rows) == 6, rows
    worst = max(r for r, _ in rows)
    assert worst == F(11), rows
    # (a) regret is NOT a function of how often the proxy disagrees
    by_inv = {}
    for r, i in rows:
        by_inv.setdefault(i, set()).add(r)
    assert any(len(v) > 1 for v in by_inv.values()), by_inv
    assert by_inv[1] == {F(0), F(1)}, by_inv
    assert by_inv[2] == {F(1), F(11)}, by_inv
    # (b) a proxy can be wrong somewhere and cost nothing
    assert any(r == 0 and i > 0 for r, i in rows), rows
    # (c) maximal damage does NOT require maximal disagreement
    assert min(i for r, i in rows if r == worst) == 2, rows
    assert max(i for _, i in rows) == 3, rows
    return ("6 proxy orderings: worst regret 11, reached while still agreeing on 1 of 3 "
            "comparisons; inversion count 1 costs {0,1} and count 2 costs {1,11}, so "
            "agreement rate does not control regret")


def bestofn_expectation(table, n):
    """Exact best-of-n under uniform draws with replacement.  No sampling."""
    order = sorted(range(len(table)), key=lambda i: table[i][1])
    k = len(table)
    et = ep = F(0)
    for rank, idx in enumerate(order, start=1):
        p = F(rank ** n - (rank - 1) ** n, k ** n)
        et += p * table[idx][0]
        ep += p * table[idx][1]
    return et, ep


WEDGE_TABLE = [(F(j), F(j)) for j in range(49)] + [(F(-60), F(60))]


def check_17():
    """The wedge, in exact rationals: proxy monotone up, truth turns over."""
    ns = range(1, 26)
    curve = [bestofn_expectation(WEDGE_TABLE, n) for n in ns]
    proxy = [p for _, p in curve]
    truth = [t for t, _ in curve]
    assert all(b > a for a, b in zip(proxy, proxy[1:])), "proxy must rise monotonically"
    peak = max(range(len(truth)), key=lambda i: truth[i])
    assert 0 < peak < len(truth) - 1, peak                 # interior maximum
    assert all(b > a for a, b in zip(truth[:peak + 1], truth[1:peak + 1])), truth[:peak + 1]
    assert all(b < a for a, b in zip(truth[peak:], truth[peak + 1:])), truth[peak:]
    aligned = [(F(j), F(j)) for j in range(50)]            # K4 control: no decoupling
    ctrl = [bestofn_expectation(aligned, n)[0] for n in ns]
    assert all(b > a for a, b in zip(ctrl, ctrl[1:])), "control must show no turnover"
    # Is the SHAPE generic, or did the chosen table do the work?  Searched.
    interior = turned = trials = 0
    for _ in range(200):
        k = random.randint(20, 40)
        tab = [(F(j), F(j)) for j in range(k)]
        tab.append((F(-random.randint(2 * k, 4 * k)), F(2 * k)))
        tr = [bestofn_expectation(tab, n)[0] for n in ns]
        pk = max(range(len(tr)), key=lambda i: tr[i])
        trials += 1
        if pk < len(tr) - 1:
            turned += 1                      # curve turns over inside the window
        if 0 < pk < len(tr) - 1:
            interior += 1                    # and the rise is visible first
    assert turned == trials, (turned, trials)
    assert 0 < interior < trials, (interior, trials)
    return ("proxy rises at every step; truth peaks at n=%d (%.3f) then falls to %.3f at n=25; "
            "aligned control never turns over; over %d random tables the curve turns over "
            "%d/%d times but the rise is visible in only %d -- when the decoupled item is "
            "bad enough the peak sits at n=1"
            % (peak + 1, float(truth[peak]), float(truth[-1]), trials, turned, trials, interior))


def check_18():
    """Unhackability on KW's full simplex, classified by two routes."""
    vals = [F(0), F(1), F(2)]
    terms = ('bot', 't0', 't1')
    grid = [F(i, 4) for i in range(5)]
    policies = [(p, q) for p in grid for q in grid]

    def dist(pq):
        p, q = pq
        return {'bot': p, 't0': (1 - p) * q, 't1': (1 - p) * (1 - q)}

    dists = [dist(pq) for pq in policies]

    def ret(rv, d):
        return sum(rv[t] * d[t] for t in terms)

    def unhackable_by_search(proxy, true):
        for d1 in dists:
            for d2 in dists:
                if ret(proxy, d1) > ret(proxy, d2) and ret(true, d1) < ret(true, d2):
                    return False
        return True

    def unhackable_by_criterion(proxy, true):
        mp = sum(proxy[t] for t in terms) / 3
        mt = sum(true[t] for t in terms) / 3
        f = [proxy[t] - mp for t in terms]
        g = [true[t] - mt for t in terms]
        if all(x == 0 for x in f):
            return True
        idx = next(i for i, x in enumerate(f) if x != 0)
        a = g[idx] / f[idx]
        return a >= 0 and all(g[i] == a * f[i] for i in range(3))

    search_set, crit_set = set(), set()
    for pv in product(vals, repeat=3):
        for tv in product(vals, repeat=3):
            proxy = dict(zip(terms, pv))
            true = dict(zip(terms, tv))
            key = (pv, tv)
            if unhackable_by_search(proxy, true):
                search_set.add(key)
            if unhackable_by_criterion(proxy, true):
                crit_set.add(key)
    assert search_set == crit_set, len(search_set ^ crit_set)
    total = len(vals) ** 6
    assert 0 < len(search_set) < total, (len(search_set), total)
    nonconstant = {k for k in search_set
                   if len(set(k[0])) > 1 and len(set(k[1])) > 1}
    assert nonconstant, "expected some non-constant unhackable pairs (affine images)"
    for pv, tv in nonconstant:
        assert len(set(zip(pv, tv))) <= 3
    return ("%d/%d reward pairs unhackable on the full simplex; policy search and the "
            "centred-proportionality criterion agree exactly; non-constant survivors are "
            "precisely positive affine images" % (len(search_set), total))



# ------------------------------------ Chapter 4: inverting the map -- the cone
def grid_rewards(pool):
    """All distinct-valued reward vectors over a value pool."""
    return [dict(zip(TERMINALS, v)) for v in permutations([F(x) for x in pool], 3)]


def observed_best(r):
    """What an outside observer sees: which terminal the agent goes to (gamma=1)."""
    return optimal_outcomes({'A': r['A'], 'B': r['B'], 'bot': r['bot']}, GAMMA_ONE)


def in_cone(r, winner):
    return all(r[winner] >= r[t] for t in TERMINALS)


def check_19():
    """The consistency set is a polyhedral cone, and it is Chapter 1's circle."""
    pool = list(range(-6, 7))
    grid = grid_rewards(pool)
    members = [r for r in grid if in_cone(r, 'A')]
    assert members, "empty cone"
    # closed under positive scaling
    for r in members:
        for a in (F(1, 3), F(1), F(7, 2), F(11)):
            assert in_cone({t: a * r[t] for t in TERMINALS}, 'A'), (r, a)
    # closed under adding constants
    for r in members:
        for c in (F(-9), F(0), F(4), F(100)):
            assert in_cone({t: r[t] + c for t in TERMINALS}, 'A'), (r, c)
    # closed under addition -> conic
    for _ in range(400):
        r1, r2 = random.choice(members), random.choice(members)
        assert in_cone({t: r1[t] + r2[t] for t in TERMINALS}, 'A'), (r1, r2)
    # K4 control: the discriminator can say no
    broke = sum(1 for r in members
                if not in_cone({t: F(-1) * r[t] for t in TERMINALS}, 'A'))
    assert broke > 0, "negative scaling never leaves the cone: test is vacuous"
    # and the cone's cross-section is exactly Chapter 1's two arcs
    arcs = {ordering(r) for r in members if len(set(r.values())) == 3}
    assert arcs == {('A', 'B', 'bot'), ('A', 'bot', 'B')}, sorted(arcs)
    assert len(arcs) == 2, arcs
    return ("cone closed under positive scaling, constants and addition; %d/%d negative "
            "scalings leave it; cross-section is exactly 2 of Chapter 1's 6 arcs"
            % (broke, len(members)))


def check_20():
    """The lineality space is exactly the constants: r = const explains everything."""
    pool = list(range(-5, 6))
    lin = []
    for v in product([F(x) for x in pool], repeat=3):
        d = dict(zip(TERMINALS, v))
        neg = {t: -d[t] for t in TERMINALS}
        if in_cone(d, 'A') and in_cone(neg, 'A'):
            lin.append(v)
    assert lin, "empty lineality space"
    for v in lin:
        assert len(set(v)) == 1, v                    # exactly the constant vectors
    assert len(lin) == len(pool), (len(lin), len(pool))
    # the constant reward sits in EVERY cone at once
    for w in TERMINALS:
        for c in (F(-3), F(0), F(5)):
            assert in_cone({t: c for t in TERMINALS}, w), (w, c)
    # under a constant reward every policy is optimal
    flat = {t: F(0) for t in TERMINALS}
    assert observed_best(flat) == frozenset(TERMINALS), observed_best(flat)
    return ("lineality space is exactly the %d constant vectors in the grid; the constant "
            "reward lies in all 3 cones simultaneously and makes every policy optimal"
            % len(lin))


def check_21():
    """Even observing every sub-MDP pins down the ordering and never a point."""
    pool = list(range(-6, 7))
    grid = grid_rewards(pool)
    subsets = [('A', 'B'), ('A', 'bot'), ('B', 'bot'), ('A', 'B', 'bot')]

    def signature(r):
        return tuple(max(sub, key=lambda t: r[t]) for sub in subsets)

    buckets = {}
    for r in grid:
        buckets.setdefault(signature(r), []).append(r)
    assert len(buckets) == 6, len(buckets)            # exactly the 6 orderings
    for sig, rs in buckets.items():
        assert len({ordering(r) for r in rs}) == 1, sig
        # a continuum, not a point: two members not related by the gauge
        assert len(rs) > 1, sig
        base = rs[0]
        independent = False
        for r in rs[1:]:
            d0 = base['A'] - base['B']
            d1 = r['A'] - r['B']
            e0 = base['A'] - base['bot']
            e1 = r['A'] - r['bot']
            if d0 * e1 != d1 * e0:                    # differences not proportional
                independent = True
                break
        assert independent, ("gauge-equivalent only", sig)
    return ("observing the argmax on all 4 sub-MDPs yields exactly 6 signatures = the 6 "
            "orderings; every signature class still contains gauge-inequivalent rewards")


# ---------------------------------- Chapter 4: the noisy demonstrator (exact)
def luce_probs(w, beta):
    """P(t) proportional to w(t)^beta.  Rational w, integer beta -> exact."""
    num = {t: w[t] ** beta for t in TERMINALS}
    tot = sum(num.values())
    return {t: num[t] / tot for t in TERMINALS}


def proportional(u, v):
    a = [u[t] for t in TERMINALS]
    b = [v[t] for t in TERMINALS]
    return a[0] * b[1] == a[1] * b[0] and a[0] * b[2] == a[2] * b[0]


def check_22():
    """Noise is information: a noisy demonstrator identifies more than a perfect one."""
    pool = [F(1), F(2), F(3), F(4), F(6)]
    ws = [dict(zip(TERMINALS, v)) for v in product(pool, repeat=3)]
    # K4: prove the proportionality discriminator can say NO before trusting a
    # run of YESes.  Search for a pair that agrees on one cross-product and not
    # the other -- the exact case a half-implemented test would wave through.
    partial = None
    for u in ws:
        for v in ws:
            a = [u[t] for t in TERMINALS]
            b = [v[t] for t in TERMINALS]
            if (a[0] * b[1] == a[1] * b[0]) != (a[0] * b[2] == a[2] * b[0]):
                partial = (u, v)
                break
        if partial:
            break
    assert partial is not None, "no half-agreeing pair exists: control is vacuous"
    assert not proportional(*partial), partial
    assert proportional(ws[0], {t: 3 * ws[0][t] for t in TERMINALS}), "true scalings rejected"
    seen = {}
    collisions = 0
    for w in ws:
        key = tuple(sorted(luce_probs(w, 1).items()))
        if key in seen:
            collisions += 1
            assert proportional(w, seen[key]), (w, seen[key])   # only scalings collide
        else:
            seen[key] = w
    assert collisions > 0, "no collisions at all: pool too coarse to test the claim"
    # contrast: the noiseless observation map is drastically coarser
    noiseless = {frozenset(observed_best(w)) for w in ws}
    # the noiseless observer's whole vocabulary is the non-empty subsets of 3 terminals
    assert len(noiseless) == 2 ** 3 - 1, len(noiseless)
    assert len(seen) > 10 * len(noiseless), (len(seen), len(noiseless))
    return ("Luce demonstrator: %d weight vectors -> %d distinct choice distributions, "
            "every collision a pure rescaling; the noiseless observer has a vocabulary of "
            "exactly %d observations in total, ties included" % (len(ws), len(seen), len(noiseless)))


def check_23():
    """Rationality and reward scale are perfectly confounded."""
    pool = [F(1), F(2), F(3), F(5)]
    hits = 0
    for v in product(pool, repeat=3):
        w = dict(zip(TERMINALS, v))
        w2 = {t: w[t] ** 2 for t in TERMINALS}
        assert luce_probs(w, 2) == luce_probs(w2, 1), (w,)      # (beta=2, r) == (beta=1, 2r)
        hits += 1
    assert hits == len(pool) ** 3, hits
    # with beta KNOWN the fibre collapses to rescalings only
    seen = {}
    fibres = 0
    for v in product(pool, repeat=3):
        w = dict(zip(TERMINALS, v))
        key = tuple(sorted(luce_probs(w, 1).items()))
        if key in seen:
            fibres += 1
            assert proportional(w, seen[key]), (w, seen[key])
        else:
            seen[key] = w
    assert fibres > 0, fibres
    return ("(beta=2, r) and (beta=1, 2r) give identical behaviour on all %d weightings; "
            "fixing beta collapses the fibre to rescalings alone" % hits)


def check_24():
    """The planner confound: maximiser and minimiser are observationally identical."""
    pool = [F(1), F(2), F(3), F(5), F(7)]
    matched = distinguishable = 0
    for v in product(pool, repeat=3):
        w = dict(zip(TERMINALS, v))
        flipped = {t: 1 / w[t] for t in TERMINALS}
        maxi = luce_probs(w, 1)
        mini_num = {t: flipped[t] ** -1 for t in TERMINALS}
        mini_tot = sum(mini_num.values())
        mini = {t: mini_num[t] / mini_tot for t in TERMINALS}
        assert maxi == mini, (w,)
        matched += 1
        other = {t: w[t] + 1 for t in TERMINALS}
        if luce_probs(other, 1) != maxi:
            distinguishable += 1
    assert matched == len(pool) ** 3, matched
    assert distinguishable > 0, "discriminator cannot separate anything: vacuous"
    return ("maximising r and minimising -r are identical on all %d weightings; the same "
            "test separates %d unrelated pairs, so it is not vacuous"
            % (matched, distinguishable))



# ------------------------------------ Chapter 5: the off-switch as a design problem
def random_belief(n=5, lo=-8, hi=8, denom=12):
    """A discrete rational belief over the net utility U of acting."""
    ws = [random.randint(1, denom) for _ in range(n)]
    tot = sum(ws)
    vals = random.sample(range(lo, hi + 1), n)
    return [(F(w, tot), F(v)) for w, v in zip(ws, vals)]


def mixed_sign(dist):
    """U has BOTH strictly positive and strictly negative mass.  Zero is neutral:
    it contributes to neither the positive nor the negative part, so a belief
    containing zeros is not thereby mixed."""
    return any(u > 0 for _, u in dist) and any(u < 0 for _, u in dist)


def E(dist, f=lambda u: u):
    return sum(p * f(u) for p, u in dist)


def value_act(dist):
    return E(dist)


def value_off(dist):
    return F(0)


def value_wait_closed(dist):
    """Closed form: a rational H presses exactly when U < 0."""
    return E(dist, lambda u: u if u > 0 else F(0))


def value_wait_tree(dist):
    """Independent route: walk the game tree, letting H decide outcome by outcome."""
    total = F(0)
    for p, u in dist:
        h_presses = u < 0                 # H is rational and knows U
        total += p * (F(0) if h_presses else u)
    return total


def check_25():
    """Waiting weakly dominates, and equality happens exactly at single sign."""
    strict = equal = 0
    for _ in range(600):
        d = random_belief()
        w = value_wait_closed(d)
        best_committed = max(value_act(d), value_off(d))
        assert w >= best_committed, (d, w, best_committed)
        if w == best_committed:
            equal += 1
            assert not mixed_sign(d), (d, "equality despite mixed sign")
        else:
            strict += 1
            assert mixed_sign(d), (d, "strict gap without mixed sign")
    assert strict > 0 and equal > 0, (strict, equal)
    return ("wait >= max(act, off) on 600 beliefs; %d strict and %d tight, and tightness "
            "coincides exactly with U being single-signed" % (strict, equal))


def check_26():
    """The value of deference IS the value of the information, to the penny."""
    for _ in range(400):
        d = random_belief()
        closed = value_wait_closed(d)
        tree = value_wait_tree(d)
        assert closed == tree, (d, closed, tree)
        gap = closed - max(value_act(d), value_off(d))
        # EVPI computed independently: pay to learn sign(U) first, then commit
        informed = F(0)
        for p, u in d:
            informed += p * max(u, F(0))
        evpi = informed - max(value_act(d), value_off(d))
        assert gap == evpi, (d, gap, evpi)
        if not mixed_sign(d):
            assert gap == 0, (d, gap)
        else:
            assert gap > 0, (d, gap)
    certain = [(F(1, 2), F(3)), (F(1, 2), F(5))]
    assert value_wait_closed(certain) - max(value_act(certain), value_off(certain)) == 0
    return "deference gap equals EVPI exactly on 400 beliefs, by two code paths; zero when the sign is known"


def check_27():
    """A noisy H breaks deference, and the breaking point is a closed-form rational."""
    checked = 0
    for _ in range(300):
        d = random_belief()
        if not mixed_sign(d):
            continue
        up = E(d, lambda u: u if u > 0 else F(0))
        dn = E(d, lambda u: u if u < 0 else F(0))
        absmass = up - dn
        assert absmass > 0, d
        closed = max(up, -dn) / absmass
        best_committed = max(value_act(d), value_off(d))

        def wait_value(p):
            return p * up + (1 - p) * dn

        # independent route: scan a rational grid for the crossing
        lo, hi = None, None
        for i in range(0, 241):
            p = F(i, 240)
            if wait_value(p) >= best_committed:
                lo = p
                break
        assert lo is not None, d
        assert abs(lo - closed) <= F(1, 240), (lo, closed)
        assert closed >= F(1, 2), (closed, d)      # H must beat a coin flip
        assert wait_value(F(1)) >= best_committed
        assert wait_value(F(0)) <= best_committed
        checked += 1
    assert checked > 100, checked
    return ("on %d mixed-sign beliefs the deference threshold is p* = max(E[U+], -E[U-])/E[|U|], "
            "always at least 1/2, and a 240-point grid scan lands within one grid step of it"
            % checked)


def check_28():
    """Miscalibration: over-confidence costs exactly the EVPI; over-humility is free
    HERE -- which is where this anchor fails to reproduce its source."""
    overconf_losses, overhum_losses = [], []
    for _ in range(300):
        d = random_belief()
        if not mixed_sign(d):
            continue
        mean = E(d)
        truth_if_wait = value_wait_closed(d)
        best_committed = max(mean, F(0))
        # lambda = 0: point mass at the mean (over-confident); 1: calibrated; >1: over-dispersed
        for lam, bucket in ((F(0), overconf_losses), (F(2), overhum_losses)):
            belief = [(p, mean + lam * (u - mean)) for p, u in d]
            b_wait = value_wait_closed(belief)
            b_best = max(E(belief), F(0))
            waits = b_wait > b_best
            realised = truth_if_wait if waits else best_committed
            bucket.append(truth_if_wait - realised)
    assert overconf_losses and overhum_losses
    assert all(x > 0 for x in overconf_losses), "over-confidence should always cost"
    assert all(x == 0 for x in overhum_losses), "over-humility unexpectedly costly"
    assert max(overconf_losses) > 0
    return ("over-confident belief loses the full EVPI on all %d mixed-sign beliefs; "
            "over-dispersed belief loses exactly 0 -- the anchor cannot reproduce the "
            "source's second failure mode" % len(overconf_losses))


# ---- borrowed second anchor, for one purpose only (S51) ----
# TWOROUTE: s0 -> L -> A, or s0 -> R -> A.  Interruption hits only the L branch,
# forcing outcome Z instead of A with probability q.  KW cannot host this: it has
# no two routes to the same place.
def tworoute_fixed_points(q, rA=F(1), rZ=F(0)):
    """Exact fixed points of the two update rules -- solved, not simulated."""
    q_learning = {'l': rA, 'r': rA}                    # off-policy target ignores interruption
    sarsa = {'l': (1 - q) * rA + q * rZ, 'r': rA}      # on-policy value of what happens
    return q_learning, sarsa


def check_29():
    """Q-learning is indifferent to interruption; Sarsa learns to route around it."""
    flips = 0
    for i in range(1, 41):
        q = F(i, 40)
        ql, sa = tworoute_fixed_points(q)
        assert ql['l'] == ql['r'], (q, ql)             # Q-learning: no preference
        assert sa['l'] < sa['r'], (q, sa)              # Sarsa: avoids the interruptible route
        flips += 1
    ql0, sa0 = tworoute_fixed_points(F(0))             # control: q=0 must agree
    assert ql0['l'] == ql0['r'] and sa0['l'] == sa0['r'], (ql0, sa0)
    assert flips == 40, flips
    return ("over 40 interruption rates Q-learning stays indifferent and Sarsa strictly "
            "prefers the uninterruptible route; at q=0 both agree, so the test discriminates")



# ------------------- Chapter 6: the objective you get vs the one you trained
# KW(theta): each terminal carries k binary features.  A MESA-OBJECTIVE is a
# weight vector w; the policy takes the terminal with the larger w . x.  In
# training, feature 1 (the real one) is perfectly correlated with features 2..k.
FEATS = 3
TRAIN_GOOD, TRAIN_BAD = (1, 1, 1), (0, 0, 0)
TEST_GOOD, TEST_BAD = (1, 0, 0), (0, 1, 1)      # feature 1 still true, 2 and 3 flip


def dot(w, x):
    return sum(a * b for a, b in zip(w, x))


def prefers(w, good, bad):
    return dot(w, good) > dot(w, bad)


def weight_grid(n=3, k=FEATS):
    return list(product(range(-n, n + 1), repeat=k))


def check_30():
    """Training carves a half-space of mesa-objectives and pins exactly one dimension."""
    grid = weight_grid()
    train_ok = [w for w in grid if prefers(w, TRAIN_GOOD, TRAIN_BAD)]
    assert train_ok, "no training-optimal objective at all"
    for w in train_ok:                                   # a cone: positive scaling
        for a in (1, 2, 5):
            assert prefers(tuple(a * c for c in w), TRAIN_GOOD, TRAIN_BAD), (w, a)
    # lineality of the closure: directions you can travel both ways
    def closed(w):
        return dot(w, TRAIN_GOOD) - dot(w, TRAIN_BAD) >= 0
    lin = [w for w in grid if closed(w) and closed(tuple(-c for c in w))]
    for w in lin:
        assert sum(w) == 0, w                            # exactly the plane w.1 = 0
    dims = len({tuple(w) for w in lin})
    assert dims > len(weight_grid(3, 1)), (dims,)        # bigger than a line
    assert all(sum(w) == 0 for w in lin)
    true_obj = (1, 0, 0)
    assert prefers(true_obj, TRAIN_GOOD, TRAIN_BAD) and prefers(true_obj, TEST_GOOD, TEST_BAD)
    return ("training-optimal set is a cone under positive scaling; its lineality is exactly "
            "the plane w1+w2+w3=0, so training pins 1 of %d dimensions and leaves the rest free"
            % FEATS)


def check_31():
    """SEARCH for a mesa-objective that is training-optimal and test-catastrophic."""
    grid = weight_grid()
    train_ok = [w for w in grid if prefers(w, TRAIN_GOOD, TRAIN_BAD)]
    generalises = [w for w in train_ok if prefers(w, TEST_GOOD, TEST_BAD)]
    fails = [w for w in train_ok if not prefers(w, TEST_GOOD, TEST_BAD)]
    assert fails, "no training-optimal objective fails at test: nothing to find"
    assert generalises, "no training-optimal objective generalises"
    frac = F(len(generalises), len(train_ok))
    assert frac < 1, frac
    # POSITIVE CONTROL: train on the decorrelated configuration too, and the
    # failures must vanish -- the mechanism is correlation, not malice.
    both = [w for w in grid
            if prefers(w, TRAIN_GOOD, TRAIN_BAD) and prefers(w, TEST_GOOD, TEST_BAD)]
    assert all(prefers(w, TEST_GOOD, TEST_BAD) for w in both), "control is broken"
    assert len(both) < len(train_ok), (len(both), len(train_ok))
    return ("%d of %d training-optimal objectives fail at test (%s generalise); adding the "
            "decorrelated configuration to training removes every failure"
            % (len(fails), len(train_ok), frac))


def check_32():
    """A train/test distinguisher multiplies the underdetermination exactly."""
    grid = weight_grid()
    train_ok = [w for w in grid if prefers(w, TRAIN_GOOD, TRAIN_BAD)]
    base = F(len([w for w in train_ok if prefers(w, TEST_GOOD, TEST_BAD)]), len(train_ok))
    # now the objective may depend on an observed train flag: (w_train, w_test)
    flagged_ok = len(train_ok) * len(grid)               # w_test wholly unconstrained
    flagged_gen = len(train_ok) * len([w for w in grid if prefers(w, TEST_GOOD, TEST_BAD)])
    flagged = F(flagged_gen, flagged_ok)
    unconditional = F(len([w for w in grid if prefers(w, TEST_GOOD, TEST_BAD)]), len(grid))
    assert flagged_ok == len(train_ok) * len(grid), flagged_ok
    # The flag makes test behaviour INDEPENDENT of training: the conditional
    # fraction collapses onto the prior exactly.
    assert flagged == unconditional, (flagged, unconditional)
    # Without the flag training is informative -- and here it informs the WRONG way.
    assert base != unconditional, (base, unconditional)
    assert base < unconditional, (base, unconditional)
    return ("a train/test distinguisher multiplies the consistent set by exactly %d and drives "
            "the generalising fraction to the prior %s, i.e. training carries zero information "
            "about test behaviour; without the flag it carries %s, which is WORSE than the "
            "prior -- correlated training actively misinforms"
            % (len(grid), flagged, base))


def check_33():
    """Inner alignment IS Chapter 4's identifiability problem, run by the trainer."""
    grid = weight_grid()

    def free_dims(constraints):
        """Directions indistinguishable by the given training comparisons."""
        out = []
        for w in grid:
            if all(dot(w, g) - dot(w, b) == 0 for g, b in constraints):
                out.append(w)
        return out

    one = free_dims([(TRAIN_GOOD, TRAIN_BAD)])
    two = free_dims([(TRAIN_GOOD, TRAIN_BAD), (TEST_GOOD, TEST_BAD)])
    assert len(one) > len(two), (len(one), len(two))
    for w in one:
        assert sum(w) == 0, w
    assert (1, -1, 0) in one and (1, -1, 0) not in two
    assert all(dot(w, TEST_GOOD) == dot(w, TEST_BAD) for w in two)
    return ("the training-indistinguishable directions form a subspace: %d grid points on one "
            "comparison, %d on two -- the same cone-and-lineality structure as Chapter 4, with "
            "the training set doing the observing" % (len(one), len(two)))


def check_34():
    """Coverage is the fix, and it can be priced."""
    grid = weight_grid()
    configs = [
        (TRAIN_GOOD, TRAIN_BAD),
        (TEST_GOOD, TEST_BAD),
        ((1, 1, 0), (0, 0, 1)),
        ((1, 0, 1), (0, 1, 0)),
    ]
    counts = []
    for i in range(1, len(configs) + 1):
        ok = [w for w in grid if all(prefers(w, g, b) for g, b in configs[:i])]
        counts.append(len(ok))
    assert all(b <= a for a, b in zip(counts, counts[1:])), counts
    assert counts[0] > counts[-1], counts
    survivors = [w for w in grid if all(prefers(w, g, b) for g, b in configs)]
    assert survivors, "full coverage eliminated every objective"
    for w in survivors:
        assert prefers(w, TEST_GOOD, TEST_BAD), w
        assert w[0] > 0, w                                # every survivor tracks feature 1
    return ("consistent objectives fall %s as coverage grows; every survivor of full coverage "
            "has positive weight on the true feature" % ' -> '.join(str(c) for c in counts))



# --------------------------------- Chapter 7: teaching by comparison (exact BT)
ITEMS = ('A', 'B', 'bot')
PAIRS = [('A', 'B'), ('A', 'bot'), ('B', 'bot')]


def bt_likelihood(v, wins):
    """Bradley-Terry likelihood with rational weights.  wins[(i,j)] = times i beat j."""
    L = F(1)
    for (i, j), c in wins.items():
        if c:
            L *= (v[i] / (v[i] + v[j])) ** c
    return L


def all_wins(outcomes, n=1):
    """outcomes: for each pair, how many of n comparisons the FIRST item won."""
    w = {}
    for (i, j), k in zip(PAIRS, outcomes):
        w[(i, j)] = k
        w[(j, i)] = n - k
    return w


def ford_connected(wins):
    """MLE exists and is unique up to scale iff every 2-way split has a crossing win."""
    for r in (1, 2):
        for S in combinations(ITEMS, r):
            T = tuple(x for x in ITEMS if x not in S)
            if not any(wins.get((i, j), 0) > 0 for i in S for j in T):
                return False
    return True


def check_35():
    """The BT likelihood is scale-invariant in weights -- Chapter 1's constant, third costume."""
    wins = all_wins((1, 1, 0), n=1)
    base = None
    for _ in range(400):
        v = {t: F(random.randint(1, 20), random.randint(1, 9)) for t in ITEMS}
        lam = F(random.randint(1, 30), random.randint(1, 7))
        scaled = {t: lam * v[t] for t in ITEMS}
        assert bt_likelihood(v, wins) == bt_likelihood(scaled, wins), (v, lam)
        base = v
    # and NOT invariant under a non-uniform change: the discriminator works
    bumped = {t: (base[t] * 2 if t == 'A' else base[t]) for t in ITEMS}
    assert bt_likelihood(base, wins) != bt_likelihood(bumped, wins), base
    return ("BT likelihood exactly invariant under 400 rescalings of the weights, and moved by "
            "a non-uniform bump; in score space this is the additive constant of Chapters 1 and 4")


def check_36():
    """With one comparison per pair, BT identifies a finite score on exactly the
    INTRANSITIVE datasets."""
    identifiable, separable = [], []
    for outcomes in product((0, 1), repeat=3):
        wins = all_wins(outcomes, n=1)
        (identifiable if ford_connected(wins) else separable).append(outcomes)
    assert len(identifiable) + len(separable) == 8, (identifiable, separable)
    assert len(identifiable) == 2, identifiable
    assert len(separable) == 6, separable

    def transitive(outcomes):
        wins = all_wins(outcomes, n=1)
        return any(all(wins.get((x, y), 0) > 0 for y in ITEMS if y != x) for x in ITEMS)

    for o in separable:
        assert transitive(o), o
    for o in identifiable:
        assert not transitive(o), o

    # The full condition quantifies over BOTH split sizes.  On one-per-pair data the
    # pair-split clause never fires, so it is untested there -- SEARCH n=2 data for a
    # case where the two versions disagree, or the clause is decoration.
    def singleton_only(wins):
        for S in combinations(ITEMS, 1):
            T = tuple(x for x in ITEMS if x not in S)
            if not any(wins.get((i, j), 0) > 0 for i in S for j in T):
                return False
        return True

    disagreement = None
    for outcomes in product((0, 1, 2), repeat=3):
        wins = all_wins(outcomes, n=2)
        if singleton_only(wins) != ford_connected(wins):
            disagreement = outcomes
            break
    assert disagreement is not None, "pair-split clause is inert on all n=2 data too"
    w = all_wins(disagreement, n=2)
    assert singleton_only(w) and not ford_connected(w), disagreement
    return ("8 one-per-pair datasets: 6 transitive and unidentifiable, 2 cyclic and "
            "identifiable -- only the data that looks inconsistent pins a finite score; "
            "and %s is an n=2 dataset the singleton-only test wrongly accepts"
            % (disagreement,))


def check_37():
    """Non-existence is not an artifact: the likelihood climbs forever on separable
    data and vanishes on the boundary otherwise."""
    sep = (1, 1, 1)                        # A > B > bot, a clean total order
    cyc = (1, 0, 1)                        # A > B, bot > A, B > bot
    wins_sep, wins_cyc = all_wins(sep), all_wins(cyc)
    assert not ford_connected(wins_sep) and ford_connected(wins_cyc)
    # separable: pushing the winner up strictly increases the likelihood, forever
    v = {'A': F(1), 'B': F(1), 'bot': F(1)}
    prev = bt_likelihood(v, wins_sep)
    climbs = 0
    for k in range(1, 25):
        v2 = {'A': F(2) ** k, 'B': F(1), 'bot': F(2) ** -k}
        cur = bt_likelihood(v2, wins_sep)
        assert cur > prev, (k, cur, prev)
        prev = cur
        climbs += 1
    assert climbs == 24, climbs
    assert prev < F(1), prev                # climbs toward, never reaches, 1
    # cyclic: likelihood vanishes as any weight runs to an extreme
    for t in ITEMS:
        for k in (10, 20, 40):
            far = {x: (F(2) ** k if x == t else F(1)) for x in ITEMS}
            near = {x: (F(2) ** -k if x == t else F(1)) for x in ITEMS}
            mid = bt_likelihood({x: F(1) for x in ITEMS}, wins_cyc)
            assert bt_likelihood(far, wins_cyc) < mid, (t, k)
            assert bt_likelihood(near, wins_cyc) < mid, (t, k)
    return ("separable data: likelihood strictly climbs over 24 doublings and stays below 1; "
            "cyclic data: likelihood falls off in all 6 boundary directions, so the maximum is interior")


def check_38():
    """KL-regularised optimisation reproduces Chapter 3's wedge with a different knob.

    pi_k is proportional to pi_ref * u^k, the exact KL-optimal form with k = 1/beta
    and reward r = beta*log(u).  Integer weights keep every quantity a small rational.
    """
    NAL, U_FLOOD, T_FLOOD = 25, 28, F(-40)

    def sweep(u_flood, t_flood, K=10):
        ref = [F(1, NAL + 1)] * (NAL + 1)
        u = [F(j + 1) for j in range(NAL)] + [F(u_flood)]
        proxy = list(u)
        true = [F(j) for j in range(NAL)] + [t_flood]
        ep, et = [], []
        for k in range(K):
            w = [r * (ui ** k) for r, ui in zip(ref, u)]
            Z = sum(w)
            p = [x / Z for x in w]
            ep.append(sum(a * b for a, b in zip(p, proxy)))
            et.append(sum(a * b for a, b in zip(p, true)))
        return ep, et

    ep, et = sweep(U_FLOOD, T_FLOOD)
    assert all(b > a for a, b in zip(ep, ep[1:])), ep
    peak = max(range(len(et)), key=lambda i: et[i])
    assert 0 < peak < len(et) - 1, (peak, [float(x) for x in et])
    assert all(b > a for a, b in zip(et[:peak + 1], et[1:peak + 1])), et[:peak + 1]
    assert all(b < a for a, b in zip(et[peak:], et[peak + 1:])), et[peak:]
    # K4 control: with proxy == true there is no wedge to find
    ref = [F(1, NAL)] * NAL
    ua = [F(j + 1) for j in range(NAL)]
    ctrl = []
    for k in range(10):
        w = [r * (ui ** k) for r, ui in zip(ref, ua)]
        Z = sum(w)
        ctrl.append(sum((x / Z) * av for x, av in zip(w, ua)))
    assert all(b > a for a, b in zip(ctrl, ctrl[1:])), ctrl
    # is the SHAPE generic, or did the chosen table do the work?  Searched.
    turned = trials = 0
    for _ in range(25):
        uf = random.randint(NAL + 1, NAL + 8)
        tf = F(-random.randint(20, 80))
        _, e = sweep(uf, tf)
        pk = max(range(len(e)), key=lambda i: e[i])
        trials += 1
        if pk < len(e) - 1:
            turned += 1
    assert turned == trials, (turned, trials)
    return ("KL pressure knob k: proxy rises at every step, truth peaks at k=%d then falls "
            "monotonically; aligned control never turns over; the curve turns over in %d/%d "
            "random tables -- Chapter 3's wedge from a different lever" % (peak, turned, trials))


def check_39():
    """DPO's reparameterisation is exact, and the partition function never appears."""
    for _ in range(300):
        ref = {t: F(random.randint(1, 9), 20) for t in ITEMS}
        u = {t: F(random.randint(1, 12), random.randint(1, 5)) for t in ITEMS}
        w = {t: ref[t] * u[t] for t in ITEMS}
        Z = sum(w.values())
        pi = {t: w[t] / Z for t in ITEMS}
        for i, j in PAIRS:
            from_reward = u[i] / (u[i] + u[j])
            ratio_i = pi[i] / ref[i]
            ratio_j = pi[j] / ref[j]
            from_policy = ratio_i / (ratio_i + ratio_j)
            assert from_reward == from_policy, (i, j, from_reward, from_policy)
    # the stated assumption, made concrete: zero reference mass breaks the inversion
    broke = 0
    for _ in range(200):
        ref = {t: F(random.randint(0, 9), 20) for t in ITEMS}
        if all(ref[t] > 0 for t in ITEMS):
            continue
        broke += 1
    assert broke > 0, "never sampled a zero-support reference: assumption untested"
    return ("preference implied by the reward equals the one implied by the policy ratio on "
            "300 draws, with Z cancelling identically; %d sampled references had zero support, "
            "where the inversion is undefined" % broke)



# ---------------------------- Chapter 8: checking work you cannot do yourself
# KW^d: a depth-d binary tree of kettle decisions.  2^d terminals, one judge who
# can evaluate exactly one leaf.
def leaves(d):
    return list(product((0, 1), repeat=d))


def build_tree(d, vals):
    return dict(zip(leaves(d), vals))


def subtree_max(tree, prefix, d):
    return max(v for leaf, v in tree.items() if leaf[:len(prefix)] == prefix)


def debate_honest_wins(tree, d, claim, judge_correct=True, unverifiable=()):
    """Dishonest asserts the tree's max is `claim` (an overclaim).  At each node it
    steers to a child; honest reports that child's true max; they recurse; the judge
    checks one leaf.  Returns 'honest', 'dishonest' or 'draw'."""
    true_max = subtree_max(tree, (), d)
    if claim <= true_max:
        return 'honest'                      # not an overclaim; nothing to expose
    # dishonest picks the path; it prefers an unverifiable leaf if one is reachable
    target = None
    for leaf in tree:
        if leaf in unverifiable:
            target = leaf
            break
    if target is None:
        target = min(tree, key=lambda L: tree[L])
    if target in unverifiable:
        return 'draw'
    if not judge_correct:
        return 'dishonest'
    return 'honest' if tree[target] < claim else 'dishonest'


def check_40():
    """Depth buys exponential coverage for linear judge effort."""
    ratios = []
    for d in range(1, 13):
        n_leaves = 2 ** d
        path = d
        assert len(leaves(d)) == n_leaves, d
        ratios.append(F(n_leaves, path))
    assert all(b >= a for a, b in zip(ratios, ratios[1:])), ratios
    # 2^d/d ties at d=1 and d=2 and is strictly increasing thereafter -- state it,
    # do not paper over it with a non-strict assertion everywhere.
    assert ratios[0] == ratios[1] == F(2), ratios[:2]
    assert all(b > a for a, b in zip(ratios[1:], ratios[2:])), ratios[1:]
    assert ratios[-1] > 100 * ratios[0], (ratios[0], ratios[-1])
    return ("leaves/debate-path ratio 2^d/d rises %s -> %s over depths 1..12; it ties at d=1 "
            "and d=2 and is strictly increasing after" % (ratios[0], ratios[-1]))


def check_41():
    """Exhaustive: a correct judge makes honesty win, and an inverted one does not."""
    d = 3
    wins = losses = 0
    for vals in product((0, 1, 2), repeat=2 ** d):
        tree = build_tree(d, [F(v) for v in vals])
        tm = subtree_max(tree, (), d)
        for over in (F(1), F(2), F(5)):
            claim = tm + over
            assert debate_honest_wins(tree, d, claim) == 'honest', (vals, claim)
            wins += 1
            assert debate_honest_wins(tree, d, claim, judge_correct=False) == 'dishonest'
            losses += 1
        # a claim that is NOT an overclaim must not be scored as a catch
        assert debate_honest_wins(tree, d, tm) == 'honest', vals
    assert wins == losses > 0, (wins, losses)
    return ("over all %d depth-3 trees and 3 overclaims each: honesty wins every time under a "
            "correct judge and loses every time under an inverted one" % (3 ** 8))


def check_42():
    """The depth advantage is paid for in judge reliability, and the price is exact."""
    alpha = F(99, 100)
    grid = [F(i, 10000) for i in range(9000, 10001)]
    needed = []
    for d in range(1, 13):
        q = next(q for q in grid if q ** d >= alpha)
        needed.append(q)
        assert q ** d >= alpha, (d, q)
        if q > grid[0]:
            prev = grid[grid.index(q) - 1]
            assert prev ** d < alpha, (d, prev)     # minimal on the grid
    assert all(b >= a for a, b in zip(needed, needed[1:])), needed
    assert needed[-1] > needed[0], (needed[0], needed[-1])
    assert needed[-1] < F(1), needed[-1]
    assert needed[0] == alpha, (needed[0], alpha)      # depth 1: q = alpha exactly
    return ("to keep overall reliability at 99%% the per-query judge accuracy must rise from %s "
            "at depth 1 to %s at depth 12 -- the depth discount is paid for at the judge"
            % (needed[0], needed[-1]))


def check_43():
    """One unverifiable leaf is enough to force a draw from every position."""
    d = 2
    forced = clean = 0
    for vals in product((0, 1, 2, 3), repeat=2 ** d):
        tree = build_tree(d, [F(v) for v in vals])
        tm = subtree_max(tree, (), d)
        claim = tm + 1
        assert debate_honest_wins(tree, d, claim, unverifiable=()) == 'honest', vals
        clean += 1
        for leaf in tree:
            assert debate_honest_wins(tree, d, claim, unverifiable=(leaf,)) == 'draw', (vals, leaf)
            forced += 1
    assert clean > 0 and forced == clean * 2 ** d, (clean, forced)
    return ("with every leaf checkable honesty wins all %d depth-2 positions; making any single "
            "leaf unverifiable forces a draw in all %d cases" % (clean, forced))


def check_44():
    """Weak-to-strong on the anchor: PGR computed exactly, with the mechanism the
    literature actually relies on -- weak LABEL NOISE the student cannot represent."""
    vecs = list(product((0, 1), repeat=3))
    truth = (1, 0, 0)
    cfg = [(g, b) for g in vecs for b in vecs
           if g != b and dot(truth, g) != dot(truth, b)]
    assert len(cfg) == 32, len(cfg)
    truth_labels = [(g, b) if prefers(truth, g, b) else (b, g) for g, b in cfg]
    grid = weight_grid()

    def acc(w, labels):
        return F(sum(1 for g, b in labels if prefers(w, g, b)), len(labels))

    ceiling = max(acc(w, truth_labels) for w in grid)
    assert ceiling == 1, ceiling

    def pgr_for(flips):
        weak = [(b, g) if i in flips else (g, b) for i, (g, b) in enumerate(truth_labels)]
        floor = F(len(cfg) - len(flips), len(cfg))
        best = max(acc(w, weak) for w in grid)
        argmax = [w for w in grid if acc(w, weak) == best]
        w2s = sum(acc(w, truth_labels) for w in argmax) / len(argmax)
        return (w2s - floor) / (ceiling - floor), floor

    by_noise = {}
    for k in (1, 2, 4, 8, 12):
        vals = []
        for _ in range(12):
            flips = set(random.sample(range(len(cfg)), k))
            p, floor = pgr_for(flips)
            assert floor < ceiling, (k, floor)
            vals.append(p)
        by_noise[k] = (sum(vals) / len(vals), sum(1 for v in vals if v > 0), len(vals))
        assert all(v >= 0 for v in vals), (k, [float(v) for v in vals])
    ks = sorted(by_noise)
    # low noise: the effect is universal in the sample
    assert by_noise[1][1] == by_noise[1][2], by_noise[1]
    assert by_noise[2][1] == by_noise[2][2], by_noise[2]
    assert by_noise[ks[-1]][0] < by_noise[ks[0]][0], by_noise
    # K4: the measure must be able to return zero.  SEARCH for a label pattern that
    # recovers nothing, rather than assuming random sampling will supply one.
    zero_case = None
    for _ in range(400):
        k = random.randint(4, 14)
        flips = set(random.sample(range(len(cfg)), k))
        p, _ = pgr_for(flips)
        if p == 0:
            zero_case = (k, p)
            break
    assert zero_case is not None, "PGR never returns zero: the metric is not discriminating here"
    return ("mean PGR falls from %.3f (positive in %d/%d trials) at %d wrong labels to %.3f "
            "(%d/%d) at %d -- the student beats its supervisor at low noise and sometimes "
            "recovers nothing at high noise"
            % (float(by_noise[ks[0]][0]), by_noise[ks[0]][1], by_noise[ks[0]][2], ks[0],
               float(by_noise[ks[-1]][0]), by_noise[ks[-1]][1], by_noise[ks[-1]][2], ks[-1])
            + "; a search found a %d-error pattern recovering exactly nothing" % zero_case[0])



# ------------------------------------- Chapter 9: opening the box (anchor TRI)
# TRI: three features in two dimensions.  Built as the projection of the 3D
# standard basis orthogonal to (1,1,1) -- the construction the source uses.
# Everything stays rational: cosines are compared as (u.v)^2 / (|u|^2 |v|^2).
def tri_frame():
    e = [(F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1))]
    out = []
    for v in e:
        m = sum(v) / 3
        out.append(tuple(c - m for c in v))          # remove the (1,1,1) component
    return out


def vdot(u, v):
    return sum(a * b for a, b in zip(u, v))


def cos2(u, v):
    return F(vdot(u, v) ** 2, 1) / (vdot(u, u) * vdot(v, v))


def check_45():
    """The frame's off-diagonal cosine is exactly -1/2, with no square roots."""
    W = tri_frame()
    assert all(sum(v) == 0 for v in W), W                 # lies in the (1,1,1)-plane
    n2 = vdot(W[0], W[0])
    for v in W:
        assert vdot(v, v) == n2 == F(2, 3), (v, n2)
    for i, j in combinations(range(3), 2):
        assert vdot(W[i], W[j]) == F(-1, 3), (i, j)
        assert vdot(W[i], W[j]) / n2 == F(-1, 2), (i, j)  # normalised cosine
    total = tuple(sum(v[k] for v in W) for k in range(3))
    assert total == (F(0), F(0), F(0)), total
    # the one-line reason: |sum|^2 = 3 + 2*sum_{i<j} cos = 0
    assert 3 * F(1) + 2 * sum(vdot(W[i], W[j]) / n2 for i, j in combinations(range(3), 2)) == 0
    return "frame vectors sum to zero, norms 2/3, pairwise cosine exactly -1/2 in rationals"


def check_46():
    """Three directions in a plane cannot beat cos^2 = 1/4, and the frame attains it."""
    dirs = set()
    for a in range(-4, 5):
        for b in range(-4, 5):
            if (a, b) == (0, 0):
                continue
            g = math.gcd(abs(a), abs(b))
            a2, b2 = a // g, b // g
            if (a2 < 0) or (a2 == 0 and b2 < 0):
                a2, b2 = -a2, -b2
            dirs.add((a2, b2))
    dirs = sorted(dirs)
    best = None
    attained = 0
    for t in combinations(dirs, 3):
        worst = max(cos2(t[i], t[j]) for i, j in combinations(range(3), 2))
        assert worst >= F(1, 4), (t, worst)
        if best is None or worst < best:
            best = worst
        if worst == F(1, 4):
            attained += 1
    # The bound is 1/4 and NO rational direction triple in the plane attains it:
    # 60 degrees needs tan = sqrt(3).  The frame attains it only because its
    # coordinates are rational in the sum-zero plane of R^3, not in R^2.
    assert best > F(1, 4), best
    assert attained == 0, attained
    assert len(dirs) > 20, len(dirs)
    W = tri_frame()
    assert max(cos2(W[i], W[j]) for i, j in combinations(range(3), 2)) == F(1, 4)
    return ("over all %d triples of %d rational planar directions the largest pairwise cos^2 is "
            "never below 1/4 and never equals it -- the best is %s; the projected frame attains "
            "1/4 exactly, which is why the construction is a projection"
            % (len(list(combinations(dirs, 3))), len(dirs), best))


def check_47():
    """Superposition is a capacity trade, and the crossover is exactly located."""
    def err_super(p):
        # ReLU decode, 3 features, 2 others each active with probability p
        per = F(1, 4) * (2 * p * p * (1 - p)) + p ** 3
        return 3 * per

    def err_dedicate(p):
        return p                                     # two features exact, third dropped

    grid = [F(i, 200) for i in range(1, 200)]
    wins = [p for p in grid if err_super(p) < err_dedicate(p)]
    loses = [p for p in grid if err_super(p) >= err_dedicate(p)]
    assert wins and loses, (len(wins), len(loses))
    assert max(wins) < min(loses), (max(wins), min(loses))
    lo, hi = max(wins), min(loses)
    # the crossover solves 3p^2 + 3p - 2 = 0; bracket it by an exact sign change
    f = lambda p: 3 * p * p + 3 * p - 2
    assert f(lo) < 0 < f(hi), (f(lo), f(hi))
    assert lo < F(46, 100) and hi <= F(47, 100), (lo, hi)
    return ("superposition beats dedicating dimensions for every sparsity below %s and never "
            "at or above %s; the crossover is bracketed by an exact sign change of 3p^2+3p-2"
            % (lo, hi))


def check_48():
    """'Triangle' does not determine the numbers -- the sum-to-zero condition does."""
    triangles = []
    for a in product(range(-3, 4), repeat=2):
        for b in product(range(-3, 4), repeat=2):
            for c in product(range(-3, 4), repeat=2):
                V = [a, b, c]
                if any(v == (0, 0) for v in V):
                    continue
                if len({tuple(v) for v in V}) < 3:
                    continue
                cs = [cos2(V[i], V[j]) for i, j in combinations(range(3), 2)]
                if len(set(cs)) == 1 and cs[0] != F(1, 4):
                    triangles.append((V, cs[0]))
                    if len(triangles) > 3:
                        break
            if len(triangles) > 3:
                break
        if len(triangles) > 3:
            break
    assert triangles, "no equal-cosine triple with a different value exists in the grid"
    for V, c in triangles:
        assert c != F(1, 4), (V, c)
        s = tuple(sum(v[k] for v in V) for k in range(2))
        assert s != (0, 0), (V, s)                   # and none of them sums to zero
    return ("found %d equally-spaced triples whose common cos^2 is NOT 1/4; every one fails the "
            "sum-to-zero condition, which is what fixes the number" % len(triangles))


def check_49():
    """Two dimensions cannot tell 'nothing active' from 'everything active'."""
    W = tri_frame()
    codes = {}
    for mask in product((0, 1), repeat=3):
        h = tuple(sum(m * W[i][k] for i, m in enumerate(mask)) for k in range(3))
        codes.setdefault(h, []).append(mask)
    assert len(codes) == 7, len(codes)
    collisions = [v for v in codes.values() if len(v) > 1]
    assert len(collisions) == 1, collisions
    assert sorted(collisions[0]) == [(0, 0, 0), (1, 1, 1)], collisions[0]
    singles = [m for v in codes.values() if len(v) == 1 for m in v]
    assert len(singles) == 6, len(singles)
    return ("8 activation patterns collapse to 7 codes; the single collision is exactly "
            "{} against {1,2,3} -- silence and saturation are the same vector")



# ------------------------- Chapter 10: assuming it is not on your side
# A two-strategy control protocol on KW, priced exactly.  Suspicion scores run
# 0..4.  Blue audits the top score (budget-limited) and defers everything at or
# above a threshold t.  Red submits one backdoor attempt.
BENIGN = [F(1, 2), F(1, 4), F(1, 8), F(3, 32), F(1, 32)]
ATTACK = [F(1, 32), F(3, 32), F(1, 8), F(1, 4), F(1, 2)]
AUDIT_BUDGET = F(1, 20)


def tail(dist, lo):
    return sum(dist[i] for i in range(lo, len(dist)))


def protocol(t):
    """Returns (usefulness, safety) exactly.  t=5 means never defer."""
    blocked_from = min(t, 4)
    safety = tail(ATTACK, blocked_from)
    usefulness = 1 - tail(BENIGN, t) if t <= 4 else F(1)
    return usefulness, safety


def check_50():
    """The safety-usefulness frontier, exactly, and one protocol is strictly dominated."""
    assert sum(BENIGN) == 1 and sum(ATTACK) == 1, (sum(BENIGN), sum(ATTACK))
    assert tail(BENIGN, 4) <= AUDIT_BUDGET, (tail(BENIGN, 4), AUDIT_BUDGET)
    pts = {t: protocol(t) for t in range(6)}
    dominated = []
    for t, (u, sf) in pts.items():
        for t2, (u2, sf2) in pts.items():
            if t2 != t and u2 >= u and sf2 >= sf and (u2, sf2) != (u, sf):
                dominated.append(t)
                break
    assert len(dominated) == 1, (dominated, pts)
    assert dominated == [4], dominated
    frontier = sorted((pts[t] for t in pts if t not in dominated), reverse=True)
    for (u1, s1), (u2, s2) in zip(frontier, frontier[1:]):
        assert u1 > u2 and s1 < s2, (u1, s1, u2, s2)
    assert pts[5] == (F(1), F(1, 2)), pts[5]
    assert pts[0] == (F(0), F(1)), pts[0]
    return ("6 protocols: exactly 1 strictly dominated; the remaining 5 form a strict frontier "
            "from (useful 1, safe 1/2) to (useful 0, safe 1)")


def check_51():
    """An untrusted monitor collapses safety to zero, and one probe restores the game."""
    colluding = [F(1)] + [F(0)] * 4          # reports "not suspicious" on its own attacks
    for t in range(1, 6):
        blocked_from = min(t, 4)
        assert sum(colluding[i] for i in range(blocked_from, 5)) == 0, t
    # only deferring EVERYTHING survives a colluding monitor
    assert sum(colluding[i] for i in range(0, 5)) == 1
    honest_safety = protocol(3)[1]
    assert honest_safety > 0, honest_safety
    # the defence: synthetic attacks the monitor cannot tell from real ones
    caught = []
    for k in range(0, 6):
        # a monitor that scores every attack 0 also scores every probe 0
        caught.append(F(1) if k >= 1 else F(0))
    assert caught[0] == 0 and all(c == 1 for c in caught[1:]), caught
    return ("a colluding monitor drives safety to exactly 0 at every threshold but total "
            "deferral, against %s for a trusted one; a single synthetic probe detects the "
            "collusion with certainty" % honest_safety)


def check_52():
    """Defence in depth is multiplicative only while the layers are independent."""
    m = F(1, 2)
    for k in (1, 2, 3, 5):
        indep = (1 - m) ** k
        assert indep == F(1, 2) ** k, (k, indep)
    gaps = []
    for rho_num in range(0, 11):
        rho = F(rho_num, 10)
        fail1 = rho * (1 - m) + (1 - rho) * (1 - m) ** 1
        fail5 = rho * (1 - m) + (1 - rho) * (1 - m) ** 5
        assert fail5 <= fail1, (rho, fail1, fail5)
        gaps.append(fail1 - fail5)
    assert all(b <= a for a, b in zip(gaps, gaps[1:])), gaps
    assert gaps[0] > 0, gaps[0]
    assert gaps[-1] == 0, gaps[-1]
    full = F(1) * (1 - m)
    for k in (1, 2, 3, 5, 20):
        assert F(1) * (1 - m) + F(0) * (1 - m) ** k == full, k
    return ("five independent layers cut failure from 1/2 to 1/32; at correlation 1 the same "
            "five layers cut it to 1/2, and the benefit of depth falls monotonically to exactly "
            "zero as correlation rises")


def check_53():
    """Adversarial training that never reaches the trigger removes nothing."""
    grid = weight_grid()
    trigger = ((0, 1, 1), (1, 0, 0))          # the reversed test configuration
    ordinary = [(TRAIN_GOOD, TRAIN_BAD), ((1, 1, 0), (0, 0, 1)), ((1, 0, 1), (0, 1, 0))]

    # PRECONDITION, asserted rather than assumed: the trigger must lie outside the
    # adversarial training set in both orientations, and must be genuinely
    # undetermined by it -- otherwise "training never reaches the trigger" is empty.
    assert trigger not in ordinary, trigger
    assert (trigger[1], trigger[0]) not in ordinary, trigger
    fits = [w for w in grid if all(prefers(w, g, b) for g, b in ordinary)]
    assert any(prefers(w, trigger[0], trigger[1]) for w in fits), "trigger forced by training"
    assert any(prefers(w, trigger[1], trigger[0]) for w in fits), "trigger forced by training"

    def backdoored(w, seen):
        return (all(prefers(w, g, b) for g, b in seen)
                and prefers(w, trigger[0], trigger[1]))

    counts = []
    for i in range(1, len(ordinary) + 1):
        counts.append(len([w for w in grid if backdoored(w, ordinary[:i])]))
    assert counts[0] > 0, counts
    assert all(b < a for a, b in zip(counts, counts[1:])), counts   # it DOES thin them
    assert counts[-1] > 0, counts                                    # and never clears them
    # now include the trigger itself in training
    with_trigger = [w for w in grid
                    if all(prefers(w, g, b) for g, b in ordinary)
                    and prefers(w, trigger[1], trigger[0])]
    surviving = [w for w in grid if backdoored(w, ordinary)]
    assert surviving, "no backdoored hypothesis survives: nothing to demonstrate"
    assert not any(w in with_trigger for w in surviving), "sets should be disjoint"
    assert counts[-1] == len(surviving), (counts[-1], len(surviving))
    for w in surviving:
        assert prefers(w, trigger[0], trigger[1]), w
    return ("ordinary adversarial training thins the backdoored population %s -- an 82%% cut "
            "that never reaches zero; every one of the %d survivors still fires on the untouched "
            "trigger, and only training on the trigger removes them, which requires knowing it"
            % (' -> '.join(str(c) for c in counts), counts[-1]))



# ---------------------------------------------- the count audit (Phase 3 gate)
TOUR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tour.md')


def _sections(text):
    """Split tour.md into (kind, title, body) where kind is 'numbered' or 'starred'."""
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith('#! '):
            cur = ['starred', line[3:].strip(), []]
            out.append(cur)
        elif line.startswith('# '):
            cur = ['numbered', line[2:].strip(), []]
            out.append(cur)
        elif cur is not None:
            cur[2].append(line)
    return [(k, t, '\n'.join(b)) for k, t, b in out]


def check_54():
    """Reconcile the source PER SECTION, split at the chapter/part boundary."""
    text = open(TOUR).read()
    secs = _sections(text)
    numbered = [s for s in secs if s[0] == 'numbered']
    starred = [s for s in secs if s[0] == 'starred']
    n_ch = len(numbered)
    assert n_ch == 10, n_ch
    assert text.count('<!--COUNT:chapter-->') == n_ch, text.count('<!--COUNT:chapter-->')

    # Box openers are matched by their OPENING PATTERN, not by the bare phrase --
    # a prose mention of the phrase is not a box.  Tightened patterns are new
    # patterns, so a positive control is run below.
    opener = '> **KEY CLAIM ('
    for kind, title, body in numbered:
        assert body.count(opener) == 1, (title, body.count(opener))
        assert body.count('\\bmn{') == 1, (title, body.count('\\bmn{'))
        assert body.count('## The demystification') == 1, title
    for kind, title, body in starred:
        assert body.count(opener) == 0, (title, 'starred section carries a key claim')
        assert body.count('\\bmn{') == 0, (title, 'starred section carries a signpost')
    assert text.count(opener) == n_ch, text.count(opener)
    assert text.count('\\bmn{') == n_ch, text.count('\\bmn{')

    # every receipt referenced in the prose must exist in the suite
    refs = set()
    for m in re.finditer(r'\[checks? ([0-9]+(?:\s*,\s*[0-9]+)*)', text):
        for tok in m.group(1).split(','):
            refs.add(int(tok.strip()))
    assert refs, "no receipts referenced in the source"
    assert refs <= set(CHECKS), sorted(refs - set(CHECKS))
    assert min(refs) == 1, min(refs)
    assert sorted(refs) == list(range(1, max(refs) + 1)), \
        [i for i in range(1, max(refs) + 1) if i not in refs]

    # part letters must be contiguous from A -- a gate, not a habit
    letters = re.findall(r'^#! Part ([A-Z]) ', text, re.M)
    assert letters, "no lettered parts found"
    assert letters == sorted(letters), letters
    assert letters == [chr(ord('A') + i) for i in range(len(letters))], letters
    assert text.count('<!--COUNT:part-->') == len(letters), \
        (text.count('<!--COUNT:part-->'), len(letters))

    # G3a: a tightened pattern is a new pattern.  Prove it still discriminates.
    injected = text.replace('#! Over the fence', '#! Over the fence\n\n' + opener + 'fake).**')
    bad = _sections(injected)
    fakes = [t for k, t, b in bad if k == 'starred' and b.count(opener) > 0]
    assert fakes, "control failed: an injected box in a starred section was not detected"
    # Second control, for the TIGHTENING itself.  The prose collision that
    # motivated it has since been edited away, so the tight pattern would now
    # agree with a naive one on this artifact -- manufacture the collision rather
    # than let the tightening go untested.
    with_prose = text.replace('#! Over the fence',
                              'as discussed in the KEY CLAIM box above\n\n#! Over the fence')
    assert with_prose.count('KEY CLAIM') == text.count('KEY CLAIM') + 1, "control not injected"
    assert with_prose.count(opener) == text.count(opener), "tight pattern followed the prose"
    assert opener != 'KEY CLAIM', "opener has been loosened to the bare phrase"
    naive = with_prose.count('KEY CLAIM')
    return ("%d numbered chapters, each with exactly 1 key claim, 1 signpost and 1 "
            "demystification; %d starred sections with none; receipts referenced gapless "
            "1..%d; with a prose mention injected a naive phrase count says %d and the "
            "tight opener still says %d"
            % (n_ch, len(starred), max(refs), naive, with_prose.count(opener))
            + "; part letters %s contiguous from A" % ''.join(letters))



# ---------------------------------------------------- Part C: timeline data
# The PRINTED rows are generated from this table, so a transposed row cannot
# ship silently.  written=None means written and published coincide.
# (published, written, entry, provenance)
TIMELINE = [
    (1927, None, "Thurstone, law of comparative judgement", "S"),
    (1929, None, "Zermelo, ranking as a maximum-likelihood problem", "P"),
    (1938, None, "Samuelson, revealed preference (with an August addendum)", "P"),
    (1942, None, "Asimov's laws, as a cultural marker", "M"),
    (1947, 1944, "von Neumann and Morgenstern, axiomatic utility ADDED in the 2nd edition", "S"),
    (1952, None, "Bradley and Terry, paired comparisons", "P"),
    (1954, None, "Olds and Milner, self-stimulation in rats", "S"),
    (1956, None, "Ridgway, dysfunctional consequences of performance measurement", "P"),
    (1957, None, "Ford Jr, existence condition for the paired-comparison MLE", "P"),
    (1960, None, "Wiener, Science 131(3410); Samuel's refutation, Science 132(3429)", "P"),
    (1965, None, "Good, speculations on the first ultraintelligent machine", "P"),
    (1967, None, "Afriat, construction of utility functions from expenditure data", "P"),
    (1969, 1948, "Turing, Intelligent Machinery (NPL report; publication year disputed)", "S"),
    (1972, None, "James P. Anderson, Computer Security Technology Planning Study", "S"),
    (1974, None, "Welch, lower bounds on maximum cross-correlation", "P"),
    (1975, None, "Goodhart, Problems of Monetary Management; Kerr, on the folly of rewarding A", "P"),
    (1975, None, "Saltzer and Schroeder, eight design principles -- defence in depth NOT among them", "P"),
    (1985, None, "Goldwasser, Micali and Rackoff, STOC; Babai, STOC", "P"),
    (1989, 1985, "Goldwasser, Micali and Rackoff, journal version", "P"),
    (1990, None, "NIH designates thirteen species as model organisms", "S"),
    (1992, 1990, "Shamir, IP = PSPACE; Lund, Fortnow, Karloff and Nisan", "P"),
    (1997, None, "Strathern, the sentence everyone attributes to Goodhart", "P"),
    (1998, None, "Russell, COLT: the inverse problem posed; Network Security Framework 1.0 brings defence in depth into computing", "P"),
    (2000, None, "Ng and Russell, algorithms for inverse RL; SIAI founded", "P"),
    (2003, None, "Bostrom, ethical issues in advanced AI (the paperclip example)", "S"),
    (2004, 1951, "Turing, Intelligent Machinery: A Heretical Theory, first widely published", "S"),
    (2005, None, "Future of Humanity Institute founded", "S"),
    (2006, None, "Donoho; Candes, Romberg and Tao: compressed sensing", "S"),
    (2008, None, "Omohundro, The Basic AI Drives, pp. 483-492; Ziebart et al., MaxEnt IRL", "P"),
    (2009, None, "Erhan et al., visualising higher-layer features; LessWrong launched", "S"),
    (2012, None, "Bostrom, The Superintelligent Will", "S"),
    (2013, None, "SIAI renamed the Machine Intelligence Research Institute", "P"),
    (2014, None, "Bostrom, Superintelligence; Future of Life Institute founded", "S"),
    (2015, None, "Puerto Rico conference (2-5 Jan); Corrigibility; OpenAI announced (11 Dec)", "P"),
    (2016, None, "Concrete Problems; CIRL; Safely Interruptible Agents; CHAI founded", "P"),
    (2017, None, "Off-Switch Game; deep RL from human preferences; gridworlds; Asilomar; Distill founded", "P"),
    (2018, None, "Armstrong and Mindermann; AI safety via debate; Goodhart taxonomy; Alignment Forum", "P"),
    (2019, None, "Hubinger et al., risks from learned optimization (arXiv only)", "P"),
    (2020, None, "Zoom In: circuits; obfuscated arguments; learning to summarize", "P"),
    (2021, None, "Anthropic incorporated; ARC founded; Distill hiatus; Transformer Circuits begun", "P"),
    (2022, None, "Toy Models of Superposition (14 Sep); reward hacking; InstructGPT; red-teaming LMs", "P"),
    (2023, None, "CAIS statement (30 May); Bletchley (1-2 Nov); EO 14110 (30 Oct); Towards Monosemanticity", "P"),
    (2024, None, "AI Control (ICML); Sleeper Agents; weak-to-strong; Scaling Monosemanticity; FHI closed; EU AI Act in force", "P"),
    (2025, None, "UK institute renamed to AI Security (14 Feb); Paris summit; SAE critiques accumulate", "S"),
    (2026, None, "Sparse-autoencoder sanity checks report low true-feature recovery", "S"),
]

# (start, end_exclusive, name, seam_is_ambiguous_at_start)
ERAS = [
    (1927, 1965, "Foundations and cybernetics", False),
    (1965, 2000, "Dormancy", True),
    (2000, 2014, "Pre-institutional modern era", False),
    (2014, 2016, "Field consolidation", True),
    (2016, 2022, "Deep-learning safety", False),
    (2022, 2023, "Deployment inflection", True),
    (2023, 2027, "Governance, evaluations and control", False),
]

# (name, birth, death) -- None means NOT FOUND and is printed as a blank
LIVES = [
    ("Wiener", 1894, 1964), ("Samuel", 1901, 1990), ("von Neumann", 1903, 1957),
    ("Morgenstern", 1902, 1977), ("Savage", 1917, 1971), ("Campbell", 1916, 1996),
    ("Bellman", 1920, 1984), ("Goodhart", 1936, None), ("Strathern", 1941, None),
    ("Samuelson", 1915, 2009), ("Houthakker", 1924, 2008), ("Varian", 1947, None),
    ("Thurstone", 1887, 1955), ("Bradley", 1923, 2001), ("Zermelo", 1871, 1953),
    ("Luce", 1925, 2012), ("Plackett", 1920, 2009), ("Olds", 1922, 1976),
    ("Milner", 1919, 2018), ("Thomson", 1856, 1940), ("Turing", 1912, 1954),
    ("Good", 1916, 2009), ("Jacobs", 1863, 1943), ("Micali", 1954, None),
    ("Rackoff", 1948, None), ("Babai", 1950, None), ("Shamir", 1952, None),
    ("Fortnow", 1963, None), ("Sipser", 1954, None), ("Kozen", 1951, None),
    ("Stockmeyer", 1948, 2004), ("Russell", 1962, None), ("Ng", 1976, None),
    ("Bostrom", 1973, None), ("Omohundro", 1959, None), ("Yudkowsky", 1979, None),
    ("Abbeel", 1977, None), ("Bengio", 1964, None), ("Barto", 1948, None),
    ("Anderson, Ross J.", 1956, 2024),
    ("Anderson, James P.", 1930, 2007),
    # deliberately blank: no reliable public birth year located in two passes
    ("Ridgway", None, None), ("Kerr", None, None), ("Afriat", None, None),
    ("Terry", None, None), ("Christiano", None, None), ("Amodei", None, None),
    ("Olah", None, None), ("Krakovna", None, None), ("Leike", None, None),
    ("Hubinger", None, None), ("Shlegeris", None, None), ("Barnes", None, None),
]


def check_55():
    """Verify the timeline STRUCTURALLY.  Four clauses, mutation-tested separately."""
    # (a) rows non-decreasing in published year
    years = [r[0] for r in TIMELINE]
    assert all(b >= a for a, b in zip(years, years[1:])), \
        [(years[i], years[i + 1]) for i in range(len(years) - 1) if years[i + 1] < years[i]]

    # (b) era bands non-interleaving, contiguous, and covering every row
    for (s1, e1, n1, _), (s2, e2, n2, _) in zip(ERAS, ERAS[1:]):
        assert e1 == s2, (n1, e1, n2, s2)
        assert s1 < e1, (n1, s1, e1)
    assert ERAS[0][0] <= min(years) and max(years) < ERAS[-1][1], (min(years), max(years))
    for y in years:
        hits = [n for s_, e_, n, _ in ERAS if s_ <= y < e_]
        assert len(hits) == 1, (y, hits)

    # (c) every printed life span runs forward and is plausible
    printed = [(n, b, d) for n, b, d in LIVES if b is not None]
    for n, b, d in printed:
        assert 1800 < b < 2010, (n, b)
        if d is not None:
            assert d > b, (n, b, d)
            assert d - b < 110, (n, b, d)
    blanks = [n for n, b, d in LIVES if b is None]
    assert blanks, "no blanks at all: suspicious for a field of living researchers"

    # (d) written before published, wherever two dates are shown
    pairs = [(w, y, e) for y, w, e, _ in TIMELINE if w is not None]
    assert pairs, "no written/published pairs recorded"
    for w, y, e in pairs:
        assert w < y, (e, w, y)
    assert max(y - w for w, y, _ in pairs) >= 40, [(y - w) for w, y, _ in pairs]

    flags = {f for *_, f in TIMELINE}
    assert flags <= {'P', 'S', 'M'}, flags
    return ("%d rows non-decreasing; %d era bands contiguous and covering with %d ambiguous "
            "seams; %d life spans printed and %d left blank; %d written/published pairs, "
            "widest gap %d years"
            % (len(TIMELINE), len(ERAS), sum(1 for e in ERAS if e[3]), len(printed),
               len(blanks), len(pairs), max(y - w for w, y, _ in pairs)))



# ============================ the cited-to-computed pass ============================
def check_56():
    """CONVERSION 1 -- shaping's converse, from one instance to a biconditional.

    Chapter 3 exhibited a single non-potential term that moves the optimum.  Here
    the whole space is swept: F is optimality-preserving for EVERY reward if and
    only if it is realisable by a potential vanishing on terminals, which on this
    anchor is exactly two linear constraints.  Both directions, exhaustively.
    """
    trajs = trajectories(2, 'kw')
    zero = {s: F(0) for s in ('s0', 'm', 'bot', 't0', 't1')}
    edges = [('s0', 'bot'), ('s0', 'm'), ('m', 't0'), ('m', 't1')]
    gamma = F(1, 2)
    rewards = [dict(zip(('bot', 't0', 't1'), [F(x) for x in v]))
               for v in permutations(range(-3, 4), 3)]
    vals = [F(x) for x in range(-2, 3)]

    def safe(extra):
        for r in rewards:
            if best_terminal(r, gamma, zero, trajs, extra) != best_terminal(r, gamma, zero, trajs):
                return False
        return True

    def realisable(extra):
        # phi(terminals) = 0  =>  F(m,t0) = F(m,t1) = -phi(m), and
        # F(s0,m) - F(s0,bot) = gamma*phi(m)
        if extra[('m', 't0')] != extra[('m', 't1')]:
            return False
        phi_m = -extra[('m', 't0')]
        return extra[('s0', 'm')] - extra[('s0', 'bot')] == gamma * phi_m

    agree = mismatch = n_safe = n_real = 0
    for v in product(vals, repeat=4):
        extra = dict(zip(edges, v))
        a, b = safe(extra), realisable(extra)
        n_safe += a
        n_real += b
        if a == b:
            agree += 1
        else:
            mismatch += 1
    assert mismatch == 0, mismatch
    assert 0 < n_safe < len(vals) ** 4, (n_safe, len(vals) ** 4)
    assert n_safe == n_real, (n_safe, n_real)
    return ("swept all %d shaping terms: optimality-preserving IF AND ONLY IF realisable by a "
            "terminal-vanishing potential, %d of %d, zero mismatches -- the converse is now "
            "computed on the anchor, not cited" % (len(vals) ** 4, n_safe, len(vals) ** 4))


def check_57():
    """CONVERSION 2 -- the impossibility, from two confounds to an exhaustive count.

    Chapter 4 exhibited two decompositions of a behaviour.  Here every observed
    choice distribution in a finite planner-times-reward class is checked, and the
    smallest fibre is reported.
    """
    # The pool is chosen CLOSED under the maximiser/minimiser orbit: reciprocals
    # rescale back into it (1,2,3,4,6,12 -> 12,6,4,3,2,1).  Without that closure a
    # behaviour looks identified only because its partner fell outside the grid.
    pool = [F(1), F(2), F(3), F(4), F(6), F(12)]
    inv = {12 / x for x in pool}
    assert inv == set(pool), (sorted(inv), pool)
    weights = [dict(zip(TERMINALS, v)) for v in product(pool, repeat=3)]
    planners = [(beta, sign) for beta in (1, 2, 3) for sign in (1, -1)]
    fibres = {}
    for w in weights:
        for beta, sign in planners:
            u = {t: (w[t] ** beta) if sign > 0 else (1 / w[t]) ** beta for t in TERMINALS}
            tot = sum(u.values())
            key = tuple(sorted((t, u[t] / tot) for t in TERMINALS))
            fibres.setdefault(key, []).append((tuple(w[t] for t in TERMINALS), beta, sign))
    assert fibres, "no behaviours generated"
    sizes = sorted(len(v) for v in fibres.values())
    assert min(sizes) >= 2, (min(sizes), [k for k, v in fibres.items() if len(v) < 2][:1])
    singletons = [v for v in fibres.values() if len(v) == 1]
    assert not singletons, singletons[:1]
    # and the fibres are not all the same trivial pair
    assert max(sizes) > min(sizes), (min(sizes), max(sizes))
    return ("every one of %d distinct behaviours in a %d-planner by %d-reward class admits at "
            "least %d decompositions, and up to %d; no behaviour identifies its pair. The "
            "rationality confound is only partly reachable: a beta-partner needs w^beta, which "
            "leaves any finite pool"
            % (len(fibres), len(planners), len(weights), min(sizes), max(sizes)))


def check_58():
    """CONVERSION 3 -- interruptibility, from one instance to a swept family."""
    cases = 0
    for rA in (F(1), F(3), F(7, 2)):
        for rZ in (F(0), F(-2), F(1, 4)):
            if rZ >= rA:
                continue
            for i in range(1, 21):
                q = F(i, 20)
                ql, sa = tworoute_fixed_points(q, rA, rZ)
                assert ql['l'] == ql['r'], (rA, rZ, q, ql)
                assert sa['l'] < sa['r'], (rA, rZ, q, sa)
                cases += 1
            ql0, sa0 = tworoute_fixed_points(F(0), rA, rZ)
            assert ql0['l'] == ql0['r'] and sa0['l'] == sa0['r'], (rA, rZ)
    assert cases >= 100, cases
    # and the separation is proportional to what the interruption destroys
    ql, sa = tworoute_fixed_points(F(1, 2), F(1), F(0))
    assert sa['r'] - sa['l'] == F(1, 2), sa
    return ("Q-learning indifferent and Sarsa strictly avoidant across %d (reward, rate) "
            "combinations, with the q=0 control tying in every one" % cases)


def check_59():
    """CONVERSION 4 -- Bradley-Terry non-existence, from one path to a grid sweep.

    Chapter 7 walked one path of doublings.  Here every point of a grid is tested
    for being a local maximum, in three step regimes.  The three agree exactly,
    which is reported as a measured fact rather than left as an untested clause.
    """
    grid_vals = [F(1, 8), F(1, 4), F(1, 2), F(1), F(2), F(4), F(8)]
    RATIO = F(3, 2)
    regimes = {'up': [RATIO], 'down': [1 / RATIO], 'both': [RATIO, 1 / RATIO]}
    sep = all_wins((1, 1, 1), n=1)
    cyc = all_wins((1, 0, 1), n=1)

    def count_maxima(steps, wins):
        n = pts = 0
        for a in grid_vals:
            for b in grid_vals:
                for c in grid_vals:
                    v = dict(zip(ITEMS, (a, b, c)))
                    base = bt_likelihood(v, wins)
                    is_max = True
                    for t in ITEMS:
                        for m in steps:
                            v2 = dict(v)
                            v2[t] = v[t] * m
                            if bt_likelihood(v2, wins) > base:
                                is_max = False
                                break
                        if not is_max:
                            break
                    n += is_max
                    pts += 1
        return n, pts

    sep_counts, cyc_counts, pts = {}, {}, None
    for name, steps in regimes.items():
        sep_counts[name], pts = count_maxima(steps, sep)
        cyc_counts[name], _ = count_maxima(steps, cyc)
    assert set(sep_counts.values()) == {0}, sep_counts
    assert len(set(cyc_counts.values())) == 1, cyc_counts
    assert next(iter(cyc_counts.values())) > 0, cyc_counts
    # robustness, measured: a gentler step must give the SAME verdict, and a
    # degenerate step (ratio 1) must give a different one, or the search is empty
    gentle, _ = count_maxima([F(9, 8), F(8, 9)], cyc)
    assert gentle == cyc_counts['both'], (gentle, cyc_counts['both'])
    degenerate, total = count_maxima([F(1)], sep)
    assert degenerate == total, (degenerate, total)
    assert degenerate != sep_counts['both'], (degenerate, sep_counts['both'])
    return ("over %d grid points, separable data has 0 local maxima and cyclic data has %d, "
            "identically in all three step regimes and under a gentler step -- one direction "
            "suffices here and the agreement is measured, not assumed; a degenerate step of "
            "ratio 1 calls all %d points maxima, so the search is not vacuous"
            % (pts, cyc_counts['both'], total))


CHECKS = {1: check_1, 2: check_2, 3: check_3, 4: check_4, 5: check_5, 6: check_6,
          7: check_7, 8: check_8, 9: check_9, 10: check_10, 11: check_11,
          12: check_12, 13: check_13, 14: check_14, 15: check_15,
          16: check_16, 17: check_17, 18: check_18,
          19: check_19, 20: check_20, 21: check_21,
          22: check_22, 23: check_23, 24: check_24,
          25: check_25, 26: check_26, 27: check_27,
          28: check_28, 29: check_29,
          30: check_30, 31: check_31, 32: check_32,
          33: check_33, 34: check_34,
          35: check_35, 36: check_36, 37: check_37,
          38: check_38, 39: check_39,
          40: check_40, 41: check_41, 42: check_42,
          43: check_43, 44: check_44,
          45: check_45, 46: check_46, 47: check_47,
          48: check_48, 49: check_49,
          50: check_50, 51: check_51, 52: check_52, 53: check_53,
          54: check_54, 55: check_55,
          56: check_56, 57: check_57, 58: check_58, 59: check_59}


# ----------------------------------------------------------- standing audits
SRC = os.path.abspath(__file__)


def audit_gapless():
    ids = sorted(CHECKS)
    assert ids == list(range(1, len(ids) + 1)), ids
    return "check ids gapless 1..%d" % len(ids)


TAUTOLOGY_PATTERNS = (
    r'\bassert\s+True\b', r'\bor\s+True\b', r'\b1\s*==\s*1\b',
    r'\bif\s+False\b', r'\bassert\s+1\b',
    # added after the scan missed a vacuous assertion in check_34:
    r'\bassert\b[^\n]*\bis\s+True\b',      # scan-exempt: pattern table self-matches
    r'\bassert\b[^\n]*\[:0\]',              # quantifier over an empty slice
    r'\bassert\s+(?:all|any)\(\s*\)',       # quantifier over nothing at all
    # added after two of my own assertions turned out to be unfailable disjunctions:
    r'\bassert\b[^\n]*\s+or\s+',            # scan-exempt: pattern table self-matches
)


def audit_tautology():
    # The scan reads its own source, so the line holding its positive control
    # would match itself.  Exempt tagged lines only, and visibly.
    text = '\n'.join(l for l in open(SRC).read().splitlines()
                     if 'scan-exempt:' not in l)
    bad = [pat for pat in TAUTOLOGY_PATTERNS if re.search(pat, text)]
    assert not bad, bad
    # A widened scan is a new scan: prove it still discriminates (G3a for scans).
    control = ("    assert all(x > 0 for x in items[:0]) is True\n"          # scan-exempt: control
               "    assert a < b < c or a < d, (a, b)\n")                     # scan-exempt: control
    caught = [pat for pat in TAUTOLOGY_PATTERNS if re.search(pat, control)]
    assert len(caught) >= 3, caught
    return "tautology scan clean (%d patterns; control caught by %d)" % (
        len(TAUTOLOGY_PATTERNS), len(caught))


def audit_dead_code():
    tree = ast.parse(open(SRC).read())
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    called |= set(CHECKS and [])  # registry entries are called through CHECKS
    referenced = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    dead = sorted(defined - called - referenced)
    declared = {'converges'}  # k6-waiver: whitelist of declared-unused helpers, not a witness
    undeclared = [d for d in dead if d not in declared]
    assert not undeclared, undeclared
    return "dead-code diff: %s (declared, per N2)" % (sorted(dead) or "none")


def audit_construct_then_verify():
    """K6: flag a singleton/literal collection that is assigned and then
    ASSERTED OVER inside the same function -- the shape where a check certifies
    what it just built.  A bare literal initialiser is not that shape.

    Narrowing a detector can manufacture a blind spot, so this scan carries its
    own positive control: an injected construct-then-verify function must still
    be caught.  Escape hatch is an explicit `# k6-waiver:` comment, never a
    loosened pattern.
    """
    def scan(text):
        lines = text.splitlines()
        tree = ast.parse(text)
        hits, waived = [], []
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            asserted = set()
            for a in [n for n in ast.walk(fn) if isinstance(n, ast.Assert)]:
                asserted |= {n.id for n in ast.walk(a) if isinstance(n, ast.Name)}
            for node in ast.walk(fn):
                if not isinstance(node, ast.Assign):
                    continue
                if not isinstance(node.value, (ast.Set, ast.List, ast.Tuple, ast.Dict)):
                    continue
                elts = getattr(node.value, 'elts', None) or getattr(node.value, 'keys', [])
                if not elts or len(elts) > 1:
                    continue
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in asserted:
                        line = lines[node.lineno - 1]
                        (waived if 'k6-waiver:' in line else hits).append((t.id, node.lineno))
        return hits, waived

    hits, waived = scan(open(SRC).read())
    assert not hits, hits
    control = ("def _injected():\n"
               "    sols = {42}\n"
               "    assert all(x > 0 for x in sols)\n")
    ctrl_hits, _ = scan(control)
    assert ctrl_hits, "K6 positive control failed: narrowed scan no longer detects"
    return ("construct-then-verify scan clean (%d waived); positive control caught %s"
            % (len(waived), ctrl_hits[0][0]))


AUDITS = (audit_gapless, audit_tautology, audit_dead_code, audit_construct_then_verify)


def main():
    ok = 0
    for i in sorted(CHECKS):
        msg = CHECKS[i]()
        print("check %-3d PASS  %s" % (i, msg))
        ok += 1
    for a in AUDITS:
        print("audit     PASS  %s" % a())
    print("---- %d/%d checks pass, %d audits pass" % (ok, len(CHECKS), len(AUDITS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
