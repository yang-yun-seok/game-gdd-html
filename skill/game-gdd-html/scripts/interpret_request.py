#!/usr/bin/env python3
"""Normalize natural-language game-planning requests into GDDQL and a scope filter."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
import unicodedata
from pathlib import Path
from typing import Any

from kind_contracts import (
    CATEGORY_LABELS,
    KIND_CONTRACTS,
    KIND_NAMES,
    lookup_kind_name,
)
from profile_contracts import (
    ALL_CANONICAL_SECTION_IDS,
    PROFILE_NAMES,
    PROFILE_RULES,
    build_section_plan,
)
from request_rules import (
    AUDIENCE_WEIGHT,
    COMBINATION_BONUS,
    COMBINATION_TERMS,
    EXPLICIT_WEIGHT,
    FEATURE_SIGNALS,
    MERGE_TERMS,
    MULTI_JOIN_TERMS,
    PROFILE_SIGNALS,
    SPLIT_TERMS,
    STRONG_WEIGHT,
    WEAK_WEIGHT,
)


GDDQL_VERSION = "1.0"
CLAUSES = (
    "DESIGN",
    "KIND",
    "FROM",
    "ABOUT",
    "FOR",
    "GOAL",
    "WITH",
    "WITHOUT",
    "ASSUME",
    "OUTPUT",
)
PROFILE_ALIASES = {
    "auto": "AUTO",
    "자동": "AUTO",
    "전체": "full",
    "통합": "full",
    "컨셉": "concept",
    "콘셉트": "concept",
    "시스템": "system",
    "ui": "ui-ux",
    "ux": "ui-ux",
    "ui/ux": "ui-ux",
    "화면": "ui-ux",
    "콘텐츠": "content",
    "컨텐츠": "content",
    "밸런스": "balance",
    "수치": "balance",
    "경제": "economy",
    "재화": "economy",
    "레벨": "level",
    "스테이지": "level",
    "내러티브": "narrative",
    "시나리오": "narrative",
    "라이브": "live-ops",
    "운영": "live-ops",
    "프로덕션": "production",
    "제작": "production",
    "개발 일정": "production",
    "사업": "business",
}


class InterpretError(ValueError):
    """Raised when GDDQL or request input cannot be interpreted."""


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = value.replace("·", " ").replace("•", " ")
    value = re.sub(r"[\t\r\n]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def contains_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    if re.fullmatch(r"[a-z0-9+./ -]+", normalized_phrase):
        pattern = re.escape(normalized_phrase).replace(r"\ ", r"\s+")
        return bool(
            re.search(
                rf"(?<![a-z0-9]){pattern}(?![a-z0-9])",
                text,
            )
        )
    return normalized_phrase in text


def phrase_spans(text: str, phrase: str) -> list[tuple[int, int]]:
    """Return normalized phrase spans with ASCII token boundaries."""
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return []
    if re.fullmatch(r"[a-z0-9+./ -]+", normalized_phrase):
        pattern = re.escape(normalized_phrase).replace(r"\ ", r"\s+")
        return [
            match.span()
            for match in re.finditer(
                rf"(?<![a-z0-9]){pattern}(?![a-z0-9])",
                text,
            )
        ]
    return [
        (match.start(), match.end())
        for match in re.finditer(re.escape(normalized_phrase), text)
    ]


def phrase_position(text: str, phrase: str) -> int | None:
    """Return the first normalized phrase position."""
    spans = phrase_spans(text, phrase)
    return spans[0][0] if spans else None


def is_excluded_mention(text: str, start: int, end: int) -> bool:
    if re.search(r"(?:^|[.,;]\s*|\s)제외\s*:\s*$", text[:start]):
        return True
    return re.match(
        r"^\s*(?:(?:은|는|을|를)\s*)?"
        r"(?:제외(?!하지)|빼고|말고|없이|"
        r"(?:(?:따로|별도(?:로)?)\s*)?(?:(?:작성|생성|포함)하지|만들지)\s*(?:마|말|않))",
        text[end:],
    ) is not None


def is_reference_mention(text: str, start: int, end: int) -> bool:
    tail = text[end:]
    prefix = text[:start]
    if re.match(
        r"^\s*(?:(?:은|는|을|를)\s*)?"
        r"(?:(?:후속(?:\s*문서)?|입력\s*문서)(?:로|인)?\s*)?"
        r"(?:참조|참고|인계)(?:용|만|한다|해|하고)?",
        tail,
    ):
        return True
    if re.match(
        r"^\s*(?:(?:은|는|을|를)\s*)?"
        r"(?:(?:바탕|기준)(?:으)?로|(?:참조|참고)(?:해|하여|해서|하고))",
        tail,
    ):
        return True
    return bool(
        re.search(
            r"(?:입력|참고|참조|후속)\s*문서(?:인|로)?\s*$",
            prefix,
        )
    )


def detect_kind_mentions(text: str) -> list[dict[str, Any]]:
    """Detect explicit document kinds and preserve their mention order."""
    mentions: list[dict[str, Any]] = []
    for registry_index, kind_name in enumerate(KIND_NAMES):
        contract = KIND_CONTRACTS[kind_name]
        best: tuple[int, int, str] | None = None
        for alias in (kind_name, *contract["aliases"]):
            position = phrase_position(text, alias)
            if position is None:
                continue
            candidate = (position, -len(normalize_text(alias)), alias)
            if best is None or candidate < best:
                best = candidate
        if best is not None:
            mentions.append(
                {
                    "kind": kind_name,
                    "alias": best[2],
                    "position": best[0],
                    "registry_index": registry_index,
                }
            )
    mentions.sort(
        key=lambda item: (
            item["position"],
            -len(normalize_text(item["alias"])),
            item["registry_index"],
        )
    )
    return mentions


def mask_non_target_documents(text: str) -> tuple[str, list[str], set[str]]:
    """Mask excluded document occurrences before both lexical scoring and routing."""
    phrases = {phrase for signals in PROFILE_SIGNALS.values() for phrase in signals["explicit"]}
    for kind, contract in KIND_CONTRACTS.items():
        phrases.update((kind, *contract["aliases"]))
    spans = sorted({
        span for phrase in phrases for span in phrase_spans(text, phrase)
    }, reverse=True)
    masked = list(text)
    non_targets = []
    exclusions = set()
    next_excluded_start = None
    for start, end in spans:
        # In "A와 B는 빼고" the same predicate applies to both document names.
        joined = (
            next_excluded_start is not None and end < next_excluded_start
            and re.fullmatch(r"\s*(?:와|과|및|하고)\s*", text[end:next_excluded_start])
        )
        if joined or is_excluded_mention(text, start, end):
            exclusions.add(text[start:end])
            next_excluded_start = start
        elif not is_reference_mention(text, start, end):
            continue
        masked[start:end] = " " * (end - start)
        non_targets.append(text[start:end])
    return "".join(masked), non_targets, exclusions


def detect_generic_profile_mentions(
    text: str,
    candidates: list[dict[str, Any]],
    kind_mentions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find explicit broad-profile artifacts not consumed by a kind phrase."""
    kind_spans = [
        (
            mention["position"],
            mention["position"] + len(normalize_text(mention["alias"])),
        )
        for mention in kind_mentions
    ]
    mentions: list[dict[str, Any]] = []
    for candidate in candidates:
        best_position: int | None = None
        best_phrase = ""
        for phrase in candidate["explicit"]:
            for start, end in phrase_spans(text, phrase):
                consumed = any(
                    kind_start <= start and end <= kind_end
                    for kind_start, kind_end in kind_spans
                )
                if consumed:
                    continue
                if best_position is None or start < best_position:
                    best_position = start
                    best_phrase = phrase
        if best_position is not None:
            mentions.append(
                {
                    "profile": candidate["profile"],
                    "position": best_position,
                    "phrase": best_phrase,
                }
            )
    mentions.sort(key=lambda item: (item["position"], item["profile"]))
    return mentions


