"""Exact priority-maintenance comparisons for fixed sequential workflow DAGs.

Independent educational implementations, not ports of XLA or Pegasus. All
reductions modify scheduling metadata only; no physical dependency is removed.
Python 3.10+; standard library only. See the accompanying proof/code companion.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Iterable

@dataclass(frozen=True)
class File:
    name: str
    producer: int | None
    consumers: frozenset[int]
    size: int

@dataclass(frozen=True)
class Workflow:
    successors: tuple[tuple[int, ...], ...]
    files: tuple[File, ...]

    @property
    def n(self) -> int:
        return len(self.successors)

    def validate(self) -> None:
        """Shared input validation; report separately from method preparation."""
        names: set[str] = set()
        for u, row in enumerate(self.successors):
            if len(row) != len(set(row)):
                raise ValueError(f"duplicate dependency from task {u}")
            if any(type(v) is not int or not 0 <= v < self.n or v == u for v in row):
                raise ValueError("invalid dependency endpoint")
        fifo_kahn(self.successors)  # Rejects cycles.
        reached: dict[int, set[int]] = {}
        for f in self.files:
            if not isinstance(f.name, str) or f.name in names:
                raise ValueError("file names must be distinct strings")
            names.add(f.name)
            if type(f.size) is not int or f.size < 0:
                raise ValueError("file size must be a nonnegative integer")
            if any(type(c) is not int or not 0 <= c < self.n for c in f.consumers):
                raise ValueError("invalid file consumer")
            p = f.producer
            if p is None:  # External input, excluded from release credit.
                continue
            if type(p) is not int or not 0 <= p < self.n:
                raise ValueError("invalid file producer")
            if p not in reached:
                seen: set[int] = set()
                todo = [p]
                while todo:
                    for v in self.successors[todo.pop()]:
                        if v not in seen:
                            seen.add(v)
                            todo.append(v)
                reached[p] = seen
            if not f.consumers <= reached[p]:
                raise ValueError("a producer must precede each of its consumers")


def indegrees(successors: tuple[tuple[int, ...], ...]) -> list[int]:
    degree = [0] * len(successors)
    for row in successors:
        for v in row:
            degree[v] += 1
    return degree


def fifo_kahn(successors: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    """P1: source removal. Input rows must contain valid, unique endpoints."""
    degree = indegrees(successors)
    ready = deque(v for v, d in enumerate(degree) if d == 0)
    order: list[int] = []
    while ready:
        u = ready.popleft()                 # P1a: eligible task only
        order.append(u)
        for v in successors[u]:
            degree[v] -= 1                 # P1b: one removed predecessor
            if degree[v] == 0:
                ready.append(v)
    if len(order) != len(successors):
        raise ValueError("cycle detected")
    return tuple(order)


def creation_cost(w: Workflow) -> list[int]:
    """Keep costs at original producers, including retained final outputs."""
    out = [0] * w.n
    for f in w.files:
        if f.producer is not None:
            out[f.producer] += f.size
    return out


def full_scores(w: Workflow, done: set[int], ready: Iterable[int],
                produced_bytes: list[int]) -> dict[int, int]:
    """P2: independent recomputation from ORIGINAL consumer sets."""
    score = {v: -produced_bytes[v] for v in ready}
    for f in w.files:
        if f.producer is None or not f.consumers or f.size == 0:
            continue
        remaining = f.consumers - done
        if len(remaining) == 1:
            v = next(iter(remaining))
            if v in score:
                score[v] += f.size
    return score

@dataclass
class Run:
    order: tuple[int, ...]
    ready_scores: tuple[dict[int, int], ...]
    counter_decrements: int = 0
    counter_visits: int = 0
    queue_refreshes: int = 0
    heap_pushes: int = 0
    stale_pops: int = 0


def recompute(w: Workflow) -> Run:
    """P2 reference policy; used as a correctness oracle, not the main rival."""
    degree = indegrees(w.successors)
    ready = {v for v, d in enumerate(degree) if d == 0}
    cost = creation_cost(w)
    done: set[int] = set()
    order: list[int] = []
    states: list[dict[int, int]] = []
    while ready:
        scores = full_scores(w, done, ready, cost)
        states.append(scores)
        u = min(ready, key=lambda v: (-scores[v], v))
        ready.remove(u)
        done.add(u)
        order.append(u)
        for v in w.successors[u]:
            degree[v] -= 1
            if degree[v] == 0:
                ready.add(v)
    if len(order) != w.n:
        raise ValueError("cycle detected")
    return Run(tuple(order), tuple(states))

@dataclass(frozen=True)
class Group:
    consumers: frozenset[int]
    weight: int


def per_file_groups(w: Workflow) -> tuple[Group, ...]:
    """Zero-byte files have no score effect; omit them in EVERY implementation."""
    return tuple(Group(f.consumers, f.size) for f in w.files
                 if f.producer is not None and f.consumers and f.size > 0)


def aggregate_equal(groups: tuple[Group, ...]) -> tuple[Group, ...]:
    """P4: equal consumer IDENTITIES, never merely equal cardinalities."""
    total: dict[frozenset[int], int] = {}
    for g in groups:
        total[g.consumers] = total.get(g.consumers, 0) + g.weight
    return tuple(Group(consumers, weight) for consumers, weight in total.items())


def incremental(w: Workflow, groups: tuple[Group, ...], audit: bool = True) -> Run:
    """P3: exact ready scores, one shared queue engine for ALL reductions.

    Singleton groups use static credits. A dynamic counter stops at one because
    no further decrement can change an unfinished task's release priority.
    XOR identifies the remaining task without repeatedly scanning consumers.
    """
    score = [-x for x in creation_cost(w)]
    incident: list[list[int]] = [[] for _ in range(w.n)]
    count: list[int] = []
    remaining_xor: list[int] = []
    weights: list[int] = []
    for g in groups:
        if not g.consumers or g.weight <= 0:
            raise ValueError("groups must have consumers and positive weight")
        if len(g.consumers) == 1:           # P3a: static sole-consumer credit
            score[next(iter(g.consumers))] += g.weight
            continue
        k = len(count)
        count.append(len(g.consumers))
        weights.append(g.weight)
        code = 0
        for v in g.consumers:
            code ^= v
            incident[v].append(k)
        remaining_xor.append(code)

    degree = indegrees(w.successors)
    ready = {v for v, d in enumerate(degree) if d == 0}
    version = [0] * w.n
    heap: list[tuple[int, int, int]] = []
    pushes = refreshes = stale = visits = decrements = 0
    def push(v: int) -> None:
        nonlocal pushes
        version[v] += 1
        heappush(heap, (-score[v], v, version[v]))
        pushes += 1
    for v in ready:
        push(v)
    order: list[int] = []
    states: list[dict[int, int]] = []
    while ready:
        if audit:
            states.append({v: score[v] for v in ready})
        while heap:
            neg_score, u, stamp = heappop(heap)
            if u in ready and stamp == version[u]:
                break
            stale += 1
        else:
            raise AssertionError("ready set has no valid heap entry")
        ready.remove(u)
        order.append(u)
        dirty: set[int] = set()
        for k in incident[u]:
            visits += 1
            if count[k] == 1:              # P3b: terminal state, no decrement
                continue
            count[k] -= 1
            remaining_xor[k] ^= u
            decrements += 1
            if count[k] == 1:              # P3c: the only score-changing event
                v = remaining_xor[k]
                score[v] += weights[k]
                if v in ready:
                    dirty.add(v)
        for v in w.successors[u]:
            degree[v] -= 1
            if degree[v] == 0:
                ready.add(v)
                push(v)                   # Newly ready: initialize once
        for v in dirty:                   # P3d: at most one refresh per task
            push(v)
            refreshes += 1
    if len(order) != w.n:
        raise ValueError("cycle detected")
    return Run(tuple(order), tuple(states), decrements, visits,
               refreshes, pushes, stale)

@dataclass
class Budget:
    limit: int | None
    used: int = 0

    def charge_edge(self) -> bool:
        if self.limit is not None and self.used >= self.limit:
            return False
        self.used += 1
        return True

@dataclass(frozen=True)
class SearchResult:
    status: str                   # FOUND, ABSENT, or UNKNOWN
    path: tuple[int, ...] = ()


def certify_later(start: int, consumers: frozenset[int],
                  successors: tuple[tuple[int, ...], ...],
                  budget: Budget) -> SearchResult:
    """P6: FOUND contains an actual path to another consumer.

    UNKNOWN means the global edge-inspection budget was exhausted. It is NOT
    evidence that a path is absent. No adjacency list is copied before charging.
    """
    todo = deque([start])
    parent: dict[int, int | None] = {start: None}
    while todo:
        u = todo.popleft()
        for v in successors[u]:
            if not budget.charge_edge():
                return SearchResult("UNKNOWN")
            if v in parent:
                continue
            parent[v] = u
            if v in consumers:
                path = [v]
                x = u
                while x != start:
                    path.append(x)
                    x = parent[x]  # type: ignore[assignment]
                path.append(start)
                return SearchResult("FOUND", tuple(reversed(path)))
            todo.append(v)
    return SearchResult("ABSENT")

@dataclass
class Plan:
    groups: tuple[Group, ...]
    inspections: int = 0
    searches: int = 0
    unknown: int = 0
    witnesses: list[tuple[int, tuple[int, ...]]] = field(default_factory=list)


def reduce_consumers(w: Workflow, groups: tuple[Group, ...],
                     edge_budget: int | None) -> Plan:
    """P5/P6: remove only consumers with a witnessed later consumer.

    With no budget, retained vertices are precedence-maximal consumers. With
    a finite budget they can be a larger set, but still cover every removed
    consumer through a chain of genuine dependency paths. Sorting and metadata
    scans incur costs in addition to the edge-inspection budget.
    """
    if edge_budget is not None and edge_budget < 0:
        raise ValueError("edge budget must be nonnegative or None")
    budget = Budget(edge_budget)
    reduced: list[Group] = []
    plan = Plan(())
    for k, g in enumerate(groups):
        kept = set(g.consumers)
        if len(kept) > 1:
            for c in sorted(g.consumers):
                if budget.limit is not None and budget.used >= budget.limit:
                    break
                plan.searches += 1
                result = certify_later(c, g.consumers, w.successors, budget)
                if result.status == "FOUND":
                    kept.remove(c)
                    plan.witnesses.append((k, result.path))
                elif result.status == "UNKNOWN":
                    plan.unknown += 1
        if not kept:
            raise AssertionError("acyclic precedence cannot eliminate all consumers")
        reduced.append(Group(frozenset(kept), g.weight))
    plan.groups = tuple(reduced)
    plan.inspections = budget.used
    return plan


def direct_certificates(w: Workflow, groups: tuple[Group, ...]) -> Plan:
    """Inexpensive comparator: only direct-edge witnesses, no transitive BFS."""
    out: list[Group] = []
    plan = Plan(())
    for k, g in enumerate(groups):
        kept = set(g.consumers)
        if len(kept) > 1:
            for c in sorted(g.consumers):
                for d in w.successors[c]:
                    plan.inspections += 1
                    if d in g.consumers:
                        kept.remove(c)
                        plan.witnesses.append((k, (c, d)))
                        break
        out.append(Group(frozenset(kept), g.weight))
    plan.groups = tuple(out)
    return plan


def valid_order(w: Workflow, order: tuple[int, ...]) -> bool:
    if len(order) != w.n or set(order) != set(range(w.n)):
        return False
    position = {v: i for i, v in enumerate(order)}
    return all(position[u] < position[v]
               for u, row in enumerate(w.successors) for v in row)


def peak_retained_bytes(w: Workflow, order: tuple[int, ...]) -> int:
    """Illustrative live-file model, not process RAM or a runtime benchmark.

    Allocate each task's outputs BEFORE releasing last-used inputs. Retain final
    outputs; omit external inputs. File aliases and internal temporaries absent.
    """
    if not valid_order(w, order):
        raise ValueError("invalid task order")
    left = [len(f.consumers) for f in w.files]
    live: set[int] = set()
    peak = 0
    for v in order:
        live.update(i for i, f in enumerate(w.files) if f.producer == v)
        peak = max(peak, sum(w.files[i].size for i in live))
        for i, f in enumerate(w.files):
            if f.producer is not None and v in f.consumers:
                if i not in live:
                    raise AssertionError("input not available")
                left[i] -= 1
                if left[i] == 0:
                    live.remove(i)
    return peak
