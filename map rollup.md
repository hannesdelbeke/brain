---
tags:
  - architecture
  - algorithms
  - data
---
An [OLAP](https://en.wikipedia.org/wiki/Online_analytical_processing) aggregation operation that climbs a dimension hierarchy, not a distributed computing model.

## What It Does
Sums, counts, averages, or takes min/max of a measure at each coarser level of a hierarchy: day into month into year, city into state into country. The opposite operation, drill-down, breaks a summary back into its detail. SQL exposes it directly as `GROUP BY ROLLUP(...)`, which returns the normal grouped rows plus a subtotal row for each prefix of the column list and one grand total row.

Salesforce uses the same word for a narrower case: a roll-up summary field on a parent object that sums, counts, or finds min/max across its child records, recalculated whenever a child record changes.

## Why It Gets Mixed Up With Map-Reduce
Both reduce many rows to fewer, and both can run inside a big-data engine — [Spark](https://spark.apache.org/)'s `ROLLUP` clause is planned and executed through the same distributed dataframe machinery Spark uses for everything else. But rollup is a query-level aggregation semantic, an answer to "sum this at every level of a hierarchy", while [[map-reduce]] is a general execution model for turning arbitrary computation into parallel map and reduce steps. A rollup can be implemented on top of map-reduce; map-reduce is not a kind of rollup.

### Related
- [[map-reduce]] — the distributed processing model it gets confused with.
- [[hierarchical map-reduce note rollup]] — a different, unrelated sense of "rollup": batching leaf summaries into a tree, not climbing a data hierarchy.
