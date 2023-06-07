---
sentiment:
- 5
sentiment-hash: f979600e
sentiment-label:
- factual
tags:
- technical
---

Consider the two scenarios `div > span { }` vs. `div span { }`

Here, the ' ' (space) selects all the all the `<span>` elements inside `<div>` element even if they are nested inside more than one element. The `>` selects all the children of `<div>` element but if they are not inside another element.

[[CSS]]
