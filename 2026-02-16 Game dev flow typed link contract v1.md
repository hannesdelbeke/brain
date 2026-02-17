⚠️ IMO this whole summary is kinda shit
I asked [[OpenAI Codex]] to analyze [[Game dev flow]].
It assumed I want to combine my whole personal vault with a unity repo, instead of talking about general project documentation practices.


---
## Feedback summary
1. The current flow mixes 3 link domains into one:
- knowledge links (notes/docs)
- runtime/action links (launch tools)
- tracking links (tasks/comments)

These should have separate source-of-truth rules. See [[Game dev flow]].

2. **The write path in Unity is still too manual**.
- This is already called out in [[2025 Unity notes feedback]].
- **If links are not near-zero friction to write, flow breaks.**

2. **[[Temporal integrity]] is unresolved**.
- Branch/history breakage and link integrity concerns are noted in [[Game dev flow]] and [[consider 2 sources of truth]].
- **Flow is not complete if links fail across rollback, branches, and history**.

4. Distribution and discovery are split.
- Distribution constraints are in [[tool distribution]].
- Discovery/launch is in [[tool launcher]], [[unimenu]], and [[buttonizer]].
- These should be unified into one contract.

5. Existing notes already suggest the direction.
- Keep docs close to assets and compute backlinks.
- See [[Unity notes]], [[Unity note editor]], [[backlink]], and [[consider 2 sources of truth]].

## How to achieve flow
1. Define a typed link contract.
2. Remove manual URI typing.
3. Compute backlinks via indexer, not by hand.
4. Add branch/commit context to links.

## Goal
Achieve smooth flow between [[Unity]], [[Obsidian]], and tool/task systems by standardizing links and removing manual link-writing friction.

## Core principle
One low-friction authoring surface + one typed link contract + one background resolver.

For asset-centered workflows, the canonical source should be Unity-side note metadata.
External systems are projections/sync targets, not primary truth.

## Link contract v1
Use only these link types:
- `doc`: link asset to documentation/note
- `tool`: link asset to executable command/tool action
- `task`: link asset to ticket/task item
- `related_asset`: link asset to other assets/scenes/prefabs

Each link record:
```json
{
  "id": "uuid",
  "type": "doc|tool|task|related_asset",
  "from": {
    "kind": "unity_asset",
    "project": "project-id",
    "assetGuid": "unity-guid"
  },
  "to": {
    "kind": "obsidian|unity_asset|url|task",
    "target": "obsidian://... | unity://... | https://... | jira://...",
    "stableId": "optional-external-id"
  },
  "reason": "short why-link sentence",
  "state": {
    "branch": "main",
    "commit": "optional-git-sha",
    "createdAt": "ISO-8601",
    "updatedAt": "ISO-8601"
  },
  "visibility": "project|team|private"
}
```

## Authoring UX rules
- Never require manual URI typing in editor fields.
- Use actions only: `Copy link`, `Paste link`, `Create linked note`, `Create task`.
- Always store a short reason for the link (why this relation exists).
- Default to nearest context: write links from selected asset inspector/panel.

## Backlink model
[[backlink|Backlinks]] are computed by an indexer from forward links.
Do not store backlinks as primary data.

Indexer outputs:
- `asset -> linked docs/tools/tasks/assets`
- `note/task/url -> inbound assets`
- unresolved links report

This mirrors the model in [[consider 2 sources of truth]] while keeping one canonical forward-link source.

## Temporal integrity rules
To reduce branch/history breakage:
- Store `branch` and optional `commit` in each link record. 
  %% this only works for git %%
- Resolve links relative to current branch first.
- If target missing on current branch, show fallback options:
  - open last-known target
  - open historical target at recorded commit
  - relink target
%% this seems to me to add a lot of complexity, that e.g. can cause issues when merging conflicts %%
## Sync policy
- Unity metadata is [[canonical]] for asset-centered links.
- Projections:
	- Obsidian note embeds/resolved links
	- task system references
	- launcher/discovery views
- Sync should be idempotent and append-only where possible.
- Keep conflict logs human-readable.

## Integration checklist (v1)
1. Add typed link model to [[Unity note editor]] storage.
2. Add UI to create links without raw URI typing.
3. Add `reason` field with lightweight prompt.
4. Implement indexer to compute backlinks and unresolved links.
5. Add branch/commit fields and resolver behavior.
6. Add projection writer for [[link Unity to Obsidian]] and [[link Obsidian to Unity]].
7. Add launcher integration for `tool` links via [[plugget]] / [[tool launcher]] / [[Unity tool launcher]].
8. Add install-on-demand flow for unresolved tools (distribution + launch in one path).
9. Add weekly integrity job: broken links, orphan assets, stale tasks.
10. Document this in [[documentation]] and keep one short usage guide for artists.

## Success criteria
- Creating a valid cross-system link takes <= 2 clicks from selected asset.
- Zero manual URI typing in normal workflow.
- Backlinks visible in Unity and Obsidian views.
- Broken links are surfaced automatically.
- Tool link can install and run in the same flow.

## Notes
This intentionally uses a hybrid approach:
- internal IDs/wikilink-like stable links for owned systems
- URL links for external systems
matching the conclusion in [[consider 2 sources of truth]].
