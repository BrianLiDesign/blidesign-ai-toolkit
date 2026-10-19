---
name: dependency-graphs
description: Build evidence-backed graphs of module imports, package dependencies, build relationships, or coupling, using Graphviz DOT when appropriate. Preserve edge meaning and distinguish static dependencies from runtime calls.
---

# Dependency graphs

Read [shared standards](../engineering-visuals/references/standards.md) and
[graph practices](references/practices.md) before extracting or drawing a graph.

Define the node grain and exactly what an edge means. Collect edges from the project's existing
dependency tooling, manifests, imports, or build metadata; record the extraction scope and omitted
dynamic relationships. Do not infer a runtime call graph from imports alone.

Use DOT with the `dot` layout for directed dependencies when Graphviz is available. A small graph
can use Mermaid if that fits its destination; follow these domain checks regardless of renderer.
Keep an edge list or extraction command with maintained output so the graph can be refreshed.
Use clusters for meaningful boundaries and split dense graphs rather than hiding inconvenient
cycles. Render with the shared helper, inspect the result, and report evidence and limitations.
