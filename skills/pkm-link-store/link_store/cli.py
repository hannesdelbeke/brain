"""CLI for pkm-link-store: sync, audit, and query."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .adapters import BoundaryPolicy, sync_claude_root, sync_git_repo
from .db import LinkStoreDB


def _parse_kv(spec: str) -> tuple[str, str]:
    name, sep, path = spec.partition("=")
    if not sep or not name.strip() or not path.strip():
        raise argparse.ArgumentTypeError(f"Expected NAME=PATH, got {spec!r}")
    return name.strip(), path.strip()


def cmd_sync(args: argparse.Namespace) -> dict:
    vault_roots = dict(_parse_kv(v) for v in args.vault)
    policy = BoundaryPolicy.from_args(
        allow_roots=args.allow_root,
        deny_roots=args.deny_root,
        vault_roots=vault_roots,
    )
    summary: dict = {"db": str(Path(args.db).expanduser()), "claude": [], "repos": []}
    with LinkStoreDB(args.db) as db:
        for root in args.claude_root:
            res = sync_claude_root(db, root, policy=policy)
            summary["claude"].append({"root": root, **res})
        for repo_spec in args.repo:
            rname, rpath = _parse_kv(repo_spec)
            res = sync_git_repo(
                db, rname, rpath, policy=policy, max_commits=args.max_commits
            )
            summary["repos"].append({"name": rname, "path": rpath, **res})
    return summary


def cmd_audit(args: argparse.Namespace) -> dict:
    with LinkStoreDB(args.db) as db:
        node_counts = {
            row["node_type"]: row["cnt"]
            for row in db.conn.execute(
                "SELECT node_type, COUNT(*) AS cnt FROM nodes WHERE expired_at IS NULL GROUP BY node_type"
            )
        }
        edge_counts = {
            row["rel"]: row["cnt"]
            for row in db.conn.execute(
                "SELECT rel, COUNT(*) AS cnt FROM edges WHERE expired_at IS NULL GROUP BY rel"
            )
        }
        expired_nodes = db.conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE expired_at IS NOT NULL"
        ).fetchone()[0]
        expired_edges = db.conn.execute(
            "SELECT COUNT(*) FROM edges WHERE expired_at IS NOT NULL"
        ).fetchone()[0]

        total_nodes = sum(node_counts.values())
        total_edges = sum(edge_counts.values())
        density = (
            (2.0 * total_edges) / (total_nodes * (total_nodes - 1))
            if total_nodes > 1
            else 0.0
        )

        hubs = [
            dict(row)
            for row in db.conn.execute(
                """
                SELECT n.id, n.node_type, n.title, COUNT(*) AS degree
                FROM (
                    SELECT src_id AS nid FROM edges WHERE expired_at IS NULL
                    UNION ALL
                    SELECT dst_id AS nid FROM edges WHERE expired_at IS NULL
                ) d
                JOIN nodes n ON n.id = d.nid
                GROUP BY n.id
                ORDER BY degree DESC
                LIMIT 15
                """
            )
        ]

        return {
            "db": str(db.db_path),
            "active_nodes": total_nodes,
            "active_edges": total_edges,
            "expired_nodes": expired_nodes,
            "expired_edges": expired_edges,
            "density": round(density, 6) if not math.isnan(density) else 0.0,
            "nodes_by_type": node_counts,
            "edges_by_rel": edge_counts,
            "top_hubs": hubs,
        }


def cmd_query(args: argparse.Namespace) -> dict:
    with LinkStoreDB(args.db) as db:
        node_id = db.resolve_alias(args.node) or args.node
        node = db.get_node(node_id)
        if not node:
            return {"error": f"node not found: {args.node!r}"}
        outbound = [
            dict(row)
            for row in db.conn.execute(
                """
                SELECT e.rel, e.dst_id, n.node_type AS dst_type, n.title AS dst_title,
                       e.valid_from, e.valid_to, e.source_adapter
                FROM edges e
                JOIN nodes n ON n.id = e.dst_id
                WHERE e.src_id = ? AND e.expired_at IS NULL
                ORDER BY e.rel, e.dst_id
                """,
                (node_id,),
            )
        ]
        inbound = [
            dict(row)
            for row in db.conn.execute(
                """
                SELECT e.rel, e.src_id, n.node_type AS src_type, n.title AS src_title,
                       e.valid_from, e.valid_to, e.source_adapter
                FROM edges e
                JOIN nodes n ON n.id = e.src_id
                WHERE e.dst_id = ? AND e.expired_at IS NULL
                ORDER BY e.rel, e.src_id
                """,
                (node_id,),
            )
        ]
        return {"node": node, "outbound": outbound, "inbound": inbound}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PKM Link Store CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="Ingest transcripts and git repos")
    p_sync.add_argument("--db", required=True, help="Path to SQLite link store DB")
    p_sync.add_argument("--claude-root", action="append", default=[])
    p_sync.add_argument("--repo", action="append", default=[], metavar="NAME=PATH")
    p_sync.add_argument("--vault", action="append", default=[], metavar="NAME=PATH")
    p_sync.add_argument("--allow-root", action="append", default=[])
    p_sync.add_argument("--deny-root", action="append", default=[])
    p_sync.add_argument("--max-commits", type=int, default=None)

    p_audit = sub.add_parser("audit", help="Audit graph counts, density, and hubs")
    p_audit.add_argument("--db", required=True)

    p_query = sub.add_parser("query", help="Query neighbors for a canonical ID or alias")
    p_query.add_argument("--db", required=True)
    p_query.add_argument("--node", required=True)

    args = parser.parse_args(argv)
    if args.command == "sync":
        out = cmd_sync(args)
    elif args.command == "audit":
        out = cmd_audit(args)
    else:
        out = cmd_query(args)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
