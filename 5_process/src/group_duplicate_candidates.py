"""Group duplicate candidates into connected components for manual review."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
INTERIM = REPO / "5_process" / "data" / "interim"
REPORTS = REPO / "5_process" / "reports"
URL_CANDIDATES = INTERIM / "url_duplicate_candidates.csv"
EXACT_CANDIDATES = INTERIM / "exact_duplicate_candidates.csv"
NEAR_CANDIDATES = INTERIM / "near_duplicate_candidates.csv"
OUTPUT_DEFAULT = INTERIM / "duplicate_groups.csv"
REPORT_DEFAULT = REPORTS / "duplicate_grouping_report.json"
SOURCE_INPUTS = (URL_CANDIDATES, EXACT_CANDIDATES, NEAR_CANDIDATES)
PROTECTED_ARTIFACTS = (
    REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv",
    URL_CANDIDATES,
    EXACT_CANDIDATES,
    NEAR_CANDIDATES,
    REPORTS / "url_duplicate_report.json",
    REPORTS / "exact_duplicate_report.json",
    REPORTS / "near_duplicate_report.json",
)

GROUPING_VERSION = "1.0.0"
REVIEW_STATUS = "REVIEW_REQUIRED"
TYPE_BY_SOURCE = {
    URL_CANDIDATES: "URL_DUPLICATE",
    EXACT_CANDIDATES: "EXACT_CONTENT_DUPLICATE",
    NEAR_CANDIDATES: "NEAR_DUPLICATE",
}
ALLOWED_TYPES = {*TYPE_BY_SOURCE.values(), "VERSION_DUPLICATE"}
PAIR_COLUMNS = ("article_id_1", "article_id_2")
OUTPUT_COLUMNS = (
    "duplicate_group_id",
    "article_id",
    "group_size",
    "duplicate_types",
    "detection_methods",
    "review_status",
    "reason",
    "candidate_pair_count",
    "candidate_pairs_json",
)


class UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self._parent.setdefault(item, item)

    def find(self, item: str) -> str:
        self.add(item)
        if self._parent[item] != item:
            self._parent[item] = self.find(self._parent[item])
        return self._parent[item]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            first, second = sorted((left_root, right_root))
            self._parent[second] = first


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Candidate input does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"{path}: candidate CSV must have a header.")
        return list(reader)


def _required_id(value: Any, path: Path, row_number: int, field: str) -> str:
    article_id = value.strip() if isinstance(value, str) else ""
    if not article_id:
        raise ValueError(f"{path.name} row {row_number}: {field} must not be blank.")
    return article_id


def _candidate_evidence(
    *,
    pair: tuple[str, str],
    duplicate_type: str,
    method: str,
    source_file: str,
    row: dict[str, str],
) -> dict[str, Any]:
    if duplicate_type not in ALLOWED_TYPES:
        raise ValueError(f"{source_file}: unsupported duplicate_type {duplicate_type!r}.")
    if not isinstance(method, str) or not method.strip():
        raise ValueError(f"{source_file}: method must not be blank.")

    evidence: dict[str, Any] = {
        "article_id_1": pair[0],
        "article_id_2": pair[1],
        "duplicate_type": duplicate_type,
        "method": method.strip(),
        "source_file": source_file,
    }
    for field in ("reason", "similarity_score", "threshold", "normalized_url", "content_hash"):
        value = row.get(field, "")
        if value not in (None, ""):
            evidence[field] = value
    if duplicate_type == "VERSION_DUPLICATE":
        raw_version_evidence = row.get("version_evidence", "")
        version_evidence = (
            raw_version_evidence.strip()
            if isinstance(raw_version_evidence, str)
            else ""
        )
        if not version_evidence:
            raise ValueError(
                f"{source_file}: VERSION_DUPLICATE requires explicit version_evidence."
            )
        evidence["version_evidence"] = version_evidence
    return evidence


def build_groups(
    source_paths: tuple[Path, Path, Path] = SOURCE_INPUTS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read candidate sources and group their article relationships transitively."""
    if len(source_paths) != 3:
        raise ValueError("Exactly three candidate source files are required.")

    union_find = UnionFind()
    edge_evidence: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    evidence_signatures: dict[tuple[str, str], set[str]] = defaultdict(set)
    candidate_rows_by_source: dict[str, int] = {}
    raw_candidate_pair_count = 0

    for path in source_paths:
        expected_type = next(
            (value for source, value in TYPE_BY_SOURCE.items() if source.name == path.name),
            None,
        )
        if expected_type is None:
            raise ValueError(f"Unrecognized candidate source path: {path}")
        rows = _read_csv(path)
        candidate_rows_by_source[path.name] = len(rows)

        if path.name == EXACT_CANDIDATES.name:
            exact_required = {
                "duplicate_group_id",
                "article_id",
                "content_hash",
                "duplicate_type",
                "method",
            }
            exact_header = set(rows[0].keys()) if rows else set(_read_header(path))
            missing = sorted(exact_required - exact_header)
            if missing:
                raise ValueError(f"{path.name}: missing required columns: {missing}.")
            groups: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
            for row_number, row in enumerate(rows, start=2):
                group_id = _required_id(
                    row.get("duplicate_group_id"), path, row_number, "duplicate_group_id"
                )
                article_id = _required_id(row.get("article_id"), path, row_number, "article_id")
                if row.get("duplicate_type") != expected_type:
                    raise ValueError(
                        f"{path.name} row {row_number}: duplicate_type must be {expected_type}."
                    )
                groups[group_id].append((row_number, row))

            for input_group_id, members in groups.items():
                member_ids = [
                    _required_id(row.get("article_id"), path, row_number, "article_id")
                    for row_number, row in members
                ]
                if len(member_ids) < 2:
                    raise ValueError(
                        f"{path.name}: exact candidate group {input_group_id!r} "
                        "must contain at least two articles."
                    )
                if len(member_ids) != len(set(member_ids)):
                    raise ValueError(
                        f"{path.name}: duplicate article_id within exact candidate group "
                        f"{input_group_id!r}."
                    )
                hashes = {row.get("content_hash", "") for _, row in members}
                if len(hashes) != 1:
                    raise ValueError(
                        f"{path.name}: content_hash differs within exact candidate group "
                        f"{input_group_id!r}."
                    )
                for article_id in member_ids:
                    union_find.add(article_id)
                methods = {row.get("method", "") for _, row in members}
                if len(methods) != 1:
                    raise ValueError(
                        f"{path.name}: method differs within exact candidate group "
                        f"{input_group_id!r}."
                    )
                for (left_id, left_entry), (right_id, right_entry) in combinations(members, 2):
                    left = _required_id(left_entry.get("article_id"), path, left_id, "article_id")
                    right = _required_id(right_entry.get("article_id"), path, right_id, "article_id")
                    pair = tuple(sorted((left, right)))
                    evidence = _candidate_evidence(
                        pair=pair,
                        duplicate_type=expected_type,
                        method=left_entry.get("method", ""),
                        source_file=path.name,
                        row=left_entry,
                    )
                    evidence["source_group_id"] = input_group_id
                    edge_evidence[pair].append(evidence)
                    signature = json.dumps(evidence, sort_keys=True, ensure_ascii=True)
                    evidence_signatures[pair].add(signature)
                    union_find.union(*pair)
                    raw_candidate_pair_count += 1
            continue

        required_fields = set(PAIR_COLUMNS) | {"duplicate_type", "method"}
        for field in required_fields:
            if field not in (rows[0].keys() if rows else _read_header(path)):
                raise ValueError(f"{path.name}: missing required column {field!r}.")
        for row_number, row in enumerate(rows, start=2):
            article_id_1 = _required_id(row.get("article_id_1"), path, row_number, "article_id_1")
            article_id_2 = _required_id(row.get("article_id_2"), path, row_number, "article_id_2")
            if article_id_1 == article_id_2:
                raise ValueError(f"{path.name} row {row_number}: self-pair is not allowed.")
            duplicate_type = row.get("duplicate_type", "")
            if duplicate_type not in {expected_type, "VERSION_DUPLICATE"}:
                raise ValueError(
                    f"{path.name} row {row_number}: duplicate_type must be "
                    f"{expected_type} or VERSION_DUPLICATE."
                )
            pair = tuple(sorted((article_id_1, article_id_2)))
            evidence = _candidate_evidence(
                pair=pair,
                duplicate_type=duplicate_type,
                method=row.get("method", ""),
                source_file=path.name,
                row=row,
            )
            signature = json.dumps(evidence, sort_keys=True, ensure_ascii=True)
            if signature not in evidence_signatures[pair]:
                edge_evidence[pair].append(evidence)
                evidence_signatures[pair].add(signature)
            union_find.union(*pair)
            raw_candidate_pair_count += 1

    components: dict[str, set[str]] = defaultdict(set)
    for article_id in union_find._parent:
        components[union_find.find(article_id)].add(article_id)
    ordered_components = sorted(
        (sorted(members) for members in components.values() if len(members) >= 2),
        key=lambda members: members,
    )

    output_rows: list[dict[str, Any]] = []
    group_size_distribution: Counter[int] = Counter()
    duplicate_type_distribution: Counter[str] = Counter()
    for group_number, article_ids in enumerate(ordered_components, start=1):
        group_id = f"DUP-GROUP-{group_number:06d}"
        member_set = set(article_ids)
        group_edges = {
            pair: evidence
            for pair, evidence in edge_evidence.items()
            if pair[0] in member_set and pair[1] in member_set
        }
        group_types = sorted(
            {evidence["duplicate_type"] for items in group_edges.values() for evidence in items}
        )
        methods = sorted({evidence["method"] for items in group_edges.values() for evidence in items})
        group_evidence = [
            evidence
            for pair in sorted(group_edges)
            for evidence in sorted(
                group_edges[pair],
                key=lambda item: (item["source_file"], item["duplicate_type"], item["method"]),
            )
        ]
        reason = (
            f"Connected component of {len(article_ids)} articles linked by "
            f"{len(group_edges)} unique candidate pairs; types: {', '.join(group_types)}. "
            "Grouping is for review only; no article is confirmed, removed, edited, or merged."
        )
        group_size_distribution[len(article_ids)] += 1
        for duplicate_type in group_types:
            duplicate_type_distribution[duplicate_type] += 1
        evidence_json = json.dumps(group_evidence, ensure_ascii=True, separators=(",", ":"))
        for article_id in article_ids:
            output_rows.append(
                {
                    "duplicate_group_id": group_id,
                    "article_id": article_id,
                    "group_size": len(article_ids),
                    "duplicate_types": "; ".join(group_types),
                    "detection_methods": "; ".join(methods),
                    "review_status": REVIEW_STATUS,
                    "reason": reason,
                    "candidate_pair_count": len(group_edges),
                    "candidate_pairs_json": evidence_json,
                }
            )

    unique_pair_count = len(edge_evidence)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_candidate_pairs": unique_pair_count,
        "raw_candidate_pair_records": raw_candidate_pair_count,
        "candidate_rows_by_source": candidate_rows_by_source,
        "total_groups": len(ordered_components),
        "total_articles_in_groups": len(output_rows),
        "group_size_distribution": {
            str(size): count for size, count in sorted(group_size_distribution.items())
        },
        "duplicate_type_distribution": dict(sorted(duplicate_type_distribution.items())),
        "candidate_pair_type_distribution": _pair_type_distribution(edge_evidence),
        "detector_version": GROUPING_VERSION,
        "grouping_method": "connected_components_union_find",
        "review_status": REVIEW_STATUS,
        "version_duplicate_evidence_available": duplicate_type_distribution.get(
            "VERSION_DUPLICATE", 0
        )
        > 0,
    }
    return output_rows, report


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        return next(reader, [])


