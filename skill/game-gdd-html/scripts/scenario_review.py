"""Check a reviewer's scenario traces against the editable GDD source."""

from __future__ import annotations

import re
from typing import Any


def _block_text(document: dict, path: str) -> str:
    if not re.fullmatch(r"/sections/(0|[1-9][0-9]*)/blocks/(0|[1-9][0-9]*)/.+", path):
        return ""
    value: Any = document
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            value = value.get(token)
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            index = int(token)
            if index >= len(value):
                return ""
            value = value[index]
        else:
            return ""
    return value if isinstance(value, str) else ""


def check_scenarios(document: dict, review: Any) -> list[str]:
    cases = review.get("scenarios") if isinstance(review, dict) else None
    if not isinstance(cases, list) or not cases:
        return ["scenario review needs a non-empty scenarios array"]
    errors = []
    for index, case in enumerate(cases):
        label = f"scenarios[{index}]"
        if not isinstance(case, dict) or not _text(case.get("input")):
            errors.append(f"{label}: describe the concrete input")
            continue
        results = {}
        paths = set()
        for role in ("rule", "diagram", "qa"):
            trace = case.get(role)
            location = f"{label}.{role}"
            if not isinstance(trace, dict):
                errors.append(f"{location}: missing trace or scope reason")
                continue
            if role != "rule" and set(trace) == {"out_of_scope"} and _text(trace["out_of_scope"]):
                continue
            path, quote, outcome = (trace.get(key) for key in ("path", "quote", "outcome"))
            if not all(_text(item) for item in (path, quote, outcome)):
                errors.append(f"{location}: missing evidence path, literal quote or outcome")
                continue
            if quote not in _block_text(document, path):
                errors.append(f"{location}: quote missing at {path}")
            if path in paths:
                errors.append(f"{location}: cite this representation's own evidence")
            paths.add(path)
            results[role] = outcome.strip()
        if len(results) < 2:
            errors.append(f"{label}: trace the rule and at least one other representation")
        elif len(set(results.values())) > 1:
            errors.append(f"{label}: different outcomes for the same input: {results}")
    return errors


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
