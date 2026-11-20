#!/usr/bin/env python3
"""Prepare immutable revision baselines and compare actual GDD JSON changes."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from compile_context import depth_contract, _profile_reference_contract, _kind_reference_contract
from document_source import LegacyDocument, data_digest, digest, legacy_evidence, load_document
from kind_contracts import KIND_CONTRACTS
from profile_contracts import PROFILE_RULES


def write_new(path: Path, value: Any, *, markdown: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = value if markdown else json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    for index in range(1, 10000):
        candidate = path if index == 1 else path.with_name(f"{path.stem}-{index}{path.suffix}")
        try:
            with candidate.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            return str(candidate.resolve())
        except FileExistsError:
            continue
    raise OSError(f"no available output name for {path}")


def revision_context(data: dict[str, Any], request: str) -> str:
    document = data["document"]
    profile = document.get("profile")
    if profile not in PROFILE_RULES:
        raise ValueError("source needs a supported document.profile before revision")
    kind = document.get("kind")
    sections = [item["id"] for item in data["sections"]]
    canonical = [item for item in sections if item in PROFILE_RULES[profile]["allowed_ids"]]
    contract = _profile_reference_contract(profile, canonical)
    lines = ["# 기존 문서 수정", "", "## 사용자 변경 요청", "", request,
             "", "## 원본 기준", "", f"- 제목: {document.get('title', '')}",
             f"- profile: {profile}; kind: {kind or 'generic'}", "- 섹션: " + ", ".join(sections),
             "- 원본·snapshot은 보존하고 candidate만 수정한다. 기존 결정·논리 ID·출처·미정 상태를 기준으로 삼는다.",
             "- 변경 위치, 요청 이유, 파생 영향, 유지할 결정을 먼저 짧게 정리한다. 새 scaffold로 원본을 대체하지 않는다.",
             "- 변경된 규칙을 인용한 표·도식·수치 예제·UI 표시·수용조건을 찾아 일치시킨다.",
             "- 관련 문서가 제공되었으면 실제 참조를 확인한다. 미제공 연계 문서는 검토 필요로 남긴다.",
             "- 요청과 무관한 문체·내용 개편은 하지 않는다. 범위 변경은 사용자 요청에 근거하고 명시한다.",
             "", "## 현재 범위의 완료 조건", ""]
    lines.extend(f"- {item['id']}: {item['minimum_completion']}" for item in contract["sections"])
    if kind:
        if kind not in KIND_CONTRACTS or KIND_CONTRACTS[kind]["profile"] != profile:
            raise ValueError("source kind/profile mapping is invalid")
        detail = _kind_reference_contract(kind)
        lines.extend(["", "## 문서 고유 결정", "", detail["must_answer"], detail["done_when"]])
    lines.extend(["", "## 변경 부분의 기획 깊이", "", depth_contract(profile), "",
                  "## 검토", "", "references/revision-workflow.md와 design-depth.md의 review 기준으로 실제 차이를 검토한다.",
                  "자동 비교는 구조·내용 차이만 보고하며 기획의 타당성이나 영향 검토 완료를 보증하지 않는다."])
    return "\n".join(lines) + "\n"


def prepare(source: Path, request: str, output_dir: Path) -> dict[str, Any]:
    if not request.strip():
        raise ValueError("revision request must not be empty")
    try:
        data = load_document(source)
    except LegacyDocument as error:
        evidence = legacy_evidence(source)
        evidence["request"] = request
        evidence["reason"] = str(error)
        evidence_path = write_new(output_dir / "reconstruction-evidence.json", evidence)
        return {"status": "needs-reconstruction", "evidence": evidence_path,
                "message": "Find matching original JSON first; otherwise reconcile the original into baseline JSON before editing."}
    if data["document"].get("profile") not in PROFILE_RULES:
        evidence_path = write_new(output_dir / "reconstruction-evidence.json", {
            "source": str(source.resolve()), "request": request, "document_data": data,
            "reason": "Legacy source has no supported document.profile; classify from the actual content and preserve its decisions when mapping to the current schema.",
        })
        return {"status": "needs-reconstruction", "evidence": evidence_path,
                "message": "Reconcile legacy metadata and section mapping into a separate baseline; do not replace the content with a blank scaffold."}
    context = revision_context(data, request)
    snapshot = write_new(output_dir / "baseline.json", data)
    candidate = write_new(output_dir / "candidate.json", copy.deepcopy(data))
    context_path = write_new(output_dir / "revision-context.md", context, markdown=True)
    manifest = {"status": "ready", "source": str(source.resolve()),
                "source_sha256": digest(source.read_text(encoding="utf-8-sig")),
                "baseline_sha256": data_digest(data),
                "baseline": snapshot, "candidate": candidate, "context": context_path}
    manifest["manifest"] = write_new(output_dir / "revision-manifest.json", manifest)
    return manifest


def read_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if (not isinstance(manifest, dict) or manifest.get("status") != "ready"
            or not all(isinstance(manifest.get(key), str) and manifest[key]
                       for key in ("source", "source_sha256", "baseline", "candidate"))):
        raise ValueError(f"Invalid revision manifest: {path}")
    return manifest


def find_preparation(baseline: Path, candidate: Path) -> dict[str, Any] | None:
    """Find an older path-based caller's preparation, including numbered retries."""
    selected = {baseline.resolve(), candidate.resolve()}
    directories = {p.parent for p in selected if p.stem.split("-")[0] in {"baseline", "candidate"}}
    unreadable = None
    for directory in directories:
        for path in directory.glob("revision-manifest*.json"):
            try:
                record = read_manifest(path)
            except (ValueError, OSError):
                unreadable = path
                continue
            if any(Path(record[key]).resolve() in selected for key in ("baseline", "candidate")):
                return record
    if unreadable is not None:
        raise ValueError(f"Cannot identify the revision pair; check the manifest: {unreadable}")
    return None


