---
date: 2026-08-30
created: 2026-08-30
tags:
  - technical
  - pkm
  - search
  - agents
  - security
aliases:
  - 2026-08-30 sharing a vector index across people and orgs
  - shared vector database permissions
  - federated RAG for personal vaults
---

# Sharing a Vector Index across People and Orgs

A single-owner vector index like [[pkm metadata indexer]] has no permission problem: whoever runs the query owns everything in it. The moment a second person or org sits behind the same query, retrieval and access control become two separate systems that both have to hold. Industry writing calls this [the isolation paradox](https://www.alternates.ai/knowledge-hub/articles/federated-rag-secure-cross-org-knowledge-bots): partition data too aggressively for safety and the cross-source value that made semantic search worth it disappears; share too loosely and a friend's private journal or a company's confidential doc leaks into an answer it should never reach.

There are three shapes people actually build, not two. **Pool**: one shared index, every row tagged with an owner or ACL, every query gets a mandatory filter injected. **Silo**: one index per person or org, queried separately, results merged after. **Federated**: nothing centralizes at all, each side keeps its own store and answers queries against its own data under its own rules, with only the question and a filtered answer crossing the boundary. Two common asks — "connect me to a friend's index without their private journal" and "connect me to a company index kept current with its docs" — turn out to want different shapes.

## The enterprise case wants pool-with-synced-ACL, and it already exists

[Glean](https://docs.glean.com/connectors/connectors-power-glean) and [Onyx](https://onyx.app/insights/enterprise-rag-platforms-2026) (formerly Danswer) are the production answer to "connect to a company index kept up to date with repos, docs and permissions." Both sync the source system's own permission model rather than a copy an admin maintains by hand: connectors fetch content and the ACL (or equivalent) from Confluence, Slack, GitHub, Drive and so on, so a query only ever surfaces what the querying user could already open at the source. Glean additionally runs zero-copy — the documents stay where they live and only vectors plus metadata get cached — which sidesteps a whole class of "now there's a second stale copy of the confidential wiki" problems.

The failure mode worth knowing before building anything: [filtering that happens after the similarity search runs, not before](https://www.osohq.com/post/right-approach-to-authorization-in-rag). A naive implementation retrieves top-k over the whole index and then discards what the caller can't see, which both leaks relevance signal (you can tell something exists even if you can't read it) and degrades quality (the slots the ACL blocked are gone, not backfilled). The pattern that avoids it pushes the permission check into the retrieval call itself, either as a mandatory filter alongside the ANN search or by asking the source system's own auth API before returning a hit, per [AWS's writeup](https://aws.amazon.com/blogs/security/authorizing-access-to-data-with-rag-implementations/). For a company index this is the honest scope: pull a real ACL from whatever already gates the repos and docs, tag rows with it, and make the filter mandatory rather than best-effort — a metadata column and a query-time join, not a new database.

## The friend case wants federation, not a shared pool

This is a materially different problem: there is no shared employer to define the ACL, and "I shouldn't see his private journal" needs to fail closed even if the two people never agree on a permission schema. The closest working prototype is [SocialGenPod](https://arxiv.org/pdf/2403.10408), built on [Solid pods](https://repolex.ai/blog/2025/11/08/EVERYTHING-YOU-SHOULD-KNOW-ABOUT-SOLID-PODS/): each person's data stays in their own pod under their own WebACL rules, and a query from one person's agent only ever reaches what the other person's pod already agreed to expose, enforced at the data owner's end rather than the querier's. Nothing centralizes, so there's no single store to breach and no reconciliation of two people's differing ideas of "private."

Mapped onto a tool like this one, the friend's corpus isn't a filtered view inside one shared index — it's the friend's own copy of the search daemon, running their own indexer over their own vault, with their own decision about which folders it walks. A query crosses the boundary as a network call to their daemon; their daemon enforces the boundary, and if it's down or misconfigured the query returns nothing rather than everything, which is the fail-closed property a shared pool with a missed filter doesn't have. Two federated-search research lines go further than this: [FRAG](https://arxiv.org/html/2410.13272v1) runs encrypted ANN search so neither side sees the other's raw vectors or queries, and [Trans-RAG](https://link.springer.com/chapter/10.1007/978-981-92-0372-7_35) keeps per-org vector spaces near-orthogonal so a cross-org query can't accidentally resolve into the wrong corpus. Both solve for mutual distrust between orgs that don't know each other, a stronger requirement than two friends who already trust each other's intent and only need the mechanical guarantee that one folder isn't walked.

## MCP is already the right shape for this

MCP already has the isolation property this needs by default: a client holds one connection per server, and [that one-to-one shape is called out as a security boundary in its own right](https://codilime.com/blog/model-context-protocol-explained/) — no context or permission crosses from one server to another inside the protocol. So "connect to a friend's vector database" and "connect to a company's vector database" are the same primitive as any other MCP connector: a second server, not a merged index. The friend runs their own daemon over the subset of their vault they choose to expose, the company runs one over its repos and docs synced from whatever already gates them, and an agent holds several servers instead of one, each answering only for its own corpus under its own rules. The thing worth avoiding, per [MCP's own token-passthrough warning](https://www.wiz.io/academy/ai-security/model-context-protocol-security), is letting a credential meant for one server get forwarded to another — each server needs its own scoped token.

## What this means in practice

A company connector is a schema change on an existing indexer: an ACL column and a mandatory filter, not a new database. A friend connector isn't a schema change at all — it's the friend running the same kind of daemon and a second MCP server pointed at theirs. The two "connect to X's vector database" asks read as one thing but resolve to two different architectures, and building the pooled version for the friend case would be strictly worse than what federation already gives for free: fail-closed instead of fail-open, and no reconciliation of two people's privacy expectations into one schema.

## Related

- [[pkm metadata indexer]] — the single-owner index this note extends past one person
- [[retrieval augmented generation]] — feeding an LLM passages fetched at query time instead of training them in
