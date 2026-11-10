"""Generate URL-duplicate candidates without modifying source records."""
from __future__ import annotations

import argparse
import csv
import hashlib
import ipaddress
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REPO = Path(__file__).resolve().parents[2]
INPUT_DEFAULT = REPO / "1_du_lieu_chinh" / "vn_labor_news_dataset.csv"
OUTPUT_DEFAULT = REPO / "5_process" / "data" / "interim" / "url_duplicate_candidates.csv"
REPORT_DEFAULT = REPO / "5_process" / "reports" / "url_duplicate_report.json"

DETECTOR_VERSION = "1.0.0"
METHOD = "url_normalization_v1"
DUPLICATE_TYPE = "URL_DUPLICATE"
REVIEW_STATUS = "REVIEW_REQUIRED"
REQUIRED_COLUMNS = ("article_id", "source_url")
OUTPUT_COLUMNS = (
    "article_id_1",
    "article_id_2",
    "original_url_1",
    "original_url_2",
    "normalized_url",
    "duplicate_type",
    "method",
    "reason",
    "detector_version",
    "review_status",
)

_TRACKING_EXACT = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "yclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "zarsrc",
}
_TRACKING_PREFIXES = ("utm_",)
_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _normalized_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        try:
            ascii_host = host.encode("idna").decode("ascii").lower()
        except UnicodeError:
            return ""
        if not ascii_host or "." not in ascii_host:
            return ""
        labels = ascii_host.split(".")
        if any(not _DNS_LABEL.fullmatch(label) for label in labels):
            return ""
        return ascii_host

    if isinstance(address, ipaddress.IPv6Address):
        return f"[{address.compressed}]"
    return address.compressed


def normalize_url(value: str) -> str:
    """Return a conservative comparison key, or an empty string for invalid URLs.

    HTTP(S) schemes, host case, a leading ``www.``, fragments, recognized tracking
    parameters, and a trailing path slash are normalized. Other query parameters,
    including ``ref``, are retained in their original order.
    """
    if not isinstance(value, str):
        return ""
    raw = value.strip()
    if not raw or any(char.isspace() or ord(char) < 0x20 for char in raw):
        return ""

    try:
        parts = urlsplit(raw)
        if parts.scheme.lower() not in {"http", "https"}:
            return ""
        if parts.username is not None or parts.password is not None:
            return ""
        host = parts.hostname
        port = parts.port
    except ValueError:
        return ""

    if not host:
        return ""
    normalized_host = _normalized_host(host)
    if not normalized_host:
        return ""
    if normalized_host.startswith("www.") and not normalized_host.startswith("["):
        normalized_host = normalized_host[4:]
        if not normalized_host:
            return ""

    scheme = parts.scheme.lower()
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        normalized_host = f"{normalized_host}:{port}"

    path = parts.path.rstrip("/")
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_EXACT
        and not key.lower().startswith(_TRACKING_PREFIXES)
    ]
    normalized_query = urlencode(query, doseq=True)
    return urlunsplit(("https", normalized_host, path, normalized_query, ""))


def find_candidates(records: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """Return pairwise URL candidates and the number of records with invalid URLs."""
    seen_article_ids: set[str] = set()
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    invalid_url_count = 0

    for row_number, record in enumerate(records, start=2):
        raw_article_id = record.get("article_id") or ""
        article_id = raw_article_id.strip() if isinstance(raw_article_id, str) else ""
        if not article_id:
            raise ValueError(f"CSV row {row_number}: article_id must not be blank.")
        if article_id in seen_article_ids:
            raise ValueError(f"CSV row {row_number}: duplicate article_id {article_id!r}.")
        seen_article_ids.add(article_id)

        original_url = record.get("source_url") or ""
        normalized_url = normalize_url(original_url)
        if not normalized_url:
            invalid_url_count += 1
            continue
        grouped[normalized_url].append(
            {
                "article_id": article_id,
                "original_url": original_url,
            }
        )

    candidates = []
    for normalized_url, members in sorted(grouped.items()):
        members.sort(key=lambda member: member["article_id"])
        for first, second in combinations(members, 2):
            candidates.append(
                {
                    "article_id_1": first["article_id"],
                    "article_id_2": second["article_id"],
                    "original_url_1": first["original_url"],
                    "original_url_2": second["original_url"],
                    "normalized_url": normalized_url,
                    "duplicate_type": DUPLICATE_TYPE,
                    "method": METHOD,
                    "reason": (
                        "source_url values normalize to the same comparison URL; "
                        "this is a candidate and requires human review."
                    ),
                    "detector_version": DETECTOR_VERSION,
                    "review_status": REVIEW_STATUS,
                }
            )
    return candidates, invalid_url_count


def detect_from_csv(input_path: Path, output_path: Path) -> tuple[int, int, int, str]:
    """Read the source CSV and write only the derived candidate file."""
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Output path must not overwrite the input CSV.")

    input_hash = _file_sha256(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {missing}")
        records = list(reader)
    if input_hash != _file_sha256(input_path):
        raise ValueError("Input CSV changed while being read; no output was written.")

    candidates, invalid_url_count = find_candidates(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(candidates)
    return len(candidates), invalid_url_count, len(records), input_hash


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    invalid_url_count: int,
    candidate_count: int,
    input_article_count: int,
    input_sha256: str,
) -> None:
    resolved_paths = {path.resolve() for path in (input_path, output_path, report_path)}
    if len(resolved_paths) != 3:
        raise ValueError("Input, candidate output, and JSON report paths must be different.")
    if _file_sha256(input_path) != input_sha256:
        raise ValueError("Input CSV changed after candidate generation; no report was written.")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path.resolve()),
        "input_sha256": input_sha256,
        "input_article_count": input_article_count,
        "candidate_file": str(output_path.resolve()),
        "candidate_sha256": _file_sha256(output_path),
        "detector_version": DETECTOR_VERSION,
        "method": METHOD,
        "candidate_pair_count": candidate_count,
        "invalid_url_count": invalid_url_count,
        "status": "REVIEW_REQUIRED" if candidate_count else "NO_CANDIDATES_FOUND",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args(argv)

    try:
        if len(
            {
                args.input.resolve(),
                args.output.resolve(),
                args.report.resolve(),
            }
        ) != 3:
            raise ValueError("Input, candidate output, and JSON report paths must be different.")
        (
            candidate_count,
            invalid_url_count,
            input_article_count,
            input_sha256,
        ) = detect_from_csv(args.input, args.output)
        _write_report(
            args.input,
            args.output,
            args.report,
            invalid_url_count,
            candidate_count,
            input_article_count,
            input_sha256,
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"URL duplicate detection failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote {candidate_count} URL duplicate candidates to {args.output}; "
        f"invalid URLs skipped: {invalid_url_count}; report: {args.report}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