def load_comparison(manifest_path: Path | None, baseline: Path | None,
                    candidate: Path | None) -> tuple[dict[str, Any], dict[str, Any], str]:
    if manifest_path is None:
        if baseline is None or candidate is None:
            raise ValueError("compare requires --manifest or both --baseline and --updated")
        manifest = find_preparation(baseline, candidate)
        if manifest is None:
            return load_document(baseline), load_document(candidate), "standalone"
    else:
        manifest = read_manifest(manifest_path)

    recorded_baseline = Path(manifest["baseline"]).resolve()
    recorded_candidate = Path(manifest["candidate"]).resolve()
    if ((baseline is not None and baseline.resolve() != recorded_baseline)
            or (candidate is not None and candidate.resolve() != recorded_candidate)
            or recorded_baseline == recorded_candidate):
        raise ValueError("Baseline and candidate must be the pair recorded by the same prepare run.")
    before = load_document(recorded_baseline)
    expected = manifest.get("baseline_sha256")
    if "baseline_sha256" not in manifest:
        # Older preparations recorded the original file's digest but not its parsed snapshot.
        source = Path(manifest["source"])
        if digest(source.read_text(encoding="utf-8-sig")) != manifest["source_sha256"]:
            raise ValueError("Original source changed since legacy prepare; recover the original to verify the baseline.")
        expected = data_digest(load_document(source))
    if data_digest(before) != expected:
        raise ValueError("Baseline differs from the prepared snapshot. Recover it from the original before comparing.")
    return before, load_document(recorded_candidate), "verified"


def pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def changes(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"op": "replace", "path": path, "before": before, "after": after}]
    if isinstance(before, dict):
        result: list[dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            child = path + "/" + pointer_token(key)
            if key not in before:
                result.append({"op": "add", "path": child, "after": after[key]})
            elif key not in after:
                result.append({"op": "remove", "path": child, "before": before[key]})
            else:
                result.extend(changes(before[key], after[key], child))
        return result
    if isinstance(before, list):
        result = []
        for index in range(max(len(before), len(after))):
            child = path + "/" + str(index)
            if index >= len(before):
                result.append({"op": "add", "path": child, "after": after[index]})
            elif index >= len(after):
                result.append({"op": "remove", "path": child, "before": before[index]})
            else:
                result.extend(changes(before[index], after[index], child))
        return result
    return [] if before == after else [{"op": "replace", "path": path, "before": before, "after": after}]


def compare(before: dict[str, Any], after: dict[str, Any], *,
            allowed_sections: list[str] | None = None, allow_scope_change: bool = False) -> dict[str, Any]:
    delta = changes(before, after)
    old = {item["id"]: item for item in before["sections"]}
    new = {item["id"]: item for item in after["sections"]}
    section_changes = []
    for section_id in list(old) + [item for item in new if item not in old]:
        if section_id not in old:
            section_changes.append({"id": section_id, "change": "added"})
        elif section_id not in new:
            section_changes.append({"id": section_id, "change": "removed"})
        elif changes(old[section_id], new[section_id]):
            section_changes.append({"id": section_id, "change": "modified"})
    old_order, new_order = list(old), list(new)
    before_shared = [key for key in old_order if key in new]
    after_shared = [key for key in new_order if key in old]
    reordered = [current for previous, current in zip(before_shared, after_shared) if current != previous]
    contract_changes = [key for key in ("profile", "kind", "scope")
                        if before["document"].get(key) != after["document"].get(key)]
    errors = []
    structural = contract_changes or set(old) != set(new)
    if structural and not allow_scope_change:
        errors.append("Document contract or section membership changed; reconcile with the user's requested scope.")
    if allowed_sections is not None:
        unknown = set(allowed_sections) - (set(old) | set(new))
        if unknown:
            errors.append("Unknown allowed section IDs: " + ", ".join(sorted(unknown)))
        touched = {item["id"] for item in section_changes} | set(reordered)
        outside = sorted(touched - set(allowed_sections))
        if outside:
            errors.append("Changes outside the declared section set: " + ", ".join(outside))
    return {"status": "blocked" if errors else ("needs-review" if delta else "unchanged"),
            "semantic_review": "required" if delta else "not-run",
            "errors": errors, "contract_changes": contract_changes,
            "section_order_changed": old_order != new_order,
            "reordered_sections": reordered,
            "section_changes": section_changes, "changes": delta,
            "impact_review": ["규칙·용어·우선순위", "비용·보상·성장·계산 예시", "도식·표·UI 피드백", "예외·보존·재진입", "수용조건·연계 문서" ] if delta else []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--source", type=Path, required=True)
    request = prep.add_mutually_exclusive_group(required=True)
    request.add_argument("--request")
    request.add_argument("--request-file", type=Path)
    prep.add_argument("--output-dir", type=Path, required=True)
    diff = commands.add_parser("compare")
    diff.add_argument("--manifest", type=Path, help="Manifest from prepare; selects and verifies the revision pair")
    diff.add_argument("--baseline", type=Path)
    diff.add_argument("--updated", type=Path)
    diff.add_argument("--output-dir", type=Path, required=True)
    diff.add_argument("--allow-section", action="append")
    diff.add_argument("--allow-scope-change", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            request_text = args.request if args.request is not None else args.request_file.read_text(encoding="utf-8-sig")
            result = prepare(args.source, request_text, args.output_dir)
        else:
            before, after, integrity = load_comparison(args.manifest, args.baseline, args.updated)
            result = compare(before, after,
                             allowed_sections=args.allow_section, allow_scope_change=args.allow_scope_change)
            result["baseline_integrity"] = integrity
            report = write_new(args.output_dir / "revision-diff.json", result)
            result = {"status": result["status"], "report": report,
                      "changed_sections": result["section_changes"], "reordered_sections": result["reordered_sections"],
                      "baseline_integrity": integrity, "errors": result["errors"]}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 2 if result["status"] == "blocked" else 0
    except (OSError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
