---
tags:
  - technical
  - planning
  - work
---

## the critique, restated

[[Pyblish issues]] lists nine concrete complaints, not just "Pyblish is bad": [[Pyblish issue - dependency injection]] makes plugin behavior depend on an arg *name* rather than its position or type, which is unpythonic and silently changes what a plugin does on rename; [[Pyblish issue - has no explicit plugin control]] means you register a folder and get an all-or-nothing run, no way to cleanly opt a single plugin in or out; [[Pyblish issue - action and plugin have no direct link]] forces actions to re-derive their instance from `context.data['results']` instead of holding a reference; [[Pyblish issue - inconsistent logic]] and [[Pyblish issue - warning vs error]] cover the mixed data-driven/explicit design and the fact that warning and error are two unrelated code paths (log line vs exception) instead of one severity value; [[Pyblish issue - plugins are hardcoded to the project or studio]] means almost no plugin is reusable across projects because it reaches into `context` for project-specific data; and [[Pyblish issue - docs are confusing]], [[Pyblish issue - UI is not artist friendly]], [[Pyblish issue - development is slow]] cover documentation sprawl, an artist-facing UI that only shows pass/fail with no per-check detail, and a slow-moving core that can't absorb fixes without breaking backwards compatibility. The conclusion in that note is explicit: don't patch Pyblish, don't fork it either ("if you hard fork, you might as well start from scratch"), use it as-is for now, and build [[pipeline as code]] instead.

## the direction already chosen

[[pipeline as code]] (no note yet, referenced from [[Pyblish issues]], [[review pac]], [[validation gym]] and [[my code projects]]) is the named replacement direction: explicit config-driven plugin selection, a community plugin repo, and workflows as data instead of folder-scanning magic. [[review pac]] records that this was already attempted once, as "pac2" — a working prototype built in days that hit Pyblish's goals more cleanly, then died from scope creep (generalizing from validation into a full batch/export/CI pipeline tool) and over-abstraction (custom metaclasses, `__setattr__` overrides to auto-link nodes). The retrospective's own fix for next time: ship against the original validation-only goal, get test users, then generalize — not the reverse.

## what already exists in the wild

No open-source project already *is* the "pipeline as code" note as specified — that's a genuine gap, not something to research further. What's out there instead:

- **AYON / OpenPype / Avalon** are the direct lineage of studio tools built on Pyblish, and all three keep Pyblish's plugin engine as their core and only add a settings server, a nicer Publisher UI, and per-project config layered on top. They do not fix the underlying complaints: dependency injection is unchanged, family-based filtering is still implicit (an OpenPype maintainer discussion explicitly debates this vs. an explicit check), and action/plugin/instance linkage is the same context-lookup pattern. They would not replace Pyblish under this proposal's goals, they'd just move the complaints one layer up.
- **USD asset validation** (NVIDIA's `usdex.test`/`unittest`-based Asset Validator, the standalone `omniverse-asset-validator` used in CI) is the closest real-world match to "explicit, code-first checks with no implicit dependency injection": validators are plain classes/functions registered explicitly, runnable headless in CI, no context-based magic. It's schema/USD-specific rather than a general DCC pipeline, so it's a pattern to borrow, not a drop-in replacement.
- **Kabaret** is a broader pipeline/asset-management framework (dataflow graphs, no fixed schema) but its own docs say not to use it in production yet, and it doesn't target validation specifically.
- No hit for a maintained "asset validation via pytest" framework as a named product — the closest is exactly the vault's own [[R&D Blender validation pipeline with pytest]] experiment.

## recommended next step

Don't restart pac2's scope. [[R&D Blender validation pipeline with pytest]] is already the first concrete step in the pipeline-as-code direction: plain Python functions (`get_non_zero_transform`, `get_non_manifold_edges`, ...) called directly from parametrized pytest tests, with no implicit `process(self, context)` dependency injection and no folder-scanning plugin discovery — the plugin *is* the test file, explicitly selected by pytest's own collection args. That note stalled on a real but narrow problem (Blender's bundled addons aren't packages, so pytest collection breaks on `--ignore` edge cases), not on architecture.

Concrete next step: take that Blender/pytest prototype, solve the collection-path issue properly (an explicit `pytest.ini`/`conftest.py` with `testpaths` pointed only at the validation suite, instead of `--ignore`-ing addon folders), and extend it to cover two or three checks from [[validation gym]] (e.g. [[validation gym - 001 - is a mesh]], [[validation gym - 002 - is a mesh with a material]]) end to end: collect → validate → report pass/fail per check. That gives a working, scope-limited answer to "does pipeline-as-code via pytest actually cover what Pyblish covers" before any decision to build a bespoke framework like pac2 again. If pytest's fixture/parametrize model turns out to hit the same issues (no plugin-to-action link, no severity model for warning vs error), that's the evidence needed to justify a custom tool — right now that evidence doesn't exist.

## links
- [[Pyblish issues]]
- [[Pyblish issue - dependency injection]]
- [[Pyblish issue - has no explicit plugin control]]
- [[Pyblish issue - action and plugin have no direct link]]
- [[Pyblish issue - inconsistent logic]]
- [[Pyblish issue - plugins are hardcoded to the project or studio]]
- [[Pyblish issue - warning vs error]]
- [[Pyblish issue - docs are confusing]]
- [[Pyblish issue - UI is not artist friendly]]
- [[Pyblish issue - development is slow]]
- [[pipeline as code]]
- [[review pac]]
- [[R&D Blender validation pipeline with pytest]]
- [[validation gym]]
