"""Small, independently written teaching implementations, not new algorithms.

Python 3.10+, standard library only. Vertices are integer IDs 0 .. n-1.
Adjacency lists contain successors. Parallel edges are rejected by the builder.
The examples explain prerequisites for the retained research implementations.
"""
from __future__ import annotations
from collections import deque
from heapq import heapify, heappop, heappush
from typing import Iterable, Sequence


def make_graph(n: int, edges: Iterable[tuple[int, int]]) -> list[list[int]]:
    """Build a simple directed graph in O(n + m) expected time."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    adj = [[] for _ in range(n)]
    seen: set[tuple[int, int]] = set()
    for u, v in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("Vertex outside 0 .. n-1")
        if (u, v) in seen:
            raise ValueError("Duplicate edge")
        seen.add((u, v))
        adj[u].append(v)
    return adj


def indegrees(adj: Sequence[Sequence[int]]) -> list[int]:
    degree = [0] * len(adj)
    for successors in adj:
        for v in successors:
            degree[v] += 1
    return degree


# BEGIN kahn

def kahn(adj: Sequence[Sequence[int]]) -> list[int]:
    degree = indegrees(adj)
    ready = deque(v for v, d in enumerate(degree) if d == 0)
    order = []
    while ready:
        u = ready.popleft()
        order.append(u)
        for v in adj[u]:
            degree[v] -= 1
            if degree[v] == 0:
                ready.append(v)
    if len(order) != len(adj):
        raise ValueError("The graph contains a directed cycle")
    return order
# END kahn


# BEGIN dfs

def dfs_order(adj: Sequence[Sequence[int]]) -> list[int]:
    """Recursive teaching version. Prefer an explicit stack for deep graphs."""
    color = [0] * len(adj)  # 0 unseen, 1 active, 2 finished
    finished = []

    def visit(u: int) -> None:
        color[u] = 1
        for v in adj[u]:
            if color[v] == 1:
                raise ValueError("Back edge: directed cycle")
            if color[v] == 0:
                visit(v)
        color[u] = 2
        finished.append(u)

    for u in range(len(adj)):
        if color[u] == 0:
            visit(u)
    return finished[::-1]
# END dfs


# BEGIN priority

def priority_kahn(adj: Sequence[Sequence[int]], score: Sequence[int]) -> list[int]:
    """Fixed scores only. A dynamic score needs an additional update mechanism."""
    if len(score) != len(adj):
        raise ValueError("One score is required per vertex")
    degree = indegrees(adj)
    ready = [(-score[v], v) for v, d in enumerate(degree) if d == 0]
    heapify(ready)
    order = []
    while ready:
        _, u = heappop(ready)  # highest score, then smallest vertex ID
        order.append(u)
        for v in adj[u]:
            degree[v] -= 1
            if degree[v] == 0:
                heappush(ready, (-score[v], v))
    if len(order) != len(adj):
        raise ValueError("The graph contains a directed cycle")
    return order
# END priority


# BEGIN reachability

def reachable(adj: Sequence[Sequence[int]], source: int, target: int,
              skip: tuple[int, int] | None = None) -> bool:
    """Reachability by BFS. source == target allows a length-zero path."""
    if not (0 <= source < len(adj) and 0 <= target < len(adj)):
        raise ValueError("Unknown vertex")
    seen = {source}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == target:
            return True
        for v in adj[u]:
            if (u, v) != skip and v not in seen:
                seen.add(v)
                queue.append(v)
    return False
# END reachability


# BEGIN reduction

def transitive_reduction(adj: Sequence[Sequence[int]]) -> list[list[int]]:
    """Slow but clear DAG reference: test an alternate path for each edge."""
    kahn(adj)  # reject cyclic graphs first
    reduced = [[] for _ in adj]
    for u, successors in enumerate(adj):
        for v in successors:
            if not reachable(adj, u, v, skip=(u, v)):
                reduced[u].append(v)
    return reduced
# END reduction


# BEGIN criticalpath

def earliest_finish(adj: Sequence[Sequence[int]], duration: Sequence[int]) -> list[int]:
    """Earliest finishes with unlimited processors and zero communication time."""
    if len(duration) != len(adj) or any(t < 0 for t in duration):
        raise ValueError("One nonnegative duration is required per task")
    finish = list(duration)
    for u in kahn(adj):
        for v in adj[u]:
            finish[v] = max(finish[v], finish[u] + duration[v])
    return finish
# END criticalpath


# BEGIN counter

def consumer_events(consumers: Iterable[int], completion_order: Sequence[int],
                    size: int) -> list[dict]:
    """Illustrate a single file. All initial consumers are already eligible.

    Sets make the surviving consumer visible; this is not an optimized scheduler.
    The empty-set transition is lifetime accounting, not a second credit event.
    """
    if size < 0:
        raise ValueError("Negative file size")
    remaining = set(consumers)
    if len(completion_order) != len(remaining) or set(completion_order) != remaining:
        raise ValueError("Complete each distinct consumer exactly once")
    initial = next(iter(remaining)) if len(remaining) == 1 else None
    rows = [{"finished": None, "remaining": sorted(remaining),
             "credit_to": initial, "credit": size if initial is not None else 0}]
    for u in completion_order:
        old = len(remaining)
        remaining.remove(u)
        credit_to = next(iter(remaining)) if old == 2 else None
        rows.append({"finished": u, "remaining": sorted(remaining),
                     "credit_to": credit_to, "credit": size if credit_to is not None else 0})
    return rows
# END counter


# BEGIN insertion

def insert_edge_reference(adj: Sequence[Sequence[int]], order: Sequence[int],
                          u: int, v: int) -> tuple[list[list[int]], list[int]]:
    """An insertion baseline, NOT the Pearce-Kelly algorithm.

    Accept a forward edge without reordering. Otherwise check for a cycle and
    recompute. The caller supplies a valid order; input is not mutated.
    """
    n = len(adj)
    if not (0 <= u < n and 0 <= v < n):
        raise ValueError("Unknown vertex")
    if not is_topological(adj, order):
        raise ValueError("The supplied order is invalid")
    updated = [list(row) for row in adj]
    if v in updated[u]:
        return updated, list(order)
    pos = {x: i for i, x in enumerate(order)}
    if u == v or (pos[u] >= pos[v] and reachable(adj, v, u)):
        raise ValueError("The new edge creates a cycle")
    updated[u].append(v)
    return (updated, list(order)) if pos[u] < pos[v] else (updated, kahn(updated))
# END insertion


# BEGIN validate

def is_topological(adj: Sequence[Sequence[int]], order: Sequence[int]) -> bool:
    if len(order) != len(adj) or set(order) != set(range(len(adj))):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[u] < pos[v] for u, row in enumerate(adj) for v in row)
# END validate


def traces() -> dict:
    adj = make_graph(5, [(0, 2), (1, 2), (2, 3)])
    label = lambda nodes: [chr(65 + n) for n in nodes]
    degree = indegrees(adj)
    ready = deque(v for v, d in enumerate(degree) if d == 0)
    order = []
    rows = [{"event": "Start", "ready": label(ready), "degree": list(degree), "order": []}]
    while ready:
        u = ready.popleft();order.append(u)
        for v in adj[u]:
            degree[v] -= 1
            if degree[v] == 0:ready.append(v)
        rows.append({"event": "Finish " + chr(65 + u), "ready": label(ready),
                     "degree": list(degree), "order": label(order)})
    return {"graph": "A → C, B → C, C → D; E is independent.", "kahn": rows,
            "dfs_order": label(dfs_order(adj)),
            "priority_order": label(priority_kahn(adj, [2, 5, 4, 6, 1])),
            "critical_finish": earliest_finish(adj, [2, 3, 4, 1, 2]),
            "consumer_events": consumer_events([0, 1, 2], [0, 1, 2], 8)}


if __name__ == "__main__":
    import json
    print(json.dumps(traces(), indent=2))