def _pair_type_distribution(
    edge_evidence: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for evidence_items in edge_evidence.values():
        for duplicate_type in {
            evidence["duplicate_type"] for evidence in evidence_items
        }:
            counts[duplicate_type] += 1
    return dict(sorted(counts.items()))


def write_outputs(
    output_rows: list[dict[str, Any]],
    report: dict[str, Any],
    output_path: Path = OUTPUT_DEFAULT,
    report_path: Path = REPORT_DEFAULT,
    protected_paths: tuple[Path, ...] = PROTECTED_ARTIFACTS,
) -> None:
    resolved_output, resolved_report = output_path.resolve(), report_path.resolve()
    resolved_protected = {path.resolve() for path in protected_paths}
    if resolved_output in resolved_protected or resolved_report in resolved_protected:
        raise ValueError("Grouping outputs must not overwrite source or P4.02-P4.04 artifacts.")
    if resolved_output == resolved_report:
        raise ValueError("CSV and JSON output paths must be different.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def group_from_files(
    source_paths: tuple[Path, Path, Path] = SOURCE_INPUTS,
    output_path: Path = OUTPUT_DEFAULT,
    report_path: Path = REPORT_DEFAULT,
) -> dict[str, Any]:
    output_rows, report = build_groups(source_paths)
    protected_paths = tuple({*PROTECTED_ARTIFACTS, *source_paths})
    write_outputs(output_rows, report, output_path, report_path, protected_paths)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-candidates", type=Path, default=URL_CANDIDATES)
    parser.add_argument("--exact-candidates", type=Path, default=EXACT_CANDIDATES)
    parser.add_argument("--near-candidates", type=Path, default=NEAR_CANDIDATES)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args(argv)

    try:
        report = group_from_files(
            (args.url_candidates, args.exact_candidates, args.near_candidates),
            args.output,
            args.report,
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Duplicate grouping failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Grouped {report['total_candidate_pairs']} unique candidate pairs into "
        f"{report['total_groups']} groups ({report['total_articles_in_groups']} articles). "
        f"CSV: {args.output}; JSON: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
