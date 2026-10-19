# Where these algorithms are used

The interactive guide distinguishes verified implementations, research evaluations and teaching extensions. The input examples are not production traces.

## fifo — Load website scripts in the right order

**Setting:** Django form assets  
**Evidence type:** In software

A calendar widget fails if its script runs before jQuery. Several widgets can request overlapping scripts.

Django merges ordered asset lists with Python TopologicalSorter. Ready items have no unfinished prerequisites: the Kahn source-removal pattern.

**Evidence.** Preserves required script order and warns when the requested order is cyclic. This is a correctness benefit, not a reported speedup.

**Limit.** Does not minimize page-load time or replace a browser’s script loader.

**Match.** Core source-removal mechanism verified through Django and graphlib.

**Question.** Which part would dominate for large asset lists: graph construction, duplicate handling, or ordering?

Sources:
- [Django form assets — dependency order](https://docs.djangoproject.com/en/5.2/topics/forms/media/). Official documentation. Locator: Order of assets.
- [Django Media.merge implementation](https://github.com/django/django/blob/stable/5.2.x/django/forms/widgets.py). Source code. Locator: Media.merge; TopologicalSorter import.
- [Python graphlib — topological task processing](https://docs.python.org/3/library/graphlib.html). Official documentation. Locator: TopologicalSorter; get_ready; done; static_order.
- [Kahn — Topological Sorting of Large Networks](https://doi.org/10.1145/368996.369025). Research paper. Locator: 1962 publication record.

## lifo — Finish one image branch before starting another

**Setting:** Dask local scheduling  
**Evidence type:** Documented policy

Starting every chunk first can keep many intermediate results alive.

The documented local scheduler favors recently ready tasks with a LIFO policy, helping finish existing work.

**Evidence.** Explains a practical reason to choose a stack rather than a queue among eligible tasks.

**Limit.** No minimum-memory guarantee; the entire Dask policy includes more than a stack.

**Match.** Shared ready-stack policy, not a reproduction of every Dask scheduler.

**Question.** When does this policy help data lifetime, and when does it reduce available parallelism?

Sources:
- [Dask scheduling policy](https://docs.dask.org/en/stable/scheduling-policy.html). Official documentation. Locator: Last in first out; Break ties with depth-first search.

## priority — Choose useful build work first

**Setting:** Ninja build system  
**Evidence type:** In software

Many source files are ready to compile, but some belong to longer remaining build chains.

Ninja compares ready build edges using critical-path weights and an ID tie-break.

**Evidence.** A concrete use of priority selection inside dependency-respecting execution.

**Limit.** Priority alone does not establish an optimal build time. Real resource pools and durations matter.

**Match.** The demo uses fixed illustrative scores, not Ninja’s full priority calculation.

**Question.** Can an improvement retain the same decisions while reducing the cost of maintaining the queue?

Sources:
- [Ninja critical-path priority comparator](https://github.com/ninja-build/ninja/blob/b81e306232dfa644e92145c7d2871690017969e8/src/graph.h). Pinned source code. Locator: EdgePriorityLess; critical_path_weight.
- [Ninja critical-path weight construction](https://github.com/ninja-build/ninja/blob/b81e306232dfa644e92145c7d2871690017969e8/src/build.cc). Pinned source code. Locator: Plan priority computation; reverse traversal of sorted edges.

## lexical — Produce a repeatable dependency list

**Setting:** NetworkX ordering API  
**Evidence type:** Related application

Two valid asset orders can differ just because input enumeration changed.

A lexicographical topological sort chooses a stable key among eligible nodes.

**Evidence.** Provides a documented algorithm for reproducible dependency-respecting output.

**Limit.** The website use is an adaptation. No separate production adoption or speedup was verified for this exact policy.

**Match.** Library algorithm verified; asset-manifest example is illustrative.

**Question.** Does the study need identical output, or merely any valid order? That changes its correctness target.

Sources:
- [NetworkX lexicographical topological sort](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.lexicographical_topological_sort.html). Official implementation documentation. Locator: Function behavior and examples.
- [Django form assets — dependency order](https://docs.djangoproject.com/en/5.2/topics/forms/media/). Official documentation. Locator: Order of assets.

## generations — Run a pipeline in dependency stages

**Setting:** Python graphlib and NetworkX  
**Evidence type:** Related application

A batch system must know which jobs can start before their results are consumed.

Topological generations expose layers of eligible work; graphlib separately exposes batches of currently ready tasks.

**Evidence.** Helps visualize parallel opportunities and dependency barriers.

**Limit.** Strict layers add a barrier; graphlib ready batches need not be executed as synchronous generations.

**Match.** Exact generation operation in NetworkX; practical dispatch motivation in graphlib.

**Question.** Is waiting for a whole generation necessary, or is it extra delay introduced by the executor?

Sources:
- [NetworkX topological generations](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.topological_generations.html). Official implementation documentation. Locator: Function definition.
- [Python graphlib — topological task processing](https://docs.python.org/3/library/graphlib.html). Official documentation. Locator: TopologicalSorter; get_ready; done; static_order.

## dfs — Apply database updates safely

**Setting:** Django migrations  
**Evidence type:** In software

A foreign-key update cannot run before both required tables exist.

Django uses iterative DFS to construct forward and backward migration plans.

**Evidence.** Finds prerequisites before applying a requested migration, and dependents before removing one.

**Limit.** Real migration graphs may include replaced migrations and target-specific traversal.

**Match.** DFS family verified. The example visits the whole graph, whereas Django plans around a target.

**Question.** Would a target-specific traversal avoid work that a whole-graph ordering performs unnecessarily?

Sources:
- [Django migration dependency traversal](https://github.com/django/django/blob/5.2/django/db/migrations/graph.py). Pinned release source. Locator: MigrationGraph.forwards_plan, backwards_plan, iterative_dfs.
- [Django migrations — dependencies](https://docs.djangoproject.com/en/6.0/topics/migrations/). Official documentation. Locator: Dependencies; migration graph.

## bfs — Explain a possible lock-order problem

**Setting:** Linux lockdep  
**Evidence type:** In software

Different code paths acquire locks in conflicting orders and may hang.

Linux lockdep includes breadth-first graph searches in its dependency checks.

**Evidence.** A graph path can explain the chain connecting one lock class to another.

**Limit.** Real lock modes and annotations exceed this example; finding a path is not itself proof of an observed deadlock.

**Match.** BFS routine is present in lockdep; the simplified path example is not a kernel trace.

**Question.** Can an explanation remain short without silently ignoring relevant dependency types?

Sources:
- [Linux lock dependency validator](https://docs.kernel.org/locking/lockdep-design.html). Official documentation. Locator: Dependency graph; multi-lock dependency rules.
- [Linux lockdep breadth-first search](https://github.com/torvalds/linux/blob/0fcb05b72344f40806cbe810de8872f1698bf053/kernel/locking/lockdep.c). Pinned source code. Locator: __bfs; check_noncircular.

## bounded — Keep an interactive dependency check responsive

**Setting:** Dependency-checking tools  
**Evidence type:** Teaching extension

A search may be too expensive to finish within an interactive work budget.

The demonstration limits edge inspections and preserves UNKNOWN when it has not proved an answer.

**Evidence.** Makes the cost-versus-certainty trade-off explicit.

**Limit.** No named product was verified to use this exact cutoff rule. A truncated search cannot certify no path.

**Match.** Related to dependency checks; this particular budgeted procedure is a local teaching mechanism.

**Question.** Which inexpensive certificate could avoid an unnecessary search while remaining exact?

Sources:
- [Linux lock dependency validator](https://docs.kernel.org/locking/lockdep-design.html). Official documentation. Locator: Dependency graph; multi-lock dependency rules.
- [Pearce and Kelly — A Dynamic Topological Sort Algorithm for DAGs](https://whileydave.com/publications/pk07_jea/). Author publication page. Locator: Abstract; implementations and use.

## reduction — Remove distracting arrows from a build diagram

**Setting:** Graphviz tred; Pegasus cleanup research  
**Evidence type:** In software

A diagram contains both Compile → Test → Package and an extra Compile → Package arrow.

Transitive reduction removes an edge only when another path preserves its reachability.

**Evidence.** Graphviz provides a real reduction tool; workflow research uses related dependency removal for cleanup planning.

**Limit.** Not safe when an edge has extra semantics beyond ordering. Finding redundancy can cost more than processing it.

**Match.** Graphviz operation is exact; the deployment pipeline and reference implementation are illustrative.

**Question.** How much work is worth spending to prove that an edge is redundant?

Sources:
- [Graphviz tred — transitive reduction](https://graphviz.org/docs/cli/tred/). Official tool documentation. Locator: Transitive reduction filter for directed graphs.
- [Singh et al. — Optimizing Workflow Data Footprint](https://dcc.ligo.org/public/0006/P070017/000/P070017-00.pdf). Research paper. Locator: Cleanup dependency reduction; experiments with Montage and LIGO.

## enumeration — Check all legal orders of a tiny test case

**Setting:** NetworkX exhaustive ordering  
**Evidence type:** Library operation

A new scheduler seems correct on one output, but another valid order may expose a bug or a smaller peak.

Enumerate every valid order of a small DAG and check each against the proposed invariant.

**Evidence.** Provides an exact local oracle when the graph is tiny.

**Limit.** Output count can grow factorially. This is a testing use, not a scalable production scheduler.

**Match.** Documented enumeration function; our test-fixture use is local.

**Question.** Can a tiny exhaustive counterexample disprove a broad claim before a large experiment is built?

Sources:
- [NetworkX all_topological_sorts](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.all_topological_sorts.html). Official implementation documentation. Locator: Algorithm reference to Knuth and Szwarcfiter; function output.

## critical — Identify the build chain that limits completion

**Setting:** Ninja build scheduling  
**Evidence type:** In software

Parallel compilation cannot bypass a long chain ending in the final executable.

A reverse dependency traversal computes critical-path priorities; the demo shows longest-path dynamic programming with known toy durations.

**Evidence.** Explains why critical-path information is useful to a real build tool.

**Limit.** The 10-unit toy bound assumes enough processors and no extra transfers. It is not a measured Ninja build time.

**Match.** Critical-path mechanism verified; cost assumptions are simplified.

**Question.** Are inaccurate duration estimates more important than the cost of computing the ranking?

Sources:
- [Ninja critical-path weight construction](https://github.com/ninja-build/ninja/blob/b81e306232dfa644e92145c7d2871690017969e8/src/build.cc). Pinned source code. Locator: Plan priority computation; reverse traversal of sorted edges.
- [Ninja critical-path priority comparator](https://github.com/ninja-build/ninja/blob/b81e306232dfa644e92145c7d2871690017969e8/src/graph.h). Pinned source code. Locator: EdgePriorityLess; critical_path_weight.

## insertion — Recheck a pipeline after a dependency edit

**Setting:** Dependency editors; comparison to Abseil  
**Evidence type:** Reference method

A user adds a prerequisite after a valid order has already been constructed.

Add the edge and recompute an order, rejecting the graph if a cycle appears.

**Evidence.** Simple correctness reference for evaluating a genuine incremental method.

**Limit.** Recomputes unaffected work. Abseil is evidence for the incremental problem, not adoption of this reference routine.

**Match.** A locally implemented baseline, not a product claim.

**Question.** How often are edits already consistent with the stored order, requiring no repair?

Sources:
- [Abseil GraphCycles source](https://github.com/abseil/abseil-cpp/blob/20250127.0/absl/synchronization/internal/graphcycles.cc). Pinned release source. Locator: File introduction and rank maintenance.
- [Pearce and Kelly — A Dynamic Topological Sort Algorithm for DAGs](https://whileydave.com/publications/pk07_jea/). Author publication page. Locator: Abstract; implementations and use.
- [Python graphlib — topological task processing](https://docs.python.org/3/library/graphlib.html). Official documentation. Locator: TopologicalSorter; get_ready; done; static_order.

## pk — Catch dangerous lock acquisition orders

**Setting:** Abseil GraphCycles and Mutex  
**Evidence type:** In software

A newly observed lock order may contradict a previously recorded chain.

Abseil explicitly implements Pearce–Kelly ranks and restricted repair for incremental cycle detection.

**Evidence.** Connects a named research algorithm to a concrete debugging feature in a maintained C++ library.

**Limit.** Debugging overhead remains; a potential lock-order cycle is not a guaranteed live deadlock.

**Match.** Named algorithm match verified in pinned source; demo covers core insertion repair only.

**Question.** Which affected-region shape makes local repair cheaper or more expensive than recomputation?

Sources:
- [Abseil GraphCycles source](https://github.com/abseil/abseil-cpp/blob/20250127.0/absl/synchronization/internal/graphcycles.cc). Pinned release source. Locator: File introduction and rank maintenance.
- [Abseil synchronization guide](https://abseil.io/docs/cpp/guides/synchronization). Official documentation. Locator: Deadlock detection.
- [Pearce and Kelly — A Dynamic Topological Sort Algorithm for DAGs](https://whileydave.com/publications/pk07_jea/). Author publication page. Locator: Abstract; implementations and use.

## scc — Group mutually recursive functions

**Setting:** LLVM graph utilities and compiler passes  
**Evidence type:** In software

Two functions call one another, so treating each as an independent acyclic step is incorrect.

Tarjan SCC groups vertices that can reach one another; LLVM’s generic iterator explicitly uses Tarjan.

**Evidence.** Lets compiler analyses process cycles as components rather than pretending the call graph is a DAG.

**Limit.** SCC membership alone does not prove that a function will loop forever or establish a legal task-execution order.

**Match.** Tarjan utility and CGSCC analysis context verified; the tiny call graph is illustrative.

**Question.** Can a transformation change component boundaries and invalidate cached analysis?

Sources:
- [LLVM SCCIterator source](https://llvm.org/doxygen/SCCIterator_8h_source.html). Official source documentation. Locator: File introduction.
- [LLVM new pass manager](https://llvm.org/docs/NewPassManager.html). Official documentation. Locator: Adding passes; CGSCC pass hierarchy.

## heap — Select the next event or urgent job

**Setting:** SimPy and Python heapq  
**Evidence type:** Related application

A simulation or job dispatcher repeatedly selects one pending item, sometimes after its priority changes.

Heap queues support inexpensive selection; invalidated entries can be skipped when removed.

**Evidence.** SimPy documents a time-ordered heap; Python documents changed-priority handling.

**Limit.** The demo’s max-priority jobs and version stamps are not SimPy’s exact time-based event loop.

**Match.** Heap usage verified; mutable-priority demonstration is independently written.

**Question.** Do stale entries accumulate enough to outweigh the benefit of avoiding in-place updates?

Sources:
- [Python heapq — changing task priorities](https://docs.python.org/3/library/heapq.html). Official documentation. Locator: Priority Queue Implementation Notes.
- [SimPy — time and scheduling](https://simpy.readthedocs.io/en/latest/topical_guides/time_and_scheduling.html). Official documentation. Locator: SimPy events and time.

## fullscore — Check a storage-aware task ordering

**Setting:** XLA scheduling as the practical reference  
**Evidence type:** Reference method

A compiler must choose among instructions whose intermediates consume memory.

The local oracle recomputes released bytes minus created bytes for every ready task.

**Evidence.** Provides a straightforward check of the same simplified score used by the incremental demos.

**Limit.** This deliberately direct oracle is not the shipped XLA scheduler and is not the strongest runtime baseline.

**Match.** Score motivation matches XLA; full recomputation is our independent reference.

**Question.** Which oracle checks correctness without becoming an artificially weak performance competitor?

Sources:
- [XLA list memory scheduler](https://github.com/tensorflow/tensorflow/blob/v2.10.0/tensorflow/compiler/xla/service/hlo_memory_scheduler.cc). Pinned release source. Locator: ListScheduler; BytesFreedIfScheduled; CreateSchedule.
- [OpenXLA — compiler overview](https://openxla.org/xla). Official documentation. Locator: Overview.

## counters — Maintain memory-related scheduling priorities

**Setting:** XLA list memory scheduler  
**Evidence type:** In software

Recalculating every ready instruction’s release benefit repeats work after each completed instruction.

The source tracks unfinished uses and revisits affected priorities when one use remains.

**Evidence.** Verifies that the core update mechanism already has a real compiler application.

**Limit.** The file model omits aliases and special instructions. These simulations prove no compiler or inference speedup.

**Match.** Core event mechanism verified, not an exact full XLA reproduction.

**Question.** Where is the remaining cost after competent incremental updates are already implemented?

Sources:
- [XLA list memory scheduler](https://github.com/tensorflow/tensorflow/blob/v2.10.0/tensorflow/compiler/xla/service/hlo_memory_scheduler.cc). Pinned release source. Locator: ListScheduler; BytesFreedIfScheduled; CreateSchedule.
- [OpenXLA — compiler overview](https://openxla.org/xla). Official documentation. Locator: Overview.

## grouped — Avoid duplicate bookkeeping for shared image files

**Setting:** Workflow cleanup and compiler metadata context  
**Evidence type:** Teaching extension

Several files have identical consumers, so their remaining-consumer counts move together.

The local example shares counters for equal consumer sets while keeping creation costs separate.

**Evidence.** Illustrates an exact representation change relevant to data-intensive task graphs.

**Limit.** No separate deployed system was verified to use this exact grouping rule. Preprocessing may eliminate its runtime benefit.

**Match.** Related application evidence only; do not present this local variant as a published or novel algorithm.

**Question.** Does grouping still help after excluding trivially static final consumers?

Sources:
- [Singh et al. — Optimizing Workflow Data Footprint](https://dcc.ligo.org/public/0006/P070017/000/P070017-00.pdf). Research paper. Locator: Cleanup dependency reduction; experiments with Montage and LIGO.
- [XLA list memory scheduler](https://github.com/tensorflow/tensorflow/blob/v2.10.0/tensorflow/compiler/xla/service/hlo_memory_scheduler.cc). Pinned release source. Locator: ListScheduler; BytesFreedIfScheduled; CreateSchedule.
- [WfCommons Montage execution instances](https://github.com/wfcommons/WfInstances/blob/main/pegasus/montage/README.md). Benchmark documentation. Locator: Workflow tasks; execution-instance table.

## maximal — Recognize when the last file user is already known

**Setting:** Pegasus cleanup dependency reduction  
**Evidence type:** Teaching extension

A file has several users, but dependencies already force one user to finish last.

The local proof retains only consumers that may be last; singleton release credit can be fixed in advance.

**Evidence.** Shows how ordering information can replace some dynamic bookkeeping.

**Limit.** Pegasus reduces cleanup dependencies, not this exact score metadata. Reachability preprocessing is not free.

**Match.** Closely related prior structural idea, not a verified deployment of this local priority representation.

**Question.** Can the required dependency certificate be cheaper than maintaining the original counters?

Sources:
- [Singh et al. — Optimizing Workflow Data Footprint](https://dcc.ligo.org/public/0006/P070017/000/P070017-00.pdf). Research paper. Locator: Cleanup dependency reduction; experiments with Montage and LIGO.
- [Pegasus workflow data management](https://pegasus.isi.edu/documentation/reference-guide/data-management.html). Official documentation. Locator: In-place cleanup.

## lifetime — Delete temporary images only after their final use

**Setting:** Pegasus and Montage workflows  
**Evidence type:** Research and software

Large image pipelines retain temporary files and can exhaust their working storage.

Cleanup jobs and last-use reasoning release intermediates after all required consumers have finished.

**Evidence.** The 2007 study evaluates Montage and LIGO, including real execution; Pegasus documents cleanup support.

**Limit.** Staging, grouped cleanup and parallelism affect results. File bytes are not process RAM.

**Match.** Real application verified; our one-task-at-a-time replay is not a Montage execution.

**Question.** What does the trace omit, such as temporary files inside a task or data staging?

Sources:
- [Singh et al. — Optimizing Workflow Data Footprint](https://dcc.ligo.org/public/0006/P070017/000/P070017-00.pdf). Research paper. Locator: Cleanup dependency reduction; experiments with Montage and LIGO.
- [Pegasus workflow data management](https://pegasus.isi.edu/documentation/reference-guide/data-management.html). Official documentation. Locator: In-place cleanup.
- [WfCommons Montage execution instances](https://github.com/wfcommons/WfInstances/blob/main/pegasus/montage/README.md). Benchmark documentation. Locator: Workflow tasks; execution-instance table.

## heft — Assign image-processing tasks to different processors

**Setting:** HEFT-family image and video scheduling research  
**Evidence type:** Research evaluation

A filter runs faster on one processor while another operation favors a different processor.

HEFT combines dependency ranking with estimated finish-time placement on processors.

**Evidence.** PHEFT evaluates application-shaped LIGO and Montage workloads; embedded scheduling research motivates video and image use.

**Limit.** PHEFT uses simulated workloads and is a variant. No claim that a named consumer app deploys stock HEFT or that our example measures hardware.

**Match.** Core HEFT teaching model; application evidence is family-level research.

**Question.** Would a better schedule still be worthwhile after the scheduler’s own runtime is counted?

Sources:
- [Topcuoglu, Hariri and Wu — Performance-Effective and Low-Complexity Task Scheduling](https://doi.org/10.1109/71.993206). Research paper. Locator: HEFT task ranking and processor-selection phases.
- [Drozdov et al. — PHEFT: Pessimistic Image Processing Workflow Scheduling for DSP Clusters](https://www.mdpi.com/1999-4893/11/5/76). Research evaluation. Locator: Workload generation and simulation experiments.
- [Arras et al. — List Scheduling in Embedded Systems Under Memory Constraints](https://link.springer.com/article/10.1007/s10766-014-0338-1). Research paper — abstract inspected. Locator: Publisher abstract.

## sortscan — Maintain task order after a small dependency change

**Setting:** Incremental graph maintenance context  
**Evidence type:** Teaching extension

A few affected tasks may lie close together or be spread across a long order interval.

Recover their previous order by sorting affected positions or scanning the interval.

**Evidence.** Makes the two operation costs visible on the same affected set.

**Limit.** No verified deployment or originality claim for this exact switch. It is one subroutine, not a complete dynamic sorter.

**Match.** Inspired by reassignment work in incremental ordering; local mechanism only.

**Question.** Can a cheap observable condition choose a method without costing more than the choice saves?

Sources:
- [Pearce and Kelly — A Dynamic Topological Sort Algorithm for DAGs](https://whileydave.com/publications/pk07_jea/). Author publication page. Locator: Abstract; implementations and use.
- [Abseil GraphCycles source](https://github.com/abseil/abseil-cpp/blob/20250127.0/absl/synchronization/internal/graphcycles.cc). Pinned release source. Locator: File introduction and rank maintenance.

## lrc — Keep cached data that future tasks will use

**Setting:** LRC Spark research prototype  
**Evidence type:** Research prototype

A data-analysis job has limited cache space and may evict data that later tasks need.

LRC uses dependency information rather than recency alone when deciding which cached data to remove.

**Evidence.** The authors implemented and evaluated a Spark-based prototype; it is not just a hypothetical cache application.

**Limit.** Not the default policy of all Spark deployments. The demo isolates one count-based eviction, not the full distributed policy.

**Match.** Core dependency-count motivation; limited eviction demonstration.

**Question.** Is this workload limited by cache misses, or does another cost dominate?

Sources:
- [Yu et al. — LRC: Dependency-Aware Cache Management for Data Analytics Clusters](https://arxiv.org/abs/1703.08280). Research prototype. Locator: Abstract; Spark prototype.
