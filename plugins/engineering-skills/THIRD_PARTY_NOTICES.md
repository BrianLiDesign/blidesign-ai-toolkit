# Third-party notices

## Matt Pocock skills

- Source: <https://github.com/mattpocock/skills>
- Pinned revision: see `../../upstream/sources.lock.json`
- License: MIT
- License text: `LICENSES/mattpocock-skills-MIT.txt`

The skill directories are flattened into this plugin so each host can discover every `SKILL.md` directly.

Owned toolkit guidance is appended using `upstream/mattpocock-overlays.json`. The updater reapplies
these declared transformations before computing the content digest. The original upstream pin and
MIT license are preserved; the additions are maintained separately from the upstream text.
