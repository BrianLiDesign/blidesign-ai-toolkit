# Dependency graph practices

Reviewed: 2026-10-18 against official Graphviz documentation. Use established DOT syntax; record
the actual Graphviz release used because layout and fonts can change across machines.

## Domain rules (toolkit recommendations)

- Choose one node grain per view, such as packages or modules. Label any deliberate aggregation.
- Define `A -> B`, for example as "A imports B". Apply that direction consistently and include it
  in the title or legend. Build prerequisites may use a different direction, which must be explicit.
- Preserve meaningful cycles. Mark excluded tests, generated files, optional dependencies, and
  unresolved dynamic imports in the evidence note. Deduplicate repeated edges without losing their
  relevant type or weight.
- Use stable identifiers independent of display labels. Quote labels and escape content using DOT
  rules; do not concatenate arbitrary repository text as executable HTML labels or attributes.
- Separate static dependency evidence from runtime traces. A graph of observed calls requires
  trace coverage and cannot establish all possible calls.

## Tool guidance

[DOT language](https://graphviz.org/doc/info/lang.html) defines directed graphs, quoted identifiers,
and subgraphs. Named subgraphs with the `cluster` prefix are a layout convention rather than a
domain relationship. [The dot engine](https://graphviz.org/docs/layouts/dot/) is intended for
directed graphs and aims to reduce crossings. [SVG output](https://graphviz.org/docs/outputs/svg/)
is suitable for scalable exports.

Adapt [the dependency example](../assets/modules.dot). The sample's edge means "imports"; reverse
arrows would change that meaning. Check the extracted edge list independently of the rendered
layout. Graphviz's success establishes rendering, not completeness of dependency extraction.