def matched_phrases(text: str, phrases: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in phrases if contains_phrase(text, phrase)]


def extract_focus(text: str) -> list[str]:
    return [
        focus
        for focus, phrases in FEATURE_SIGNALS.items()
        if any(contains_phrase(text, phrase) for phrase in phrases)
    ]


def extract_scope_hints(raw: str) -> tuple[list[str], list[str]]:
    include_hints: list[str] = []
    exclude_hints: list[str] = []
    for match in re.finditer(
        r"(?:포함|include|with)\s*[:：]\s*([^.;\n]+)",
        raw,
        flags=re.IGNORECASE,
    ):
        include_hints.extend(split_csv(match.group(1)))
    for match in re.finditer(
        r"(?:제외|exclude|without)\s*[:：]\s*([^.;\n]+)",
        raw,
        flags=re.IGNORECASE,
    ):
        exclude_hints.extend(split_csv(match.group(1)))
    for marker in re.finditer(r"(?:빼고|제외하고|없이)", raw):
        prefix = raw[: marker.start()]
        local_clause = re.split(
            r"[,.;\n]|(?:포함하되|포함하고|포함하며|포함해서|"
            r"하되|하지만|다만|그리고|그 대신)",
            prefix,
        )[-1]
        value = re.sub(
            r"(?:은|는|을|를)\s*$",
            "",
            local_clause.strip(),
        ).strip()
        tokens = value.split()
        if len(tokens) > 4:
            value = " ".join(tokens[-4:])
        if value:
            exclude_hints.append(value)
    return unique(include_hints), unique(exclude_hints)


