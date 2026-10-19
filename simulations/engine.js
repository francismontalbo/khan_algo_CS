/* Algorithm simulations. Independent educational implementations, 2026-10-15.
 * emit() records immutable display frames. Rendering costs are NOT benchmarks.
 * Every displayed example is synthetic, never a recorded Montage timing result.
 * Works in the browser and Node.js. No external dependencies.
 */
(function (root) {
    'use strict';
    const clone = x => JSON.parse(JSON.stringify(x));
    const dictionary = (entries = []) => Object.assign(Object.create(null), Object.fromEntries(entries));
    const hasOwn = (object, key) => object != null && Object.prototype.hasOwnProperty.call(object, key);
    const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;
    const lex = (a, b) => { for (let i = 0; i < Math.min(a.length, b.length); i++) {
        const c = compare(a[i], b[i]);
        if (c)
            return c;
    } return a.length - b.length; };
    class MinHeap {
        constructor() { this.a = []; }
        get size() { return this.a.length; }
        push(x) { let i = this.a.length; this.a.push(x); while (i) {
            const p = (i - 1) >> 1;
            if (lex(this.a[p], x) <= 0)
                break;
            this.a[i] = this.a[p];
            i = p;
        } this.a[i] = x; }
        pop() { if (!this.a.length)
            return null; const first = this.a[0], last = this.a.pop(); if (this.a.length) {
            let i = 0;
            while (i * 2 + 1 < this.a.length) {
                let c = i * 2 + 1;
                if (c + 1 < this.a.length && lex(this.a[c + 1], this.a[c]) < 0)
                    c++;
                if (lex(last, this.a[c]) <= 0)
                    break;
                this.a[i] = this.a[c];
                i = c;
            }
            this.a[i] = last;
        } return first; }
    }
    function graph(input) {
        const nodes = input.nodes, edges = input.edges;
        if (!Array.isArray(nodes) || nodes.length < 1 || nodes.length > 9 || nodes.some(x => typeof x !== 'string' || !/^[-\w]{1,12}$/.test(x) || ['__proto__', 'constructor', 'prototype'].includes(x)) || new Set(nodes).size !== nodes.length)
            throw Error('Use 1–9 distinct task IDs containing letters, numbers, underscores or hyphens.');
        if (!Array.isArray(edges) || edges.length > 65)
            throw Error('Provide an edges array with at most 65 edges.');
        const adj = dictionary(nodes.map(v => [v, []])), rev = dictionary(nodes.map(v => [v, []])), degree = dictionary(nodes.map(v => [v, 0])), seen = new Set();
        for (const e of edges) {
            if (!Array.isArray(e) || e.length !== 2 || !nodes.includes(e[0]) || !nodes.includes(e[1]))
                throw Error('Each edge must name two existing task IDs.');
            const k = e.join('|');
            if (seen.has(k))
                throw Error('Duplicate edge: ' + e.join(' → '));
            seen.add(k);
            adj[e[0]].push(e[1]);
            rev[e[1]].push(e[0]);
            degree[e[1]]++;
        }
        return { nodes: [...nodes], edges: edges.map(e => [...e]), adj, rev, degree };
    }
    function topological(g) { const d = { ...g.degree }, q = g.nodes.filter(v => d[v] === 0), out = []; let h = 0; while (h < q.length) {
        const u = q[h++];
        out.push(u);
        for (const v of g.adj[u])
            if (--d[v] === 0)
                q.push(v);
    } return out.length === g.nodes.length ? out : null; }
    function path(g, s, t, skip = null) { if (s === t)
        return [s]; const q = [s], parent = dictionary([[s, null]]); let h = 0; while (h < q.length) {
        const u = q[h++];
        for (const v of g.adj[u]) {
            if (skip && skip[0] === u && skip[1] === v)
                continue;
            if (hasOwn(parent, v))
                continue;
            parent[v] = u;
            if (v === t) {
                const p = [v];
                while (parent[p[0]] !== null)
                    p.unshift(parent[p[0]]);
                return p;
            }
            q.push(v);
        }
    } return null; }
    function validOrder(g, o) { return o.length === g.nodes.length && new Set(o).size === o.length && g.nodes.every(v => o.includes(v)) && g.edges.every(([u, v]) => o.indexOf(u) < o.indexOf(v)); }
    function table(columns, rows) { return { columns, rows }; }
    function degrees(g, d, done) { return table(['Task', 'Remaining prerequisites', 'State'], g.nodes.map(v => [v, d[v], done.includes(v) ? 'Output' : d[v] === 0 ? 'Ready' : 'Waiting'])); }
    function validateFiles(input, g) {
        if (!topological(g))
            throw Error('File-scheduling examples require an acyclic graph.');
        if (!Array.isArray(input.files) || input.files.length > 30)
            throw Error('Provide a files array with at most 30 files.');
        const ids = new Set();
        for (const f of input.files) {
            if (typeof f.id !== 'string' || ids.has(f.id))
                throw Error('File IDs must be distinct strings.');
            ids.add(f.id);
            if (!Number.isSafeInteger(f.bytes) || f.bytes < 0 || f.bytes > 1000000)
                throw Error('File bytes must be integers from 0 to 1,000,000.');
            if (!Array.isArray(f.consumers) || new Set(f.consumers).size !== f.consumers.length || f.consumers.some(v => !g.nodes.includes(v)))
                throw Error('Consumers must be distinct existing tasks.');
            if (f.producer !== null) {
                if (!g.nodes.includes(f.producer) || f.consumers.some(v => v === f.producer || !path(g, f.producer, v)))
                    throw Error('Every file producer must precede all its consumers.');
            }
        }
    }
    function kahn(input, emit, mode) {
        const g = graph(input), d = { ...g.degree }, done = [];
        const queue = g.nodes.filter(v => d[v] === 0), heap = new MinHeap();
        let head = 0, edges = 0;
        const priority = v => mode === 'priority' ? -((hasOwn(input.priority, v) ? input.priority[v] : null) ?? 0) : v;
        if (mode === 'priority' || mode === 'lexical')
            for (const v of queue)
                heap.push([priority(v), v]);
        const ready = () => mode === 'fifo' ? queue.slice(head) : mode === 'lifo' ? [...queue].reverse() : heap.a.slice().sort(lex).map(x => x[1]);
        const state = () => ({ ready: ready(), done: [...done], order: [...done], table: degrees(g, d, done), work: { 'Edges processed': edges, 'Tasks output': done.length } });
        emit('init', 'Count incoming edges. Only tasks with no unmet prerequisite are ready.', { ...state(), equation: 'R = {v : d(v) = 0}' });
        while (ready().length) {
            const u = mode === 'fifo' ? queue[head++] : mode === 'lifo' ? queue.pop() : heap.pop()[1]; // @pick
            done.push(u);
            emit('pick', 'Select ' + u + ' from the ready set and append it to the order.', { ...state(), current: u, equation: 'd(' + u + ') = 0 ⇒ eligible' });
            for (const v of g.adj[u]) {
                const before = d[v];
                d[v]--;
                edges++; // @decrement
                if (d[v] === 0) {
                    if (mode === 'fifo' || mode === 'lifo')
                        queue.push(v);
                    else
                        heap.push([priority(v), v]);
                }
                emit('decrement', u + ' no longer blocks ' + v + (d[v] === 0 ? '; ' + v + ' becomes ready.' : '; another prerequisite remains.'), { ...state(), current: u, edge: [u, v], equation: 'd(' + v + ') = ' + before + ' − 1 = ' + d[v] });
            }
        }
        const cycle = done.length !== g.nodes.length; // @finish
        emit('finish', cycle ? 'No ready task remains, but some tasks are unprocessed: the graph contains a directed cycle.' : 'Every edge points forward in the completed order.', { ...state(), current: null, edge: null, result: cycle ? 'Cycle detected' : done.join(' → '), status: cycle ? 'cycle' : 'ok', equation: cycle ? '|output| < |V|' : '∀(u,v) ∈ E, position(u) < position(v)' });
        return { order: done, cycle };
    }
    function generations(input, emit) {
        const g = graph(input), d = { ...g.degree }, done = [], layers = [];
        let layer = g.nodes.filter(v => !d[v]), edges = 0;
        emit('init', 'Start with the sources of the graph.', { ready: layer, table: degrees(g, d, done), equation: 'L₀ = {v : d(v) = 0}' });
        while (layer.length) {
            const current = [...layer], next = [];
            layers.push(current); // @layer
            emit('layer', 'Generation ' + (layers.length - 1) + ' can run after the earlier generations finish.', { ready: current, done: [...done], groups: clone(layers), current: current[0], equation: 'generation ' + (layers.length - 1) + ' = {' + current.join(', ') + '}' });
            for (const u of current) {
                done.push(u);
                for (const v of g.adj[u]) {
                    edges++;
                    if (--d[v] === 0)
                        next.push(v);
                }
            }
            layer = next; // @advance
            emit('advance', 'Complete this entire generation before exposing the next one.', { ready: layer, done: [...done], order: [...done], table: degrees(g, d, done), work: { 'Generations': layers.length, 'Edges processed': edges } });
        }
        const cycle = done.length !== g.nodes.length;
        emit('finish', cycle ? 'A cyclic remainder cannot be assigned a generation.' : 'Generations express dependency levels, not the number of available processors.', { status: cycle ? 'cycle' : 'ok', result: cycle ? 'Cycle detected' : layers.map((l, i) => 'L' + i + ' = {' + l.join(', ') + '}').join(' · '), groups: layers });
        return { layers, order: done, cycle };
    }
    function dfs(input, emit) {
        const g = graph(input), color = dictionary(g.nodes.map(v => [v, 0])), finished = [], stack = [];
        let cycle = false, examined = 0;
        const state = () => ({ done: g.nodes.filter(v => color[v] === 2), active: [...stack], ready: [], order: [...finished], table: table(['Task', 'DFS state'], g.nodes.map(v => [v, ['Unseen', 'Active', 'Finished'][color[v]]])), work: { 'Edges examined': examined } });
        emit('init', 'White means unseen; active tasks are on the recursion stack.', { ...state(), equation: 'color ∈ {unseen, active, finished}' });
        function visit(u) {
            color[u] = 1;
            stack.push(u); // @enter
            emit('enter', 'Enter ' + u + ' and leave it active until all successors are finished.', { ...state(), current: u, equation: 'color(' + u + ') ← active' });
            for (const v of g.adj[u]) {
                examined++;
                emit('inspect', 'Inspect ' + u + ' → ' + v + '.', { ...state(), edge: [u, v] });
                if (color[v] === 1) {
                    cycle = true; // @cycle
                    emit('cycle', 'The edge returns to active task ' + v + ': this is a directed cycle.', { ...state(), status: 'cycle', result: 'Cycle detected', equation: 'edge to active vertex ⇒ directed cycle' });
                    return;
                }
                if (color[v] === 0)
                    visit(v);
                if (cycle)
                    return;
            }
            stack.pop();
            color[u] = 2;
            finished.push(u); // @finish_node
            emit('finish_node', 'Finish ' + u + ' after all of its successors.', { ...state(), current: u, equation: 'finish.append(' + u + ')' });
        }
        for (const v of g.nodes) {
            if (!color[v])
                visit(v);
            if (cycle)
                break;
        }
        const order = cycle ? [] : [...finished].reverse(); // @reverse
        if (!cycle)
            emit('reverse', 'Reverse the finish list to obtain a topological order.', { ...state(), current: null, edge: null, order, result: order.join(' → '), status: 'ok', equation: 'order = reverse(finish)' });
        return { order, cycle };
    }
    function breadth(input, emit, bounded = false) {
        const g = graph(input), s = input.source ?? g.nodes[0], t = input.target ?? g.nodes.at(-1);
        if (!g.nodes.includes(s) || !g.nodes.includes(t))
            throw Error('Source and target must name existing tasks.');
        const budget = bounded ? (input.budget ?? 3) : Infinity;
        if (bounded && (!Number.isInteger(budget) || budget < 0 || budget > 1000))
            throw Error('Use an integer edge budget from 0 to 1000.');
        const q = [s], seen = new Set([s]), parent = dictionary([[s, null]]), dist = dictionary([[s, 0]]), visited = [];
        let head = 0, inspected = 0;
        const state = () => ({ ready: q.slice(head), done: [...visited], active: [...seen], table: table(['Task', 'Distance from ' + s, 'Parent'], g.nodes.map(v => [v, dist[v] ?? '—', parent[v] ?? '—'])), work: { 'Edges examined': inspected, ...(bounded ? { 'Edge budget': budget } : {}) } });
        const found = () => { const p = [t]; while (parent[p[0]] !== null)
            p.unshift(parent[p[0]]); emit('found', 'The parent links give a shortest unweighted path.', { ...state(), path: p, current: t, result: p.join(' → '), status: 'ok', equation: 'distance(' + t + ') = ' + dist[t] }); return { path: p, status: 'found', inspected }; };
        emit('init', 'Start at ' + s + ' and search for ' + t + '.', { ...state(), equation: 'distance(' + s + ') = 0' });
        if (s === t)
            return found();
        while (head < q.length) {
            const u = q[head++];
            visited.push(u);
            emit('pop', 'Expand ' + u + '.', { ...state(), current: u });
            for (const v of g.adj[u]) {
                if (inspected >= budget) { // @unknown
                    emit('unknown', 'The edge budget is exhausted. A path may still exist.', { ...state(), status: 'unknown', result: 'UNKNOWN — not a proof of no path', equation: 'budget exhausted ≠ unreachable' });
                    return { path: null, status: 'unknown', inspected };
                }
                inspected++; // @inspect
                if (!seen.has(v)) {
                    seen.add(v);
                    parent[v] = u;
                    dist[v] = dist[u] + 1;
                    q.push(v);
                }
                emit('inspect', 'Inspect ' + u + ' → ' + v + '.', { ...state(), current: u, edge: [u, v], equation: 'distance(' + v + ') = ' + dist[v] });
                if (v === t)
                    return found();
            }
        }
        emit('absent', 'Every reachable task has been explored; the target is unreachable.', { ...state(), current: null, edge: null, status: 'unreachable', result: 'No path', equation: 'empty frontier + completed search ⇒ no path' });
        return { path: null, status: 'unreachable', inspected };
    }
    function reduction(input, emit) {
        const g = graph(input);
        if (!topological(g))
            throw Error('Transitive reduction requires a DAG in this lesson.');
        const kept = [], removed = [];
        let searches = 0;
        emit('init', 'Test each edge against an alternative path. Keep the original graph for every test.', { equation: 'remove (u,v) only if u reaches v without that edge', table: table(['Edge', 'Decision'], g.edges.map(e => [e.join(' → '), 'Not tested'])) });
        for (const edge of g.edges) {
            const witness = path(g, edge[0], edge[1], edge);
            searches++; // @test
            (witness ? removed : kept).push(edge);
            emit('test', witness ? 'Remove ' + edge.join(' → ') + ': ' + witness.join(' → ') + ' already enforces it.' : 'Keep ' + edge.join(' → ') + ': no alternate path exists.', { edge, path: witness ?? [], removed: [...removed], table: table(['Edge', 'Decision'], g.edges.map(e => [e.join(' → '), removed.some(x => lex(x, e) === 0) ? 'Redundant' : kept.some(x => lex(x, e) === 0) ? 'Keep' : 'Not tested'])), work: { 'Path searches': searches, 'Edges removed': removed.length }, equation: witness ? 'alternate path length = ' + (witness.length - 1) : 'no alternate path' });
        }
        emit('finish', 'The reduced graph preserves all reachability relations.', { edge: null, path: [], removed, result: kept.map(e => e.join(' → ')).join('; ') || 'No edges', status: 'ok', equation: 'reachability(G) = reachability(reduced G)' });
        return { edges: kept, removed };
    }
    function enumeration(input, emit) {
        const g = graph(input);
        if (g.nodes.length > 6)
            throw Error('Enumeration is limited to six tasks to keep the lesson responsive.');
        if (!topological(g))
            throw Error('No topological orders exist for a cyclic graph.');
        const orders = [], prefix = [], used = new Set();
        emit('init', 'Branch only on tasks whose prerequisites are already in the prefix.', { order: [], equation: 'eligible(v) ⇔ every predecessor is used' });
        function extend() {
            if (prefix.length === g.nodes.length) {
                orders.push([...prefix]); // @complete
                emit('complete', 'Record valid order ' + orders.length + '.', { done: [...prefix], order: [...prefix], work: { 'Orders found': orders.length }, result: prefix.join(' → ') });
                return;
            }
            const ready = g.nodes.filter(v => !used.has(v) && g.rev[v].every(p => used.has(p)));
            for (const v of ready) {
                prefix.push(v);
                used.add(v); // @choose
                emit('choose', 'Choose ' + v + ' for position ' + prefix.length + '.', { ready, done: [...prefix], current: v, order: [...prefix], equation: 'prefix ← prefix + [' + v + ']' });
                extend();
                used.delete(v);
                prefix.pop(); // @backtrack
                emit('backtrack', 'Undo ' + v + ' and try the next eligible alternative.', { current: v, done: [...prefix], order: [...prefix], equation: 'backtrack: restore the previous prefix' });
            }
        }
        extend();
        emit('finish', 'All orders have been enumerated for this small input.', { current: null, done: [], order: [], status: 'ok', result: orders.length + ' valid order' + (orders.length !== 1 ? 's' : ''), table: table(['No.', 'Valid order'], orders.map((o, i) => [i + 1, o.join(' → ')])) });
        return { orders };
    }
    function critical(input, emit) {
        const g = graph(input), order = topological(g);
        if (!order)
            throw Error('Longest-path dynamic programming here requires a DAG.');
        const duration = dictionary(g.nodes.map(v => [v, (hasOwn(input.duration, v) ? input.duration[v] : null) ?? 1]));
        if (Object.values(duration).some(x => !Number.isFinite(x) || x < 0))
            throw Error('Durations must be nonnegative finite numbers.');
        const finish = { ...duration }, parent = dictionary(g.nodes.map(v => [v, null])), done = [];
        const state = () => ({ done: [...done], order: [...done], table: table(['Task', 'Duration', 'Earliest finish'], g.nodes.map(v => [v, duration[v], finish[v]])) });
        emit('init', 'With unlimited processors and no transfer delay, each source can start at time zero.', { ...state(), equation: 'EF(v) = duration(v) initially' });
        for (const u of order) {
            done.push(u);
            for (const v of g.adj[u]) {
                const old = finish[v], candidate = finish[u] + duration[v]; // @relax
                if (candidate > old) {
                    finish[v] = candidate;
                    parent[v] = u;
                }
                emit('relax', 'Propagate the finish constraint from ' + u + ' to ' + v + '.', { ...state(), current: u, edge: [u, v], equation: 'EF(' + v + ') = max(' + old + ', ' + finish[u] + ' + ' + duration[v] + ') = ' + finish[v] });
            }
        }
        const end = g.nodes.reduce((a, b) => finish[a] >= finish[b] ? a : b), p = [end];
        while (parent[p[0]] !== null)
            p.unshift(parent[p[0]]);
        emit('finish', 'The critical path determines the earliest possible completion under these assumptions.', { ...state(), path: p, current: null, edge: null, status: 'ok', result: 'Completion time ' + finish[end] + ' · critical path ' + p.join(' → '), equation: 'T = maxᵥ EF(v) = ' + finish[end] });
        return { finish, path: p, makespan: finish[end] };
    }
    function insertion(input, emit, pk = false) {
        const g = graph(input), old = input.order ?? topological(g);
        if (!old || !validOrder(g, old))
            throw Error('Provide a valid initial topological order.');
        const [u, v] = input.insert ?? [g.nodes.at(-1), g.nodes[0]];
        if (!g.nodes.includes(u) || !g.nodes.includes(v))
            throw Error('Inserted edge endpoints must exist.');
        const pos = dictionary(old.map((x, i) => [x, i]));
        emit('init', 'Check whether the new edge ' + u + ' → ' + v + ' respects the existing order.', { order: old, newEdge: [u, v], table: table(['Task', 'Old position'], old.map((x, i) => [x, i])), equation: 'position(' + u + ') = ' + pos[u] + ', position(' + v + ') = ' + pos[v] });
        if (g.adj[u].includes(v)) {
            emit('finish', 'The edge already exists; nothing changes.', { result: old.join(' → '), status: 'ok' });
            return { order: old, cycle: false };
        }
        if (pos[u] < pos[v]) { // @forward
            emit('forward', 'The edge points forward; retain the existing order.', { result: old.join(' → '), order: old, status: 'ok', equation: 'position(u) < position(v) ⇒ no repair' });
            return { order: old, cycle: false };
        }
        const F = new Set(), B = new Set();
        let examined = 0;
        function search(start, adj, set, inside, label) {
            const todo = [start];
            while (todo.length) {
                const x = todo.pop();
                if (set.has(x))
                    continue;
                set.add(x);
                emit('discover', 'Discover ' + x + ' in the ' + label + ' affected set.', { current: x, forward: [...F], backward: [...B], equation: 'F = {' + [...F].join(', ') + '}; B = {' + [...B].join(', ') + '}' });
                for (const y of adj[x]) {
                    examined++;
                    if (inside(y) && !set.has(y))
                        todo.push(y);
                }
            }
        }
        if (pk) {
            search(v, g.adj, F, x => pos[x] <= pos[u], 'forward');
            if (!F.has(u))
                search(u, g.rev, B, x => pos[x] >= pos[v], 'backward');
        }
        const witness = pk ? (F.has(u) ? path(g, v, u) : null) : path(g, v, u);
        if (u === v || witness) { // @cycle
            emit('cycle', 'The existing path closes a cycle with the new edge. Reject this insertion.', { path: witness ?? [u], status: 'cycle', result: 'Insertion rejected; keep ' + old.join(' → '), equation: 'v reaches u + (u → v) ⇒ cycle' });
            return { order: old, cycle: true };
        }
        let order;
        if (pk) {
            const slots = old.map((x, i) => (F.has(x) || B.has(x)) ? i : -1).filter(i => i >= 0);
            const before = old.filter(x => B.has(x)), after = old.filter(x => F.has(x)); // @partition
            order = [...old];
            [...before, ...after].forEach((x, i) => order[slots[i]] = x);
            emit('partition', 'Place the backward set before the forward set, using only their original slots.', { forward: [...F], backward: [...B], order, table: table(['Task', 'Old position', 'New position'], old.map(x => [x, pos[x], order.indexOf(x)])), work: { 'Search edges examined': examined, 'Affected tasks': F.size + B.size }, equation: 'new affected order = B (old order) followed by F (old order)' });
        }
        else { // @recompute
            order = topological(graph({ ...input, edges: [...input.edges, [u, v]] }));
            emit('recompute', 'This reference method recomputes the full order after detecting a backward acyclic edge.', { order, equation: 'new order = Kahn(G + edge)' });
        }
        emit('finish', 'Check every original dependency and the new edge.', { order, status: 'ok', result: order.join(' → '), current: null, equation: '∀(a,b), position(a) < position(b)' });
        return { order, cycle: false };
    }
    function strongComponents(input, emit) {
        const g = graph(input), index = dictionary(), low = dictionary(), stack = [], on = new Set(), parts = [];
        let clock = 0;
        const state = () => ({ active: [...stack], groups: clone(parts), table: table(['Task', 'Index', 'Low link', 'On stack'], g.nodes.map(v => [v, index[v] ?? '—', low[v] ?? '—', on.has(v) ? 'Yes' : 'No'])) });
        emit('init', 'Find groups in which every task can reach every other task.', { ...state(), equation: 'u and v share a component iff u ⇝ v and v ⇝ u' });
        function visit(u) {
            index[u] = low[u] = clock++;
            stack.push(u);
            on.add(u); // @enter
            emit('enter', 'Assign a discovery index to ' + u + '.', { ...state(), current: u, equation: 'index(' + u + ') = low(' + u + ') = ' + index[u] });
            for (const v of g.adj[u]) {
                if (!(v in index)) {
                    visit(v);
                    low[u] = Math.min(low[u], low[v]);
                }
                else if (on.has(v))
                    low[u] = Math.min(low[u], index[v]); // @low
                emit('low', 'Update ' + u + ' using edge ' + u + ' → ' + v + '.', { ...state(), current: u, edge: [u, v], equation: 'low(' + u + ') = ' + low[u] });
            }
            if (low[u] === index[u]) {
                const part = [];
                let w;
                do {
                    w = stack.pop();
                    on.delete(w);
                    part.push(w);
                } while (w !== u);
                parts.push(part); // @component
                emit('component', 'Pop one complete strongly connected component.', { ...state(), current: u, equation: 'low(' + u + ') = index(' + u + ')', result: '{' + part.join(', ') + '}' });
            }
        }
        for (const v of g.nodes)
            if (!(v in index))
                visit(v);
        emit('finish', 'Components can be condensed to a DAG. Tasks within a cyclic component cannot be topologically ordered.', { ...state(), current: null, edge: null, result: parts.map(p => '{' + p.join(', ') + '}').join(' · '), status: 'ok' });
        return { components: parts };
    }
    function heapUpdates(input, emit) {
        const ids = input.nodes, heap = new MinHeap(), score = dictionary(), version = dictionary(), alive = new Set();
        graph(input);
        const events = input.events ?? [{ op: 'push', task: 'A', priority: 1 }, { op: 'push', task: 'B', priority: 3 }, { op: 'update', task: 'A', priority: 5 }, { op: 'pop' }, { op: 'pop' }, { op: 'pop' }];
        if (events.length > 40)
            throw Error('At most 40 queue operations are supported.');
        const out = [];
        const state = () => ({ ready: heap.a.slice().sort(lex).filter(e => alive.has(e[1]) && version[e[1]] === e[2]).map(e => e[1]), order: out, table: table(['Heap entry', 'Score', 'Version', 'Status'], heap.a.slice().sort(lex).map(e => [e[1], -e[0], e[2], alive.has(e[1]) && version[e[1]] === e[2] ? 'Current' : 'Stale'])) });
        emit('init', 'Keep replacement entries and reject stale versions when they reach the top.', { ...state(), equation: 'entry valid ⇔ version(entry) = version(task)' });
        for (const event of events) {
            if (event.op === 'push' || event.op === 'update') {
                const v = event.task;
                if (!ids.includes(v) || !Number.isFinite(event.priority))
                    throw Error('Queue events require an existing task and a numeric priority.');
                score[v] = event.priority;
                version[v] = (version[v] ?? 0) + 1;
                alive.add(v);
                heap.push([-score[v], v, version[v]]); // @push
                emit('push', (event.op === 'push' ? 'Insert ' : 'Replace the priority of ') + v + '.', { ...state(), current: v, equation: 'key = (−' + score[v] + ', ' + v + ', version ' + version[v] + ')' });
            }
            else if (event.op === 'pop') {
                let entry = null;
                while (heap.size) {
                    const x = heap.pop();
                    if (!alive.has(x[1]) || version[x[1]] !== x[2]) { // @stale
                        emit('stale', 'Discard obsolete entry for ' + x[1] + '.', { ...state(), current: x[1], equation: 'stale version ⇒ ignore' });
                        continue;
                    }
                    entry = x;
                    break;
                }
                if (entry) {
                    alive.delete(entry[1]);
                    out.push(entry[1]);
                    emit('pop', 'Return current highest-priority task ' + entry[1] + '.', { ...state(), current: entry[1] });
                }
                else
                    emit('empty', 'No valid entries remain.', { ...state(), current: null });
            }
            else
                throw Error('Queue op must be push, update or pop.');
        }
        emit('finish', 'Old entries never override a newer task priority.', { ...state(), current: null, status: 'ok', result: out.join(' → ') });
        return { order: out };
    }
    function storage(input, emit, mode) {
        const g = graph(input);
        validateFiles(input, g);
        const d = { ...g.degree }, done = [], doneSet = new Set(), ready = new Set(g.nodes.filter(v => !d[v]));
        const creation = dictionary(g.nodes.map(v => [v, 0]));
        for (const f of input.files)
            if (f.producer !== null)
                creation[f.producer] += f.bytes;
        let groups = input.files.filter(f => f.producer !== null && f.consumers.length && f.bytes > 0).map(f => ({ ids: [f.id], weight: f.bytes, consumers: [...f.consumers] }));
        let searches = 0;
        if (mode === 'maximal')
            for (const q of groups) {
                q.consumers = q.consumers.filter(c => !q.consumers.some(t => { if (c === t)
                    return false; searches++; return !!path(g, c, t); }));
            }
        if (mode === 'grouped') {
            const map = new Map();
            for (const q of groups) {
                const key = [...q.consumers].sort().join('|');
                if (map.has(key)) {
                    map.get(key).ids.push(...q.ids);
                    map.get(key).weight += q.weight;
                }
                else
                    map.set(key, q);
            }
            groups = [...map.values()];
        }
        const counts = groups.map(q => q.consumers.length), remaining = groups.map(q => new Set(q.consumers)), score = dictionary(g.nodes.map(v => [v, -creation[v]]));
        const incident = dictionary(g.nodes.map(v => [v, []]));
        groups.forEach((q, k) => q.consumers.forEach(v => incident[v].push(k)));
        groups.forEach((q, k) => { if (counts[k] === 1)
            score[q.consumers[0]] += q.weight; });
        const heap = new MinHeap(), versions = dictionary(g.nodes.map(v => [v, 0]));
        let decrements = 0, evaluations = 0, visits = 0;
        const refresh = v => { versions[v]++; heap.push([-score[v], v, versions[v]]); };
        for (const v of ready)
            refresh(v);
        const readyScores = () => [...ready].sort().map(v => [v, score[v]]);
        const state = () => ({ done: [...done], ready: [...ready].sort((a, b) => score[b] - score[a] || compare(a, b)), order: [...done], scores: readyScores(), table: table(['Ready task', 'Created bytes', 'Priority'], [...ready].sort().map(v => [v, creation[v], score[v]])), files: table(['Metadata files', 'Tracked consumers', mode === 'fullscore' ? 'Unfinished users' : 'Counter*'], groups.map((q, k) => [q.ids.join(', '), q.consumers.join(', '), mode === 'fullscore' ? q.consumers.filter(v => !doneSet.has(v)).length : counts[k]])), work: { 'Counter decrements': decrements, 'File score checks': evaluations, 'Counter visits': visits, 'Prep reachability searches': searches } });
        emit('init', 'Store creation costs at their original producers. Give static credit to one-consumer files.', { ...state(), equation: 's(v) = releasable bytes − bytes created by v' });
        while (ready.size) {
            if (mode === 'fullscore') {
                for (const v of ready)
                    score[v] = -creation[v];
                for (const f of input.files) {
                    if (f.producer === null || !f.consumers.length)
                        continue;
                    evaluations++;
                    const left = f.consumers.filter(v => !doneSet.has(v));
                    if (left.length === 1 && ready.has(left[0]))
                        score[left[0]] += f.bytes;
                }
                emit('recompute', 'Recompute the scores of ready tasks from the original file consumers.', { ...state(), equation: 'credit f iff |C(f) − done| = 1' });
            }
            let u;
            if (mode === 'fullscore')
                u = [...ready].sort((a, b) => score[b] - score[a] || compare(a, b))[0];
            else {
                while (heap.size) {
                    const x = heap.pop();
                    if (ready.has(x[1]) && versions[x[1]] === x[2]) {
                        u = x[1];
                        break;
                    }
                }
            }
            if (u === undefined)
                throw Error('Queue invariant failed.');
            const winning = score[u];
            ready.delete(u);
            done.push(u);
            doneSet.add(u); // @choose
            emit('choose', 'Choose ' + u + ' with priority ' + winning + '.', { ...state(), current: u, equation: 's(' + u + ') = ' + winning + ' (highest ready score)' });
            const changed = new Set();
            if (mode !== 'fullscore')
                for (const k of incident[u]) {
                    visits++;
                    if (counts[k] === 1)
                        continue; // @skip
                    const before = counts[k];
                    counts[k]--;
                    decrements++;
                    remaining[k].delete(u); // @decrement
                    let v = null;
                    if (counts[k] === 1) {
                        v = [...remaining[k]][0];
                        score[v] += groups[k].weight;
                        changed.add(v);
                    }
                    emit('decrement', 'Counter for ' + groups[k].ids.join(', ') + ' changes ' + before + ' → ' + counts[k] + (v ? '; ' + v + ' receives release credit.' : '.'), { ...state(), current: u, equation: v ? 's(' + v + ') ← s(' + v + ') + ' + groups[k].weight : 'r ← r − 1' });
                }
            for (const v of g.adj[u])
                if (--d[v] === 0) {
                    ready.add(v);
                    changed.add(v);
                }
            if (mode !== 'fullscore')
                for (const v of changed)
                    if (ready.has(v))
                        refresh(v); // @refresh
            emit('refresh', 'Make newly unblocked tasks eligible; refresh each changed ready task once.', { ...state(), current: u, equation: 'eligible(v) ⇔ d(v) = 0' });
        }
        emit('finish', 'This order follows the fixed greedy priority. It is not a proof of minimum storage.', { ...state(), current: null, status: 'ok', result: done.join(' → '), equation: 'same ready scores + same tie-break ⇒ same order' });
        return { order: done, groups, counts, decrements, evaluations, visits, searches };
    }
    function lifetime(input, emit) {
        const g = graph(input);
        validateFiles(input, g);
        const order = input.order ?? topological(g);
        if (!validOrder(g, order))
            throw Error('The supplied execution order must respect dependencies.');
        const remaining = input.files.map(f => new Set(f.consumers)), live = new Set(), done = [];
        let peak = 0;
        const bytes = () => [...live].reduce((s, k) => s + input.files[k].bytes, 0);
        const state = () => ({ done: [...done], order: [...done], files: table(['File', 'Bytes', 'Unfinished users', 'Stored here'], input.files.map((f, k) => [f.id, f.bytes, [...remaining[k]].join(', ') || 'None', f.producer === null ? 'External (excluded)' : live.has(k) ? 'Yes' : 'No'])), work: { 'Retained bytes': bytes(), 'Peak bytes': peak } });
        emit('init', 'Count generated files only. Retain final outputs; exclude external inputs.', { ...state(), equation: 'stored bytes = sum of live generated-file sizes' });
        for (const u of order) {
            input.files.forEach((f, k) => { if (f.producer === u)
                live.add(k); });
            peak = Math.max(peak, bytes()); // @allocate
            emit('allocate', 'Create outputs of ' + u + ' before releasing its inputs.', { ...state(), current: u, equation: 'peak ← max(peak, current retained bytes)' });
            input.files.forEach((f, k) => { remaining[k].delete(u); if (f.consumers.length && remaining[k].size === 0)
                live.delete(k); });
            done.push(u); // @release
            emit('release', 'After ' + u + ' finishes, release intermediates with no unfinished consumers.', { ...state(), current: u, equation: 'delete intermediate f iff remaining consumers = 0' });
        }
        emit('finish', 'Final outputs stay retained. This is a declared file-lifetime model, not process RAM.', { ...state(), current: null, status: 'ok', result: 'Peak ' + peak + ' bytes; final retained ' + bytes() + ' bytes' });
        return { peak, retained: bytes(), order };
    }
    function heft(input, emit) {
        const g = graph(input), topo = topological(g);
        if (!topo)
            throw Error('HEFT requires a DAG.');
        const costs = input.costs;
        if (!costs || g.nodes.some(v => !Array.isArray(costs[v]) || costs[v].length !== 2 || costs[v].some(x => !Number.isFinite(x) || x <= 0)))
            throw Error('Provide two positive processor costs per task.');
        const comm = input.communication ?? 1;
        if (!Number.isFinite(comm) || comm < 0)
            throw Error('Communication cost must be nonnegative.');
        const rank = dictionary(), slots = [[], []], assigned = dictionary(), finish = dictionary(), schedule = [];
        emit('init', 'Rank tasks using average execution cost; then choose processors by earliest finish.', { equation: 'rank(u) = average cost(u) + maxᵥ [communication + rank(v)]' });
        for (const u of [...topo].reverse()) {
            rank[u] = (costs[u][0] + costs[u][1]) / 2 + Math.max(0, ...g.adj[u].map(v => comm + rank[v])); // @rank
            emit('rank', 'Compute upward rank of ' + u + ' after its successors.', { current: u, table: table(['Task', 'Processor 1', 'Processor 2', 'Upward rank'], g.nodes.map(v => [v, ...costs[v], rank[v] ?? '—'])), equation: 'rank(' + u + ') = ' + rank[u] });
        }
        const order = [...g.nodes].sort((a, b) => rank[b] - rank[a] || compare(a, b));
        for (const u of order) {
            const candidates = [];
            for (let p = 0; p < 2; p++) {
                const available = Math.max(0, ...g.rev[u].map(v => finish[v] + (assigned[v] === p ? 0 : comm)));
                let start = available;
                for (const s of slots[p]) {
                    if (start + costs[u][p] <= s.start)
                        break;
                    start = Math.max(start, s.end);
                }
                candidates.push({ task: u, p, start, end: start + costs[u][p] }); // @estimate
            }
            emit('estimate', 'Check the first feasible gap on each processor for ' + u + '.', { current: u, order: schedule.map(x => x.task), schedule: clone(schedule), table: table(['Processor', 'Start', 'Finish'], candidates.map(x => ['P' + (x.p + 1), x.start, x.end])), equation: 'EFT(u,p) = first feasible start + execution cost' });
            const best = candidates.sort((a, b) => a.end - b.end || a.p - b.p)[0]; // @assign
            slots[best.p].push(best);
            slots[best.p].sort((a, b) => a.start - b.start);
            assigned[u] = best.p;
            finish[u] = best.end;
            schedule.push(best);
            emit('assign', 'Assign ' + u + ' to P' + (best.p + 1) + ' from ' + best.start + ' to ' + best.end + '.', { current: u, done: schedule.map(x => x.task), order: schedule.map(x => x.task), schedule: clone(schedule), equation: 'choose processor with minimum EFT' });
        }
        const makespan = Math.max(...Object.values(finish));
        emit('finish', 'Processor intervals obey dependencies and do not overlap on the same processor.', { current: null, schedule, done: order, order, table: table(['Task', 'Processor', 'Start', 'Finish'], schedule.map(s => [s.task, 'P' + (s.p + 1), s.start, s.end])), result: 'Makespan ' + makespan + ' time units', status: 'ok', equation: 'makespan = max finish = ' + makespan });
        return { schedule, rank, makespan };
    }
    function sortScan(input, emit) {
        const g = graph(input), order = input.order ?? topological(g), affected = input.affected ?? [g.nodes[0], g.nodes.at(-1)];
        if (!order || !validOrder(g, order))
            throw Error('A valid original order is required.');
        if (!Array.isArray(affected) || affected.some(x => !g.nodes.includes(x)) || new Set(affected).size !== affected.length || !affected.length)
            throw Error('Affected tasks must be nonempty, distinct and in the graph.');
        const pos = dictionary(order.map((v, i) => [v, i])), marked = new Set(affected), lo = Math.min(...affected.map(x => pos[x])), hi = Math.max(...affected.map(x => pos[x]));
        let checks = 0;
        const gathered = [];
        emit('init', 'Both procedures recover the same tasks in their previous relative order.', { order, active: affected, equation: 'k = ' + affected.length + ', interval length L = ' + (hi - lo + 1) });
        const sorted = [...affected].sort((a, b) => pos[a] - pos[b]); // @sort
        emit('sort', 'Sort the affected tasks by their old positions.', { order: sorted, active: affected, table: table(['Task', 'Old position'], sorted.map(v => [v, pos[v]])), equation: 'comparison-sort bound O(k log k); not a measured time' });
        for (let i = lo; i <= hi; i++) {
            checks++;
            if (marked.has(order[i]))
                gathered.push(order[i]); // @scan
            emit('scan', 'Scan old position ' + i + ' and ' + (marked.has(order[i]) ? 'collect ' : 'skip ') + order[i] + '.', { current: order[i], order: gathered, work: { 'Positions scanned': checks }, equation: 'L positions inspected; constant-time membership assumed' });
        }
        emit('finish', 'The two lists are identical. Their total preparation costs still need measurement.', { current: null, order: gathered, result: sorted.join(' → '), status: 'ok', equation: 'sort result = scan result' });
        return { sorted, scanned: gathered, checks };
    }
    function lrcRule(input, emit) {
        const g = graph(input), files = input.files ?? [];
        if (files.some(f => !Array.isArray(f.consumers) || f.consumers.some(v => !g.nodes.includes(v))))
            throw Error('Provide valid file consumer sets.');
        if (!files.length)
            throw Error('Provide at least one cached file.');
        const remaining = files.map(f => new Set(f.consumers)), resident = new Set(files.map((f, i) => i)), order = input.order ?? topological(g);
        if (!order || !validOrder(g, order))
            throw Error('A valid completion order is required.');
        const victim = [...resident].sort((a, b) => remaining[a].size - remaining[b].size || compare(files[a].id, files[b].id))[0];
        const state = () => ({ files: table(['Cached file', 'Unfinished consumers', 'Reference count', 'Resident'], files.map((f, i) => [f.id, [...remaining[i]].join(', ') || 'None', remaining[i].size, resident.has(i) ? 'Yes' : 'Evicted'])) });
        emit('init', 'Compare cached files by unfinished-dependent count. The fixture asks for one eviction.', { ...state(), equation: 'victim = argmin resident reference count' });
        resident.delete(victim); // @evict
        emit('evict', 'Evict ' + files[victim].id + '; it has the smallest unfinished-dependent count.', { ...state(), result: 'Victim: ' + files[victim].id, equation: 'r(' + files[victim].id + ') = ' + remaining[victim].size });
        const done = [];
        for (const u of order) {
            done.push(u);
            remaining.forEach(s => s.delete(u)); // @complete
            emit('complete', 'After ' + u + ' completes, update the dependent counts.', { ...state(), current: u, done, order: done });
        }
        emit('finish', 'This demonstrates the eviction priority only; it does not model misses, reloads or full cache throughput.', { ...state(), current: null, status: 'ok', result: 'Selected eviction: ' + files[victim].id });
        return { victim: files[victim].id };
    }
    const runs = { fifo: (i, e) => kahn(i, e, 'fifo'), lifo: (i, e) => kahn(i, e, 'lifo'), priority: (i, e) => kahn(i, e, 'priority'), lexical: (i, e) => kahn(i, e, 'lexical'), generations, dfs, bfs: (i, e) => breadth(i, e), bounded: (i, e) => breadth(i, e, true), reduction, enumeration, critical, insertion: (i, e) => insertion(i, e), pk: (i, e) => insertion(i, e, true), scc: strongComponents, heap: heapUpdates, fullscore: (i, e) => storage(i, e, 'fullscore'), counters: (i, e) => storage(i, e, 'counters'), grouped: (i, e) => storage(i, e, 'grouped'), maximal: (i, e) => storage(i, e, 'maximal'), lifetime, heft, sortscan: sortScan, lrc: lrcRule };
    const sourceFunctions = { fifo: kahn, lifo: kahn, priority: kahn, lexical: kahn, generations, dfs, bfs: breadth, bounded: breadth, reduction, enumeration, critical, insertion, pk: insertion, scc: strongComponents, heap: heapUpdates, fullscore: storage, counters: storage, grouped: storage, maximal: storage, lifetime, heft, sortscan: sortScan, lrc: lrcRule };
    function run(id, input, record = true) {
        if (!hasOwn(runs, id))
            throw Error('Unknown simulator.');
        graph(input);
        const frames = [];
        let previous = { ready: [], done: [], active: [], order: [], current: null, edge: null, work: {}, table: null, equation: '', result: null, status: 'running' };
        const emit = (key, message, patch = {}) => { if (frames.length >= 20000)
            throw Error('Trace too large. Reduce the example.'); previous = { ...previous, ...patch, key, message }; if (record)
            frames.push(clone(previous)); };
        const result = runs[id](clone(input), emit);
        return { id, input: clone(input), frames, result };
    }
    const api = { run, ids: Object.keys(runs), source: id => { if (!hasOwn(sourceFunctions, id)) throw Error('Unknown simulator.'); return sourceFunctions[id].toString(); }, graph, topological, path, validOrder, MinHeap };
    if (typeof module !== 'undefined' && module.exports)
        module.exports = api;
    root.AlgorithmSimulator = api;
})(typeof window !== 'undefined' ? window : globalThis);
