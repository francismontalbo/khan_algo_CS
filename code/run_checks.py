"""Reproduce proof-oriented checks. No timing or real Montage result is claimed."""
from __future__ import annotations
import argparse
import itertools
import json
import platform
import random
from datetime import date
from pathlib import Path
from workflow_methods import (File, Workflow, Group, Budget, certify_later,
    per_file_groups, aggregate_equal, reduce_consumers, direct_certificates,
    incremental, recompute, valid_order, peak_retained_bytes)


def fixture(kind: str) -> Workflow:
    if kind == "different consumer sets":
        succ = tuple((4+2*i, 5+2*i) for i in range(4)) + ((),)*8
        return Workflow(succ, tuple(File(f"f{i}", i,
                frozenset((4+2*i, 5+2*i)), i+4) for i in range(4)))
    succ = ((4,5),)*4 + (((5,),()) if kind == "ordered consumers" else ((),()))
    return Workflow(succ, tuple(File(f"f{i}", i, frozenset((4,5)), i+4)
                               for i in range(4)))


def random_workflow(seed: int) -> Workflow:
    rng = random.Random(seed)
    n = rng.randint(2, 18)
    labels = list(range(n))
    rng.shuffle(labels)  # IDs do not encode the topological order.
    succ = [set() for _ in range(n)]
    for i, u in enumerate(labels):
        for v in labels[i+1:]:
            if rng.random() < 0.16:
                succ[u].add(v)
    files: list[File] = []
    for j in range(rng.randint(n, 3*n)):
        p_pos = rng.randrange(n)
        p = labels[p_pos]
        choices = labels[p_pos+1:]
        cs = frozenset(v for v in choices if rng.random() < 0.40)
        if files and rng.random() < 0.23:
            # Deliberately oversample equal consumers for boundary coverage.
            cs = frozenset(v for v in rng.choice(files).consumers if v in choices)
        succ[p].update(cs)  # Preserve every producer-before-consumer condition.
        files.append(File(f"f{j}", p, cs, rng.choice((0,1,2,5,11,29))))
    files.append(File("external_input", None, frozenset(labels[::2]), 97))
    return Workflow(tuple(tuple(sorted(s)) for s in succ), tuple(files))


def compare(w: Workflow) -> dict:
    w.validate()
    oracle = recompute(w)
    base = per_file_groups(w)
    plans = {
        "per_file": (base, 0),
        "equal_consumers": (aggregate_equal(base), 0),
    }
    direct = direct_certificates(w, base)
    plans["direct_certificates"] = (direct.groups, direct.inspections)
    for budget in (0, 2, 8, 32, None):
        plan = reduce_consumers(w, base, budget)
        if budget is not None:
            assert plan.inspections <= budget
        for g_id, path in plan.witnesses:
            cs = base[g_id].consumers
            assert path[0] in cs and path[-1] in cs and path[0] != path[-1]
            assert all(v in w.successors[u] for u, v in zip(path, path[1:]))
        name = "full_maximal" if budget is None else f"budget_{budget}"
        plans[name] = (plan.groups, plan.inspections)
    results = {}
    for name, (groups, scans) in plans.items():
        actual = incremental(w, groups, audit=True)
        assert actual.order == oracle.order, (name, "different order")
        assert actual.ready_scores == oracle.ready_scores, (name, "different ready scores")
        assert valid_order(w, actual.order)
        expected_d = sum(max(0, len(g.consumers)-1) for g in groups)
        expected_visits = sum(len(g.consumers) for g in groups if len(g.consumers)>1)
        assert actual.counter_decrements == expected_d
        assert actual.counter_visits == expected_visits
        assert actual.queue_refreshes <= sum(len(g.consumers)>1 for g in groups)
        results[name] = {
            "counter_decrements": actual.counter_decrements,
            "counter_visits": actual.counter_visits,
            "search_edge_inspections": scans,
            "queue_refreshes": actual.queue_refreshes,
            "order": actual.order,
        }
    return results


def exhaustive_cover_check() -> dict:
    """All 64 forward-edge DAGs on four consumers; all valid set reductions.

    For each graph, every nonempty C, every nonempty S subset C covering C by
    reachability, and every downward-closed completed set D are checked. Tests
    evaluate every ready vertex. This is finite evidence, not a universal proof.
    """
    n = 4
    universe = set(range(n))
    arcs = [(u,v) for u in range(n) for v in range(u+1,n)]
    triples = checks = reductions = 0
    for mask in range(1 << len(arcs)):
        edges = [e for j,e in enumerate(arcs) if mask & (1 << j)]
        reach = [set() for _ in range(n)]
        for u,v in edges:
            reach[u].add(v)
        for u in reversed(range(n)):
            for v in tuple(reach[u]):
                reach[u].update(reach[v])
        states = []
        for bits in range(1 << n):
            done = {v for v in range(n) if bits & (1 << v)}
            if any(v in done and u not in done for u,v in edges):
                continue
            ready = {v for v in universe-done
                     if all(u in done for u,x in edges if x == v)}
            states.append((done,ready))
        for c_bits in range(1, 1 << n):
            cs = {v for v in universe if c_bits & (1 << v)}
            for s_bits in range(1, 1 << n):
                kept = {v for v in universe if s_bits & (1 << v)}
                if not kept <= cs:
                    continue
                if any(not (reach[c] & kept) for c in cs-kept):
                    continue
                reductions += 1
                for done,ready in states:
                    triples += 1
                    for v in ready:
                        original = v in cs and cs-done == {v}
                        reduced = v in kept and kept-done == {v}
                        assert original == reduced
                        checks += 1
    return {"forward_edge_graphs":64, "consumer_set_reductions":reductions,
            "completed_set_configurations":triples,
            "ready_credit_equalities_checked":checks, "passed":True}


