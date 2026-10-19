# Local rendering

Reviewed: 2026-10-18. The helper requires Python 3.10+ and uses the standard library. Run it from
the installed skill directory, or substitute its actual path. Paths below are examples relative
to that directory; input paths are resolved from the caller's working directory.

## Mermaid baseline

Mermaid CLI **12.0.0** is MIT licensed and requires Node **22.13.0+**, according to its npm metadata.
It uses a browser runtime. Prefer an existing compatible project installation. For a new isolated
tool directory outside source control, install this exact baseline and retain the generated lock:

```sh
npm install --prefix <tool-directory> --save-exact @mermaid-js/mermaid-cli@12.0.0
python scripts/render_diagram.py --engine mermaid --mermaid-cli <tool-directory>/node_modules/@mermaid-js/mermaid-cli/src/cli.js --input diagram.mmd --output diagram.svg
```

Angle-bracket paths are placeholders, not literal shell arguments. Use host-appropriate quoting.
When the project already pins a compatible release, retain it and record its version. If using an
existing Chromium browser, set the package manager process's `PUPPETEER_SKIP_DOWNLOAD=true` before
installation and pass a reviewed `--puppeteer-config` JSON containing its local `executablePath`.
Keep machine paths in that local file only. Otherwise the package may download its browser runtime.
Retain browser sandboxing. Investigate certificate failures with the host's trusted certificate
configuration; do not disable TLS verification.

The default [configuration](../assets/mermaid-config.json) uses strict security and non-HTML labels.
This does not isolate untrusted input or guarantee no network requests. The helper calls Node and
the installed JavaScript entrypoint directly, avoiding Windows command-wrapper quoting.
It never downloads dependencies itself.

Sources: [official CLI](https://github.com/mermaid-js/mermaid-cli),
[package metadata](https://www.npmjs.com/package/@mermaid-js/mermaid-cli/v/12.0.0),
[Mermaid configuration](https://mermaid.js.org/config/usage.html),
[Puppeteer configuration](https://pptr.dev/guides/configuration).

Audit the resolved dependency lock when installing or updating a renderer. The 2026-10-18 smoke
installation resolved Mermaid 12.2.0 and reported two low-severity npm findings (KaTeX and its CLI
parent), with no moderate/high/critical findings. The underlying
[KaTeX advisory](https://github.com/advisories/GHSA-238p-pmpm-9mq7) requires pre-existing prototype
pollution or attacker influence over option prototypes. This compatibility baseline is not a
security endorsement; recheck patched compatible releases before using untrusted math input.

## Graphviz and draw.io (optional)

Use installed native executables, or install a specific release through the platform's reviewed
package manager or official release. Record the exact version and provenance. Neither is bundled.

```sh
python scripts/render_diagram.py --engine graphviz --executable <dot-executable> --input graph.dot --output graph.svg
python scripts/render_diagram.py --engine drawio --executable <drawio-executable> --input diagram.drawio --output diagram.svg --page-index 0
```

Graphviz uses `-Tsvg`, `-Tpng`, or `-Tpdf`; output plugins depend on the installed build. draw.io uses
`--export`, `--format`, `--page-index`, and `--output`. Confirm the installed desktop release's
`--help`; a graphical environment may be required even for export on Linux. Use one output path per
page. Desktop export is optional when an editor can export manually.

Sources: [Graphviz CLI](https://graphviz.org/doc/info/command.html),
[Graphviz license](https://graphviz.org/license/) (EPL-2.0 for current releases),
[draw.io desktop](https://github.com/jgraph/drawio-desktop) (GPL-3.0),
[desktop argument definitions](https://github.com/jgraph/drawio-desktop/blob/dev/src/main/args.js).

## Helper guarantees and limits

The helper passes argument arrays without a shell, rejects shell-wrapper executables, refuses to
overwrite source/configuration, and stages exports separately. Existing exports survive renderer
failure; replacement requires `--overwrite`. Missing tools, nonzero exits, timeouts, empty output,
and invalid output signatures fail. SVG receives an XML/root check; PNG/PDF receive signature
checks only. These checks do not prove image integrity, editability, semantics, or accessibility.
On timeout it terminates the owned renderer process group/tree, including browser children.

The JSON result says `rendered` and explicitly leaves domain checks and visual inspection
unperformed. Inspect the exported image and apply the specialist checklist before claiming
validation. Renderer stderr can include source labels; review failure details before sharing.
