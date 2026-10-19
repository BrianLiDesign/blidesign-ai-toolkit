# Editable diagram practices

Reviewed: 2026-10-18 against official draw.io documentation and desktop source. The file structure
below is established mxGraph XML; CLI flags must be checked against the installed desktop version.

## Authoring rules (toolkit recommendations)

Use an uncompressed `.drawio` source for reviewable new diagrams. Preserve page IDs, layer parents,
cell IDs, style, metadata, and geometry when updating existing documents. For large existing files,
prefer the editor's supported operations over reserializing the whole document.

For generated XML, use an XML library to escape attribute values. Require unique cell IDs per
page, valid parents, and existing source/target cells for connected edges. Use native connectors
attached to shapes so layout edits preserve their relationships. Keep spacing and alignment
consistent; route crossing connectors clearly. These are authoring checks, not a complete draw.io
schema validator. Compressed pages require compatible decoding/editor support before inspection.

Adapt [the editable example](../assets/request.drawio). Both rectangles and their connector should
remain independently selectable after reopening. Confirm that labels fit and arrow direction
survives export. For multiple pages, select and inspect the intended pages explicitly; the bundled
helper exports one page at a time, with zero-based page indices.

## Primary sources and compatibility

- [XML source editing](https://www.drawio.com/docs/manual/advanced/diagram-source-edit/): page
  source uses mxGraphModel; malformed XML can be rejected by the editor.
- [Save formats](https://www.drawio.com/docs/manual/editor/save-file-formats/): preserve editable
  `.drawio` source; check SVG compatibility in the destination viewer.
- [Export formats](https://www.drawio.com/docs/manual/export/export-diagram/): export views for
  sharing while retaining the editable file.
- [Desktop project](https://github.com/jgraph/drawio-desktop) and its
  [CLI argument source](https://github.com/jgraph/drawio-desktop/blob/dev/src/main/args.js): use
  the installed release's `--help` to confirm export options. Desktop is GPL-3.0 licensed; it is
  an optional external tool, not vendored or installed with this skill.

An image export does not establish editability. Open/save/reopen is the relevant acceptance check
for preserved editable elements. Report that check as unavailable when no editor can be exercised.