def negative_controls() -> dict:
    # Equal cardinalities do not justify grouping different consumer identities.
    w = Workflow(((1,2,3),(),(),()), (
        File("f",0,frozenset((1,2)),10),
        File("g",0,frozenset((1,3)),20)))
    good = recompute(w)
    bad = incremental(w,(Group(frozenset((1,2)),30),),audit=True)
    assert bad.ready_scores != good.ready_scores
    # Deleting an unrelated consumer can keep the order valid but change policy.
    w2 = Workflow(((1,2),(),()),(File("x",0,frozenset((1,2)),8),))
    good2 = recompute(w2)
    bad2 = incremental(w2,(Group(frozenset((2,)),8),),audit=True)
    assert good2.order != bad2.order and valid_order(w2,bad2.order)
    # A bounded search genuinely returns UNKNOWN when the path exceeds budget.
    succ = ((1,), (2,), ())
    r = certify_later(0,frozenset((0,2)),succ,Budget(1))
    assert r.status == "UNKNOWN"
    r2 = certify_later(0,frozenset((0,2)),succ,Budget(2))
    assert r2.status == "FOUND" and r2.path == (0,1,2)
    rejected = 0
    for invalid in (Workflow(((1,),(0,)),()),
                    Workflow(((),()),(File("missing",0,frozenset((1,)),3),))):
        try:
            invalid.validate()
        except ValueError:
            rejected += 1
    assert rejected == 2
    return {"equal_count_wrong_grouping_detected":True,
            "uncertified_deletion_changes_order":True,
            "valid_order_alone_is_insufficient":True,
            "budget_exhaustion_is_unknown":True,
            "cycle_and_missing_data_dependency_rejected":True}


def greedy_counterexample() -> dict:
    # A produces a retained final file of size 1. B produces a temporary file
    # of size 2 used by C. C produces another retained final file of size 1.
    w = Workflow(((),(2,),()),(
        File("final_A",0,frozenset(),1),
        File("temporary_B",1,frozenset((2,)),2),
        File("final_C",2,frozenset(),1)))
    w.validate()
    greedy = recompute(w).order
    candidates = [(peak_retained_bytes(w,tuple(p)),tuple(p))
                  for p in itertools.permutations(range(w.n))
                  if valid_order(w,tuple(p))]
    optimum = min(candidates)
    peak = peak_retained_bytes(w,greedy)
    assert greedy == (0,1,2) and peak == 4 and optimum[0] == 3
    return {"greedy_order":greedy, "greedy_peak":peak,
            "best_order":optimum[1], "optimal_peak":optimum[0],
            "valid_orders_enumerated":len(candidates),
            "all_order_peaks":candidates,
            "model":"synthetic retained bytes; allocate outputs before input release"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases",type=int,default=5000)
    p.add_argument("--out",type=Path,default=Path(__file__).resolve().parents[1]/"output/ci/proof-checks.json")
    args = p.parse_args()
    if args.cases < 1:
        p.error("cases must be positive")
    examples = {name:compare(fixture(name)) for name in
                ("different consumer sets","independent equal consumers","ordered consumers")}
    exhaustive = exhaustive_cover_check()
    negative = negative_controls()
    counterexample = greedy_counterexample()
    for seed in range(args.cases):
        compare(random_workflow(seed))
    compare(Workflow((),()))
    result = {"run_date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).date().isoformat(), "python":platform.python_version(),
              "random_workflows":args.cases, "seeds":[0,args.cases-1],
              "tasks_per_random_workflow":[2,18],
              "incremental_variants_per_workflow":8,
              "all_ready_scores_and_orders_equal":True,
              "exhaustive_cover_checks":exhaustive,
              "negative_controls":negative,
              "fixtures":examples,"greedy_counterexample":counterexample,
              "runtime_speedup_measured":False,"montage_benchmark_run":False,
              "notes":["New run of this companion's implementation, not a copied prior result.",
                       "Same workflows reused across variants; not independent datasets.",
                       "Counter decrements stop at one, unlike the previous eight-versus-two examples.",
                       "Grouping opportunities intentionally overrepresented in random correctness tests."]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="fixtures"},indent=2))
if __name__ == "__main__":
    main()