def extract_topic(raw: str, explicit_matches: list[str]) -> str:
    first_sentence = re.split(r"[.!?\n]", raw, maxsplit=1)[0].strip()
    topic = first_sentence
    for phrase in sorted(explicit_matches, key=len, reverse=True):
        topic = re.sub(re.escape(phrase), " ", topic, flags=re.IGNORECASE)
    topic = re.sub(
        r"(?:(?:입력|참고|참조)\s*문서(?:인|로)?\s*)?"
        r"(?:은|는|이|가|을|를)?\s*(?:바탕|기준)(?:으)?로",
        " ",
        topic,
    )
    topic = re.sub(
        r"(?:입력|참고|참조)\s*문서(?:인|로)?\s*"
        r"(?:은|는|이|가|을|를)?\s*(?:참조|참고)(?:해|하여|해서|하고)?",
        " ",
        topic,
    )
    topic = re.sub(
        r"(?:html로|html|작성해\s*줘|작성해주세요|작성|만들어\s*줘|만들어주세요|정리해\s*줘|"
        r"정리해주세요|기획해\s*줘|기획해주세요|문서로|문서)",
        " ",
        topic,
        flags=re.IGNORECASE,
    )
    topic = re.sub(
        r"(?:(?:은|는|을|를)\s*)?"
        r"(?:제외(?:하고|한|해|해서)?|빼고|말고|"
        r"(?:후속\s*)?(?:참조|참고|인계)(?:해서|하여|하고|해|용|만)?)",
        " ",
        topic,
    )
    topic = re.sub(r"\s+", " ", topic).strip(" ,:;-")
    topic = re.sub(
        r"^(?:(?:은|는|을|를|이|가|와|과|및|만|하고|각각)\s*)+$",
        "",
        topic,
    )
    topic = re.sub(r"\s+(?:은|는|을|를|이|가)\s*$", "", topic)
    topic = re.sub(r"^(?:와|과|및)\s+|\s+(?:와|과|및)$", "", topic)
    topic = re.sub(
        r"(?:\s+(?:와|과|및|은|는|을|를|이|가|만|하고|각각))+\s*$",
        "",
        topic,
    )
    topic = re.sub(r"\s+", " ", topic).strip(" ,:;-")
    return topic or "TBD"


def has_multi_join(text: str) -> bool:
    return any(term in text for term in MULTI_JOIN_TERMS) or bool(
        re.search(r"[가-힣a-z0-9]+(?:와|과)\s", text)
    )


def shared_document_profiles(text: str) -> list[str]:
    """Detect coordinated profile names that share one document head."""
    document_heads = list(
        re.finditer(
            r"(?:기획서|설계서|명세서|문서|스펙|gdd)",
            text,
            flags=re.IGNORECASE,
        )
    )
    if not document_heads or not has_multi_join(text):
        return []
    prefix = text[max(0, document_heads[-1].start() - 80) : document_heads[-1].start()]
    found: set[str] = set()

    def is_profile_mention(alias: str) -> bool:
        normalized_alias = normalize_text(alias)
        if re.fullmatch(r"[a-z0-9+./ -]+", normalized_alias):
            return contains_phrase(prefix, normalized_alias)
        for match in re.finditer(re.escape(normalized_alias), prefix):
            before = prefix[match.start() - 1 : match.start()]
            after = prefix[match.end() :]
            if before and re.fullmatch(r"[가-힣]", before):
                continue
            if not after or not re.match(r"[가-힣]", after):
                return True
            if after.startswith(
                ("와", "과", "및", "을", "를", "중심", "위주")
            ):
                return True
        return False

    for alias, profile in PROFILE_ALIASES.items():
        if profile in {"AUTO", "full"}:
            continue
        if is_profile_mention(alias):
            found.add(profile)
    return [profile for profile in PROFILE_NAMES if profile in found]


def score_profiles(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for profile in PROFILE_NAMES:
        signals = PROFILE_SIGNALS[profile]
        explicit = matched_phrases(text, signals["explicit"])
        strong = matched_phrases(text, signals["strong"])
        weak = matched_phrases(text, signals["weak"])
        audience = matched_phrases(text, signals["audience"])
        combination = [
            term
            for term in COMBINATION_TERMS.get(profile, ())
            if contains_phrase(text, term)
        ]
        combo_bonus = COMBINATION_BONUS if len(combination) >= 2 else 0
        score = (
            len(explicit) * EXPLICIT_WEIGHT
            + len(strong) * STRONG_WEIGHT
            + len(weak) * WEAK_WEIGHT
            + len(audience) * AUDIENCE_WEIGHT
            + combo_bonus
        )
        candidates.append(
            {
                "profile": profile,
                "score": score,
                "explicit": explicit,
                "strong": strong,
                "weak": weak,
                "audience": audience,
                "combination": combination,
            }
        )
    return sorted(candidates, key=lambda item: (-item["score"], item["profile"]))


def select_profiles(
    text: str,
    candidates: list[dict[str, Any]],
) -> tuple[list[str], str, bool, str]:
    explicit_profiles = [
        item["profile"] for item in candidates if item["explicit"]
    ]
    split_requested = any(contains_phrase(text, term) for term in SPLIT_TERMS)
    merge_requested = any(contains_phrase(text, term) for term in MERGE_TERMS)

    if explicit_profiles:
        selected = [
            profile
            for profile in PROFILE_NAMES
            if profile in explicit_profiles
        ]
        if selected == ["full"]:
            return ["full"], "high", False, "explicit full-document phrase"
        return (
            selected,
            "high",
            False,
            "explicit document-type phrase",
        )

    coordinated_profiles = shared_document_profiles(text)
    if len(coordinated_profiles) >= 2:
        return (
            coordinated_profiles,
            "high",
            False,
            "coordinated profile names share one document-type phrase",
        )

    scored = [
        item
        for item in candidates
        if item["profile"] != "full" and item["score"] > 0
    ]
    if not scored:
        return [], "low", True, "no profile signal"

    top = scored[0]
    second_score = scored[1]["score"] if len(scored) > 1 else 0
    margin = top["score"] - second_score
    independently_strong = [
        item
        for item in scored
        if item["score"] >= 10
        and (item["strong"] or len(item["combination"]) >= 2)
    ]
    if has_multi_join(text) and len(independently_strong) >= 2:
        max_gap = 15 if split_requested else 10
        near_top = [
            item["profile"]
            for item in independently_strong[:3]
            if top["score"] - item["score"] <= max_gap
        ]
        if len(near_top) >= 2:
            confidence = (
                "high"
                if all(
                    item["score"] >= 16
                    for item in independently_strong
                    if item["profile"] in near_top
                )
                else "medium"
            )
            return (
                near_top,
                confidence,
                confidence != "high" and not merge_requested,
                "independent profile bundles joined in one request",
            )

    if top["score"] >= 16 and margin >= 6:
        return [top["profile"]], "high", False, "strong keyword bundle"
    if top["score"] >= 10 and margin >= 3:
        return [top["profile"]], "medium", True, "probable profile with limited margin"
    return [], "low", True, "ambiguous profile scores"


def output_mode_for(text: str, selected: list[Any]) -> str:
    if any(contains_phrase(text, term) for term in MERGE_TERMS):
        return "merge"
    if len(selected) > 1 or any(
        contains_phrase(text, term) for term in SPLIT_TERMS
    ):
        return "split"
    return "split"


def normalize_scope_terms(items: list[str]) -> list[str]:
    """Map free-form scope hints to stable facets without discarding unknowns."""
    normalized_terms: list[str] = []
    for item in items:
        normalized = normalize_text(item)
        if not normalized:
            continue
        matched = extract_focus(normalized)
        if normalized in FEATURE_SIGNALS or normalized in ALL_CANONICAL_SECTION_IDS:
            matched.insert(0, normalized)
        normalized_terms.extend(matched or [normalized])
    return unique(normalized_terms)


def resolve_scope(
    selected: list[str],
    selected_kinds: list[str],
    generic_profiles: list[str],
    focus: list[str],
    include_hints: list[str],
    exclude_hints: list[str],
    document_order: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    requested_facets = normalize_scope_terms(focus + include_hints)
    requested_excludes = normalize_scope_terms(exclude_hints)
    document_plans: list[dict[str, Any]] = []

    specs = document_order or [
        *(("kind", kind_name) for kind_name in selected_kinds),
        *(("profile", profile) for profile in generic_profiles),
    ]
    if not specs and selected:
        specs = [("profile", profile) for profile in selected]

    for document_type, document_id in specs:
        if document_type == "kind":
            kind_name = document_id
            contract = KIND_CONTRACTS[kind_name]
            candidate_facets = unique(
                list(contract["default_facets"]) + requested_facets
            )
            effective_excludes = requested_excludes
            section_plan = build_section_plan(
                contract["profile"],
                candidate_facets,
                effective_excludes,
            )
            ignored_facets = set(section_plan["ignored_facets"])
            effective_facets = [
                facet for facet in candidate_facets if facet not in ignored_facets
            ]
            document_plans.append(
                {
                    "id": kind_name,
                    "kind": kind_name,
                    "label": contract["label"],
                    "category": contract["category"],
                    "category_label": CATEGORY_LABELS[contract["category"]],
                    "profile": contract["profile"],
                    "reference": contract["reference"],
                    "kind_default_facets": list(contract["default_facets"]),
                    "requested_facets": requested_facets,
                    "facets": effective_facets,
                    "exclude_facets": effective_excludes,
                    "required_outputs": list(contract["required_outputs"]),
                    "default_excludes": list(contract["default_excludes"]),
                    "handoffs": list(contract["handoffs"]),
                    "section_plan": section_plan,
                }
            )
        else:
            profile = document_id
            section_plan = build_section_plan(
                profile,
                requested_facets,
                requested_excludes,
            )
            ignored_facets = set(section_plan["ignored_facets"])
            effective_facets = [
                facet for facet in requested_facets if facet not in ignored_facets
            ]
            document_plans.append(
                {
                    "id": profile,
                    "kind": None,
                    "label": PROFILE_RULES[profile]["label"],
                    "category": None,
                    "category_label": None,
                    "profile": profile,
                    "reference": f"references/profiles/{profile}.md",
                    "kind_default_facets": [],
                    "requested_facets": requested_facets,
                    "facets": effective_facets,
                    "exclude_facets": requested_excludes,
                    "required_outputs": [],
                    "default_excludes": [],
                    "handoffs": [],
                    "section_plan": section_plan,
                }
            )

    plans = {
        plan["id"]: plan["section_plan"]
        for plan in document_plans
    }
    profile_counts = {
        profile: sum(
            1 for plan in document_plans if plan["profile"] == profile
        )
        for profile in selected
    }
    for plan in document_plans:
        if profile_counts.get(plan["profile"]) == 1:
            plans.setdefault(plan["profile"], plan["section_plan"])
    conflicts = [
        {
            "document": document["id"],
            "kind": document["kind"],
            "profile": document["profile"],
            "message": message,
        }
        for document in document_plans
        for message in document["section_plan"]["conflicts"]
    ]
    return {
        "mode": "filtered",
        "facets": requested_facets,
        "exclude_facets": requested_excludes,
        "document_plans": document_plans,
        "section_plans": plans,
        "include_hints": include_hints,
        "exclude_hints": exclude_hints,
        "conflicts": conflicts,
    }


def candidate_summary(
    candidates: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    return [
        item
        for item in candidates
        if item["score"] > 0
    ][:limit]


def question_hint(
    selected: list[str],
    candidates: list[dict[str, Any]],
    confidence: str,
) -> str | None:
    if confidence == "high":
        return None
    top_profiles = [
        item["profile"] for item in candidates if item["score"] > 0
    ][:3]
    if selected:
        alternatives = [item for item in top_profiles if item not in selected]
        alternative_text = (
            f" 대신 {', '.join(alternatives)}" if alternatives else ""
        )
        return (
            f"요청을 {', '.join(selected)} 문서로 해석했습니다."
            f"{alternative_text}가 아니라 이 영역이 맞나요?"
        )
    if top_profiles:
        return (
            "문서 영역을 확정해 주세요. 현재 후보는 "
            + ", ".join(top_profiles)
            + "입니다."
        )
    return "컨셉, 시스템, UI·UX, 콘텐츠, 밸런스 등 어떤 문서가 필요한가요?"


def classify_natural(raw: str) -> dict[str, Any]:
    text = normalize_text(raw)
    routing_text, non_target_phrases, excluded_phrases = mask_non_target_documents(text)
    # A topic keyword bundle must not infer a profile explicitly declined as output.
    candidates = [
        item for item in score_profiles(routing_text) if item["explicit"] or not any(
            normalize_text(phrase) in excluded_phrases
            for phrase in PROFILE_SIGNALS[item["profile"]]["explicit"]
        )
    ]
    kind_mentions = detect_kind_mentions(routing_text)
    selected_kinds = unique([item["kind"] for item in kind_mentions])
    generic_mentions = detect_generic_profile_mentions(
        routing_text,
        candidates,
        kind_mentions,
    )
    if selected_kinds:
        kind_profiles = unique(
            [
                KIND_CONTRACTS[kind_name]["profile"]
                for kind_name in selected_kinds
            ]
        )
        generic_profiles = unique(
            [
                item["profile"]
                for item in generic_mentions
                if item["profile"] not in kind_profiles
            ]
        )
        ordered_documents = sorted(
            [
                *(
                    (item["position"], "kind", item["kind"])
                    for item in kind_mentions
                ),
                *(
                    (item["position"], "profile", item["profile"])
                    for item in generic_mentions
                    if item["profile"] in generic_profiles
                ),
            ],
            key=lambda item: (item[0], item[1], item[2]),
        )
        document_order = [
            (document_type, document_id)
            for _, document_type, document_id in ordered_documents
        ]
        selected = unique(
            [
                (
                    KIND_CONTRACTS[document_id]["profile"]
                    if document_type == "kind"
                    else document_id
                )
                for document_type, document_id in document_order
            ]
        )
        confidence = "high"
        needs_clarification = False
        reason = (
            "explicit document-kind and broad-profile phrases"
            if generic_profiles
            else "explicit document-kind phrase"
        )
        explicit_matches = [
            *[item["alias"] for item in kind_mentions],
            *[
                item["phrase"]
                for item in generic_mentions
                if item["profile"] in generic_profiles
            ],
        ]
    else:
        selected, confidence, needs_clarification, reason = select_profiles(
            routing_text,
            candidates,
        )
        generic_profiles = selected
        document_order = [
            ("profile", profile)
            for profile in selected
        ]
        explicit_matches = [
            phrase
            for item in candidates
            for phrase in item["explicit"]
            if item["profile"] in selected
        ]
    include_hints, exclude_hints = extract_scope_hints(raw)
    exclude_hints = [
        hint for hint in exclude_hints if normalize_text(hint) not in non_target_phrases
    ]
    topic_matches = unique([*explicit_matches, *non_target_phrases])
    focus_text = text
    focus_phrases = unique(
        [
            *[item["alias"] for item in kind_mentions],
            *non_target_phrases,
        ]
    )
    for phrase in sorted(
        focus_phrases,
        key=lambda item: len(normalize_text(item)),
        reverse=True,
    ):
        focus_text = re.sub(
            re.escape(normalize_text(phrase)),
            " ",
            focus_text,
        )
    focus = extract_focus(focus_text)
    explicit_include_facets = normalize_scope_terms(include_hints)
    explicit_exclude_facets = set(normalize_scope_terms(exclude_hints))
    focus = [
        facet
        for facet in focus
        if facet not in explicit_exclude_facets
        or facet in explicit_include_facets
    ]
    scope = resolve_scope(
        selected,
        selected_kinds,
        generic_profiles,
        focus,
        include_hints,
        exclude_hints,
        document_order,
    )
    if scope["conflicts"]:
        needs_clarification = True
        reason += "; scope include/exclude conflict"
    mode = output_mode_for(text, document_order)
    topic = extract_topic(raw, topic_matches)
    query = {
        "operation": "DESIGN",
        "profiles": selected or ["AUTO"],
        "kinds": selected_kinds,
        "context": {
            "from": "",
            "about": topic,
            "for": "",
            "goal": raw.strip(),
        },
        "with": scope["facets"],
        "without": scope["exclude_facets"],
        "assumptions": {},
        "output": {"format": "HTML", "mode": mode},
    }
    unresolved = []
    if not selected:
        unresolved.append("profile")
    if scope["conflicts"]:
        unresolved.append("scope-conflict")
    hint = question_hint(selected, candidates, confidence)
    if scope["conflicts"]:
        conflict_text = "; ".join(
            f"{item['profile']}: {item['message']}"
            for item in scope["conflicts"]
        )
        hint = f"포함·제외 범위가 충돌합니다. {conflict_text}"
    result = {
        "gddql_version": GDDQL_VERSION,
        "input_mode": "natural",
        "raw": raw,
        "query": query,
        "filter": {
            "selected_profiles": selected,
            "selected_kinds": selected_kinds,
            "selected_generic_profiles": generic_profiles,
            "documents": [
                {
                    key: plan[key]
                    for key in (
                        "id",
                        "kind",
                        "label",
                        "category",
                        "category_label",
                        "profile",
                    )
                }
                for plan in scope["document_plans"]
            ],
            "confidence": confidence,
            "needs_clarification": needs_clarification,
            "reason": reason,
            "candidates": candidate_summary(candidates),
            "question_hint": hint,
        },
        "scope": scope,
        "unresolved": unresolved,
    }
    result["gddql"] = render_gddql(query)
    return result


def split_csv(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("(") != value.endswith(")"):
        raise InterpretError("unbalanced parentheses in list clause")
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]
    lexer = shlex.shlex(value, posix=True)
    lexer.whitespace = ","
    lexer.whitespace_split = True
    lexer.commenters = ""
    return [item.strip() for item in lexer if item.strip()]


def unique(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def parse_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        raise InterpretError("clause value must not be empty")
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as error:
            raise InterpretError(f"invalid quoted string: {error.msg}") from error
        if not isinstance(decoded, str):
            raise InterpretError("quoted clause value must be a string")
        return decoded
    return value


def canonical_profile(value: str) -> str:
    normalized = normalize_text(value)
    alias = PROFILE_ALIASES.get(normalized, normalized)
    if alias == "AUTO":
        return alias
    if alias not in PROFILE_RULES:
        raise InterpretError(
            f"unknown profile '{value}'. Expected AUTO or: "
            + ", ".join(PROFILE_NAMES)
        )
    return alias


def parse_design(value: str) -> list[str]:
    raw_profiles = split_csv(value)
    if not raw_profiles:
        raise InterpretError("DESIGN requires AUTO or at least one profile")
    profiles = unique([canonical_profile(item) for item in raw_profiles])
    if "AUTO" in profiles and len(profiles) > 1:
        raise InterpretError("AUTO cannot be combined with explicit profiles")
    return profiles


def canonical_kind(value: str) -> str:
    normalized = normalize_text(value)
    if normalized in {"auto", "자동"}:
        return "AUTO"
    try:
        return lookup_kind_name(value)
    except KeyError as error:
        raise InterpretError(
            f"unknown document kind '{value}'. Expected AUTO or one of: "
            + ", ".join(KIND_NAMES)
        ) from error


def parse_kinds(value: str) -> list[str]:
    raw_kinds = split_csv(value)
    if not raw_kinds:
        raise InterpretError("KIND requires AUTO or at least one document kind")
    canonical = [canonical_kind(item) for item in raw_kinds]
    kinds = unique(canonical)
    if len(kinds) != len(canonical):
        raise InterpretError("KIND contains duplicate document kinds")
    if "AUTO" in kinds and len(kinds) > 1:
        raise InterpretError("KIND AUTO cannot be combined with explicit kinds")
    return kinds


def parse_assumptions(value: str) -> dict[str, str]:
    assumptions: dict[str, str] = {}
    for item in split_csv(value):
        if "=" not in item:
            raise InterpretError("ASSUME items must use key=value")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise InterpretError("ASSUME key must not be empty")
        assumptions[key] = parse_scalar(raw_value)
    return assumptions


def parse_output(value: str) -> dict[str, str]:
    try:
        parts = shlex.split(value)
    except ValueError as error:
        raise InterpretError(f"invalid OUTPUT clause: {error}") from error
    if not parts:
        raise InterpretError("OUTPUT requires a format")
    output_format = parts[0].upper()
    if output_format != "HTML":
        raise InterpretError("OUTPUT format must be HTML")
    mode = parts[1].lower() if len(parts) > 1 else "split"
    if mode not in {"split", "merge"}:
        raise InterpretError("OUTPUT mode must be SPLIT or MERGE")
    if len(parts) > 2:
        raise InterpretError("OUTPUT accepts only format and mode")
    return {"format": output_format, "mode": mode}


def parse_clause_lines(raw: str) -> dict[str, list[str]]:
    clauses: dict[str, list[str]] = {}
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        line = line.rstrip(";").strip()
        match = re.match(
            rf"^({'|'.join(CLAUSES)})\b\s*(.*)$",
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            raise InterpretError(
                f"line {line_number}: expected one of {', '.join(CLAUSES)}"
            )
        clause = match.group(1).upper()
        value = match.group(2).strip()
        clauses.setdefault(clause, []).append(value)
    return clauses


def parse_gddql(raw: str) -> dict[str, Any]:
    clauses = parse_clause_lines(raw)
    if "DESIGN" not in clauses or len(clauses["DESIGN"]) != 1:
        raise InterpretError("GDDQL requires exactly one DESIGN clause")
    for scalar_clause in ("KIND", "FROM", "ABOUT", "FOR", "GOAL", "OUTPUT"):
        if len(clauses.get(scalar_clause, [])) > 1:
            raise InterpretError(f"{scalar_clause} may appear only once")

    profiles = parse_design(clauses["DESIGN"][0])
    kind_selector = (
        parse_kinds(clauses["KIND"][0])
        if clauses.get("KIND")
        else []
    )
    context = {
        "from": parse_scalar(clauses["FROM"][0]) if clauses.get("FROM") else "",
        "about": parse_scalar(clauses["ABOUT"][0]) if clauses.get("ABOUT") else "",
        "for": parse_scalar(clauses["FOR"][0]) if clauses.get("FOR") else "",
        "goal": parse_scalar(clauses["GOAL"][0]) if clauses.get("GOAL") else "",
    }
    include_values = [
        item
        for clause_value in clauses.get("WITH", [])
        for item in split_csv(clause_value)
    ]
    exclude_values = [
        item
        for clause_value in clauses.get("WITHOUT", [])
        for item in split_csv(clause_value)
    ]
    assumptions: dict[str, str] = {}
    for value in clauses.get("ASSUME", []):
        assumptions.update(parse_assumptions(value))
    output = (
        parse_output(clauses["OUTPUT"][0])
        if clauses.get("OUTPUT")
        else {"format": "HTML", "mode": "split"}
    )

    inference_text = (
        " ".join(value for value in context.values() if value)
        + " "
        + " ".join(include_values)
    ).strip()
    inferred = (
        classify_natural(inference_text)
        if profiles == ["AUTO"] or kind_selector == ["AUTO"]
        else None
    )
    if kind_selector and kind_selector != ["AUTO"]:
        selected_kinds = kind_selector
    elif inferred is not None:
        selected_kinds = inferred["filter"]["selected_kinds"]
    else:
        selected_kinds = []

    if profiles == ["AUTO"]:
        if kind_selector and kind_selector != ["AUTO"]:
            selected = unique(
                [
                    KIND_CONTRACTS[kind_name]["profile"]
                    for kind_name in selected_kinds
                ]
            )
        else:
            selected = inferred["filter"]["selected_profiles"]
    else:
        selected = profiles

    kind_profiles = unique(
        [
            KIND_CONTRACTS[kind_name]["profile"]
            for kind_name in selected_kinds
        ]
    )
    if selected_kinds and profiles != ["AUTO"]:
        if not set(kind_profiles).issubset(selected):
            raise InterpretError(
                "KIND and DESIGN are incompatible: kinds require "
                f"{', '.join(kind_profiles)}, but DESIGN selected "
                f"{', '.join(selected)}"
            )

    if (
        inferred is not None
        and profiles == ["AUTO"]
        and not (kind_selector and kind_selector != ["AUTO"])
    ):
        generic_profiles = inferred["filter"]["selected_generic_profiles"]
        document_order = [
            (
                "kind" if document["kind"] else "profile",
                document["kind"] or document["profile"],
            )
            for document in inferred["filter"]["documents"]
        ]
    else:
        generic_profiles = [
            profile for profile in selected if profile not in kind_profiles
        ]
        document_order = []
        for profile in selected:
            profile_kinds = [
                kind_name
                for kind_name in selected_kinds
                if KIND_CONTRACTS[kind_name]["profile"] == profile
            ]
            if profile_kinds:
                document_order.extend(
                    ("kind", kind_name) for kind_name in profile_kinds
                )
            elif profile in generic_profiles:
                document_order.append(("profile", profile))

    if kind_selector and kind_selector != ["AUTO"]:
        candidates = [
            {
                "profile": profile,
                "score": EXPLICIT_WEIGHT,
                "explicit": [
                    "GDDQL KIND"
                    if profile in kind_profiles
                    else "GDDQL DESIGN"
                ],
                "strong": [],
                "weak": [],
                "audience": [],
                "combination": [],
            }
            for profile in selected
        ]
        confidence = "high"
        needs_clarification = False
        reason = "explicit GDDQL KIND clause"
        question = None
    elif inferred is not None and (
        profiles == ["AUTO"] or kind_selector == ["AUTO"]
    ):
        candidates = inferred["filter"]["candidates"]
        confidence = inferred["filter"]["confidence"]
        needs_clarification = inferred["filter"]["needs_clarification"]
        auto_label = (
            "AUTO profile inference"
            if profiles == ["AUTO"] and kind_selector != ["AUTO"]
            else "AUTO kind inference"
        )
        reason = auto_label + ": " + inferred["filter"]["reason"]
        question = inferred["filter"]["question_hint"]
    else:
        candidates = [
            {
                "profile": profile,
                "score": EXPLICIT_WEIGHT,
                "explicit": ["GDDQL DESIGN"],
                "strong": [],
                "weak": [],
                "audience": [],
                "combination": [],
            }
            for profile in selected
        ]
        confidence = "high"
        needs_clarification = False
        reason = (
            "explicit GDDQL DESIGN and KIND clauses"
            if selected_kinds
            else "explicit GDDQL DESIGN clause"
        )
        question = None

    if len(document_order) > 1 and "OUTPUT" not in clauses:
        output["mode"] = "split"
    unresolved: list[str] = []
    if not selected:
        unresolved.append("profile")
    if kind_selector == ["AUTO"] and not selected_kinds:
        unresolved.append("kind")
    if not context["about"]:
        unresolved.append("about")
    if not context["goal"]:
        unresolved.append("goal")

    scope = resolve_scope(
        selected,
        selected_kinds,
        generic_profiles,
        normalize_scope_terms(include_values),
        include_values,
        exclude_values,
        document_order,
    )
    if scope["conflicts"]:
        needs_clarification = True
        reason += "; scope include/exclude conflict"
        unresolved.append("scope-conflict")
        conflict_text = "; ".join(
            f"{item['profile']}: {item['message']}"
            for item in scope["conflicts"]
        )
        question = f"포함·제외 범위가 충돌합니다. {conflict_text}"

    query = {
        "operation": "DESIGN",
        "profiles": selected or ["AUTO"],
        "kinds": (
            ["AUTO"]
            if kind_selector == ["AUTO"] and not selected_kinds
            else selected_kinds
        ),
        "context": context,
        "with": scope["facets"],
        "without": scope["exclude_facets"],
        "assumptions": assumptions,
        "output": output,
    }
    result = {
        "gddql_version": GDDQL_VERSION,
        "input_mode": "gddql",
        "raw": raw,
        "query": query,
        "filter": {
            "selected_profiles": selected,
            "selected_kinds": selected_kinds,
            "selected_generic_profiles": generic_profiles,
            "documents": [
                {
                    key: plan[key]
                    for key in (
                        "id",
                        "kind",
                        "label",
                        "category",
                        "category_label",
                        "profile",
                    )
                }
                for plan in scope["document_plans"]
            ],
            "confidence": confidence,
            "needs_clarification": needs_clarification,
            "reason": reason,
            "candidates": candidates,
            "question_hint": question,
        },
        "scope": scope,
        "unresolved": unresolved,
    }
    result["gddql"] = render_gddql(query)
    return result


def quote_gddql(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_gddql(query: dict[str, Any]) -> str:
    profiles = query.get("profiles") or ["AUTO"]
    profile_text = (
        profiles[0]
        if len(profiles) == 1
        else "(" + ", ".join(profiles) + ")"
    )
    lines = [f"DESIGN {profile_text}"]
    kinds = query.get("kinds") or []
    if kinds:
        kind_text = (
            kinds[0]
            if len(kinds) == 1
            else "(" + ", ".join(kinds) + ")"
        )
        lines.append(f"KIND {kind_text}")
    context = query.get("context", {})
    for clause, key in (
        ("FROM", "from"),
        ("ABOUT", "about"),
        ("FOR", "for"),
        ("GOAL", "goal"),
    ):
        if context.get(key):
            lines.append(f"{clause} {quote_gddql(str(context[key]))}")
    if query.get("with"):
        lines.append("WITH " + ", ".join(query["with"]))
    if query.get("without"):
        lines.append("WITHOUT " + ", ".join(query["without"]))
    assumptions = query.get("assumptions", {})
    if assumptions:
        rendered = ", ".join(
            f"{key}={quote_gddql(str(value))}"
            for key, value in assumptions.items()
        )
        lines.append("ASSUME " + rendered)
    output = query.get("output", {"format": "HTML", "mode": "split"})
    lines.append(
        f"OUTPUT {str(output.get('format', 'HTML')).upper()} "
        f"{str(output.get('mode', 'split')).upper()};"
    )
    return "\n".join(lines)


def interpret(raw: str) -> dict[str, Any]:
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip() and not line.lstrip().startswith("--")
    ]
    looks_like_gddql = False
    if lines:
        design_match = re.match(
            r"^DESIGN\b\s*(.*?);?$",
            lines[0],
            flags=re.IGNORECASE,
        )
        if design_match:
            design_value = design_match.group(1).strip()
            has_following_clause = any(
                re.match(
                    rf"^({'|'.join(CLAUSES)})\b",
                    line,
                    flags=re.IGNORECASE,
                )
                for line in lines[1:]
            )
            compact_design_value = design_value.strip("()")
            looks_like_gddql = (
                has_following_clause
                or "," in design_value
                or bool(re.fullmatch(r"[^\s]+", compact_design_value))
            )
            if not looks_like_gddql:
                try:
                    parse_design(design_value)
                except InterpretError:
                    pass
                else:
                    looks_like_gddql = True
    if looks_like_gddql:
        return parse_gddql(raw)
    return classify_natural(raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Interpret a natural-language game-planning request or GDDQL query "
            "and emit a deterministic first-pass scope filter."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Request text or GDDQL")
    source.add_argument("--file", type=Path, help="UTF-8 request/GDDQL file")
    parser.add_argument(
        "--format",
        choices=("json", "gddql"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.text is not None:
            raw = args.text
        elif args.file is not None:
            raw = args.file.read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            raw = sys.stdin.read()
        else:
            raise InterpretError("provide --text, --file, or stdin")
        if not raw.strip():
            raise InterpretError("request must not be empty")
        result = interpret(raw)
    except (OSError, InterpretError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2

    if args.format == "gddql":
        print(result["gddql"])
    else:
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=None if args.compact else 2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
