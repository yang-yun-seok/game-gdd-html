#!/usr/bin/env python3
"""Validate rendered HTML game design documents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from document_source import load_document
from kind_contracts import KIND_CONTRACTS, KIND_NAMES
from profile_contracts import (
    ALL_CANONICAL_SECTION_IDS,
    PROFILE_NAMES,
    PROFILE_RULES,
    build_section_plan,
)
from render_gdd import KIND_LABELS_EN, PROFILE_LABELS_KO
from scenario_review import check_scenarios

AUTHORITY_BOUNDARY_KO = (
    "게임 규칙과 사용자 결과를 정의한다. 구현 방식은 개발 협의에서 확정한다."
)
AUTHORITY_BOUNDARY_EN = (
    "Design defines game rules and user-facing outcomes. "
    "Implementation is finalized with engineering."
)


def class_tokens(attrs: dict[str, str]) -> set[str]:
    return set(attrs.get("class", "").split())


class GDDParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.anchor_targets: list[str] = []
        self.section_ids: list[str] = []
        self.canvas_ids: list[str] = []
        self.mermaid_count = 0
        self.decision_count = 0
        self.source_link_count = 0
        self.source_item_count = 0
        self.h1_count = 0
        self.title_text = ""
        self.lang = ""
        self.document_profiles: list[str] = []
        self.document_kinds: list[str] = []
        self.document_scope_modes: list[str] = []
        self.document_scope_sections: list[str] = []
        self.document_scope_facets: list[str] = []
        self.document_marker_modes: list[str] = []
        self.document_marker_texts: list[str] = []
        self.document_marker_in_hero_top: list[bool] = []
        self.authority_boundary_texts: list[str] = []
        self.authority_boundary_in_hero_top: list[bool] = []
        self.hero_subtitle_texts: list[str] = []
        self.doc_meta_fields: list[str] = []
        self.pillar_section_count = 0
        self.pillar_card_count = 0
        self.brief_card_count = 0
        self.has_charset = False
        self.has_viewport = False
        self.has_toc_nav = False
        self.has_sidebar = False
        self.has_chart_script = False
        self.has_mermaid_script = False
        self.chart_config_text = ""
        self.render_error_count = 0
        self._in_title = False
        self._capture_chart_config = False
        self._in_sources = 0
        self._in_document_marker = 0
        self._in_authority_boundary = 0
        self._in_hero_subtitle = 0
        self._hero_top_depth = 0

    def handle_starttag(
        self, tag: str, attrs_list: list[tuple[str, str | None]]
    ) -> None:
        attrs = {key: value or "" for key, value in attrs_list}
        classes = class_tokens(attrs)
        if self._hero_top_depth:
            self._hero_top_depth += 1
        elif "hero-top" in classes:
            self._hero_top_depth = 1
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "html":
            self.lang = attrs.get("lang", "")
        elif tag == "meta":
            if attrs.get("charset"):
                self.has_charset = True
            meta_name = attrs.get("name", "").lower()
            if meta_name == "viewport":
                self.has_viewport = True
            elif meta_name == "gdd-profile":
                self.document_profiles.append(attrs.get("content", "").strip())
            elif meta_name == "gdd-kind":
                self.document_kinds.append(attrs.get("content", "").strip())
            elif meta_name == "gdd-scope-mode":
                self.document_scope_modes.append(
                    attrs.get("content", "").strip()
                )
            elif meta_name == "gdd-sections":
                self.document_scope_sections.append(
                    attrs.get("content", "").strip()
                )
            elif meta_name == "gdd-facets":
                self.document_scope_facets.append(
                    attrs.get("content", "").strip()
                )
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a":
            href = attrs.get("href", "")
            if href.startswith("#") and len(href) > 1:
                self.anchor_targets.append(href[1:])
            if self._in_sources and href.startswith(("http://", "https://")):
                self.source_link_count += 1
        elif (
            tag == "li"
            and self._in_sources
            and attrs.get("data-source-entry") == "true"
        ):
            self.source_item_count += 1
        elif tag == "section" and "gdd-section" in classes:
            if attrs.get("id"):
                self.section_ids.append(attrs["id"])
        elif tag == "canvas":
            if attrs.get("id"):
                self.canvas_ids.append(attrs["id"])
        elif tag == "pre" and "mermaid" in classes:
            self.mermaid_count += 1
        elif tag == "article" and "decision-card" in classes:
            self.decision_count += 1
        elif tag == "article" and "pillar-card" in classes:
            self.pillar_card_count += 1
        elif tag == "section" and "pillar-section" in classes:
            self.pillar_section_count += 1
        elif tag == "nav" and "toc-nav" in classes:
            self.has_toc_nav = True
        elif tag == "aside" and "sidebar" in classes:
            self.has_sidebar = True
        elif "render-error" in classes:
            self.render_error_count += 1
        elif tag == "script":
            source = attrs.get("src", "").lower()
            if "chart.js" in source or "chart.umd" in source:
                self.has_chart_script = True
            if "mermaid" in source:
                self.has_mermaid_script = True
            if attrs.get("id") == "gdd-chart-configs":
                self._capture_chart_config = True
        if attrs.get("id") == "sources":
            self._in_sources += 1
        if "brief-card" in classes:
            self.brief_card_count += 1
        if attrs.get("data-gdd-doc-meta-field"):
            self.doc_meta_fields.append(
                attrs["data-gdd-doc-meta-field"].strip()
            )
        if "document-type-marker" in classes:
            self.document_marker_modes.append(
                attrs.get("data-gdd-document-marker", "").strip()
            )
            self.document_marker_texts.append("")
            self.document_marker_in_hero_top.append(self._hero_top_depth > 0)
            self._in_document_marker += 1
        if "design-authority-boundary" in classes:
            self.authority_boundary_texts.append("")
            self.authority_boundary_in_hero_top.append(
                self._hero_top_depth > 0
            )
            self._in_authority_boundary += 1
        if "hero-subtitle" in classes:
            self.hero_subtitle_texts.append("")
            self._in_hero_subtitle += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._capture_chart_config:
            self._capture_chart_config = False
        elif tag == "section" and self._in_sources:
            self._in_sources -= 1
        if tag == "strong" and self._in_document_marker:
            self._in_document_marker -= 1
        if tag == "p" and self._in_authority_boundary:
            self._in_authority_boundary -= 1
        if tag == "p" and self._in_hero_subtitle:
            self._in_hero_subtitle -= 1
        if self._hero_top_depth:
            self._hero_top_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_text += data
        if self._capture_chart_config:
            self.chart_config_text += data
        if self._in_document_marker and self.document_marker_texts:
            self.document_marker_texts[-1] += data
        if self._in_authority_boundary and self.authority_boundary_texts:
            self.authority_boundary_texts[-1] += data
        if self._in_hero_subtitle and self.hero_subtitle_texts:
            self.hero_subtitle_texts[-1] += data


class Results:
    def __init__(self, profile: str = "unknown", kind: str = "") -> None:
        self.profile = profile
        self.kind = kind
        self.passes: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def check(self, condition: bool, message: str, severity: str = "error") -> None:
        if condition:
            self.passes.append(message)
        elif severity == "warning":
            self.warnings.append(message)
        else:
            self.errors.append(message)

    def as_dict(self, path: Path) -> dict[str, Any]:
        return {
            "file": str(path.resolve()),
            "profile": self.profile,
            "kind": self.kind or None,
            "valid": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "passes": self.passes,
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "passes": len(self.passes),
            },
        }


def validate(
    path: Path,
    profile: str | None = None,
    require_scope: bool = False,
    kind: str | None = None,
    scenario_review: Path | None = None,
) -> Results:
    requested_kind = (kind or "").strip()
    results = Results(profile or "auto", requested_kind)
    if scenario_review is not None:
        try:
            review = json.loads(scenario_review.read_text(encoding="utf-8-sig"))
            issues = check_scenarios(load_document(path), review)
            results.errors.extend(issues)
            if not issues:
                results.passes.append("Scenario evidence quotes and recorded outcomes agree")
        except (ValueError, OSError) as error:
            results.errors.append(f"Could not verify scenario review: {error}")
    if profile is not None and profile not in PROFILE_RULES:
        results.errors.append(
            "Unknown requested profile. Expected one of: " + ", ".join(PROFILE_NAMES)
        )
        return results
    if requested_kind and requested_kind not in KIND_CONTRACTS:
        results.errors.append(
            "Unknown requested kind. Expected one of: " + ", ".join(KIND_NAMES)
        )
        return results
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        results.errors.append("File is not valid UTF-8")
        return results

    parser = GDDParser()
    try:
        parser.feed(raw)
        parser.close()
    except Exception as error:
        results.errors.append(f"HTML parser failed: {error}")
        return results

    embedded_profiles = [item for item in parser.document_profiles if item]
    distinct_embedded_profiles = sorted(set(embedded_profiles))
    if len(parser.document_profiles) > 1:
        results.errors.append("Document contains more than one gdd-profile meta tag")
    if len(distinct_embedded_profiles) > 1:
        results.errors.append(
            "Document contains conflicting profile metadata: "
            + ", ".join(distinct_embedded_profiles)
        )
    embedded_profile = (
        distinct_embedded_profiles[0] if len(distinct_embedded_profiles) == 1 else ""
    )
    if embedded_profile and embedded_profile not in PROFILE_RULES:
        results.errors.append(f"Unknown embedded document profile: {embedded_profile}")

    embedded_kinds = [item for item in parser.document_kinds if item]
    distinct_embedded_kinds = sorted(set(embedded_kinds))
    if len(parser.document_kinds) > 1:
        results.errors.append("Document contains more than one gdd-kind meta tag")
    if len(distinct_embedded_kinds) > 1:
        results.errors.append(
            "Document contains conflicting kind metadata: "
            + ", ".join(distinct_embedded_kinds)
        )
    embedded_kind = (
        distinct_embedded_kinds[0] if len(distinct_embedded_kinds) == 1 else ""
    )
    if embedded_kind and embedded_kind not in KIND_CONTRACTS:
        results.errors.append(f"Unknown embedded document kind: {embedded_kind}")

    if requested_kind:
        effective_kind = requested_kind
        if embedded_kind:
            results.check(
                embedded_kind == requested_kind,
                "Embedded document kind matches requested kind"
                if embedded_kind == requested_kind
                else "Kind mismatch: "
                f"HTML declares {embedded_kind}, validator requested {requested_kind}",
            )
        else:
            results.errors.append(
                "Expected embedded gdd-kind metadata for the requested kind"
            )
    elif embedded_kind:
        effective_kind = embedded_kind
        if embedded_kind in KIND_CONTRACTS:
            results.passes.append("Document kind was read from embedded metadata")
    else:
        effective_kind = ""
    results.kind = effective_kind
    effective_kind_rule = KIND_CONTRACTS.get(effective_kind)

    if profile:
        effective_profile = profile
        if embedded_profile:
            results.check(
                embedded_profile == profile,
                "Embedded document profile matches requested profile"
                if embedded_profile == profile
                else "Profile mismatch: "
                f"HTML declares {embedded_profile}, validator requested {profile}",
            )
        else:
            results.warnings.append(
                "No embedded profile metadata; using the explicit CLI profile as a legacy fallback"
            )
    elif embedded_profile in PROFILE_RULES:
        effective_profile = embedded_profile
        results.passes.append("Document profile was read from embedded metadata")
    elif effective_kind_rule:
        effective_profile = str(effective_kind_rule["profile"])
        if embedded_kind:
            results.errors.append(
                "Embedded gdd-kind metadata requires embedded gdd-profile metadata"
            )
        else:
            results.warnings.append(
                "No usable profile metadata; using the explicit kind's mapped profile"
            )
    else:
        effective_profile = "full"
        results.warnings.append(
            "No usable embedded profile metadata; using legacy full-profile validation"
        )
    results.profile = effective_profile
    profile_rule = PROFILE_RULES[effective_profile]
    if effective_kind_rule:
        expected_kind_profile = str(effective_kind_rule["profile"])
        results.check(
            effective_profile == expected_kind_profile,
            f"Document kind {effective_kind} maps to profile {expected_kind_profile}"
            if effective_profile == expected_kind_profile
            else f"Kind/profile mismatch: {effective_kind} requires "
            f"{expected_kind_profile}, document uses {effective_profile}",
        )

    for meta_name, values in (
        ("gdd-scope-mode", parser.document_scope_modes),
        ("gdd-sections", parser.document_scope_sections),
        ("gdd-facets", parser.document_scope_facets),
    ):
        if len(values) > 1:
            results.errors.append(
                f"Document contains more than one {meta_name} meta tag"
            )

    embedded_scope_mode = (
        parser.document_scope_modes[0].lower()
        if len(parser.document_scope_modes) == 1
        else "legacy"
    )
    if embedded_scope_mode not in {"legacy", "filtered", "full"}:
        results.errors.append(
            "Unknown embedded scope mode: " + embedded_scope_mode
        )
        embedded_scope_mode = "legacy"
    if require_scope and embedded_scope_mode == "legacy":
        results.errors.append(
            "A filtered or full scope manifest is required; legacy scope is not allowed"
        )

    def parse_meta_list(values: list[str]) -> list[str]:
        if len(values) != 1 or not values[0]:
            return []
        return [item.strip() for item in values[0].split(",") if item.strip()]

    declared_scope_sections = parse_meta_list(
        parser.document_scope_sections
    )
    declared_scope_facets = parse_meta_list(parser.document_scope_facets)
    duplicate_scope_sections = sorted(
        section_id
        for section_id, count in Counter(declared_scope_sections).items()
        if count > 1
    )
    duplicate_scope_facets = sorted(
        facet
        for facet, count in Counter(declared_scope_facets).items()
        if count > 1
    )
    if duplicate_scope_sections:
        results.errors.append(
            "Duplicate gdd-sections values: "
            + ", ".join(duplicate_scope_sections)
        )
    if duplicate_scope_facets:
        results.errors.append(
            "Duplicate gdd-facets values: "
            + ", ".join(duplicate_scope_facets)
        )
    invalid_scope_facets = sorted(
        facet
        for facet in declared_scope_facets
        if not re.fullmatch(r"[a-z][a-z0-9-]*", facet)
    )
    if invalid_scope_facets:
        results.errors.append(
            "gdd-facets values must use lowercase ids: "
            + ", ".join(invalid_scope_facets)
        )
    if embedded_scope_mode in {"filtered", "full"} and effective_kind_rule:
        missing_kind_facets = [
            facet
            for facet in effective_kind_rule["default_facets"]
            if facet not in declared_scope_facets
        ]
        results.check(
            not missing_kind_facets,
            f"Scope includes every default facet for kind {effective_kind}"
            if not missing_kind_facets
            else f"Scope is missing default facets for kind {effective_kind}: "
            + ", ".join(missing_kind_facets),
        )

    results.check(path.suffix.lower() == ".html", "File extension is .html")
    results.check(
        bool(re.search(r"<!doctype\s+html", raw, flags=re.IGNORECASE)),
        "HTML5 doctype is present",
    )
    results.check(parser.has_charset, "Character encoding is declared")
    results.check(parser.has_viewport, "Viewport meta tag is present")
    results.check(bool(parser.lang.strip()), "Document language is declared")
    results.check(bool(parser.title_text.strip()), "Document title is present")
    results.check(parser.h1_count == 1, "Document has exactly one h1")
    results.check(parser.has_sidebar and parser.has_toc_nav, "Sidebar TOC is present")
    results.check(
        parser.brief_card_count == 0,
        "No standalone project brief card is present"
        if parser.brief_card_count == 0
        else "Standalone project brief cards are not allowed",
    )

    is_english = parser.lang.lower().startswith("en")
    expected_marker_mode = "kind" if effective_kind_rule else "profile"
    expected_marker_label = ""
    if effective_kind_rule:
        expected_marker_label = (
            KIND_LABELS_EN.get(
                effective_kind,
                str(effective_kind_rule["label"]),
            )
            if is_english
            else str(effective_kind_rule["label"])
        )
    elif embedded_profile in PROFILE_RULES:
        expected_marker_label = (
            str(PROFILE_RULES[embedded_profile]["label"])
            if is_english
            else PROFILE_LABELS_KO.get(
                embedded_profile,
                str(PROFILE_RULES[embedded_profile]["label"]),
            )
        )
    marker_structure_ok = (
        len(parser.document_marker_texts) == 1
        and len(parser.document_marker_modes) == 1
        and parser.document_marker_in_hero_top == [True]
    )
    results.check(
        marker_structure_ok,
        "Visible document marker is present exactly once in the hero top"
        if marker_structure_ok
        else "A single visible document marker is required in the hero top",
    )
    if marker_structure_ok:
        marker_text = re.sub(
            r"\s+", " ", parser.document_marker_texts[0]
        ).strip()
        results.check(
            parser.document_marker_modes[0] == expected_marker_mode,
            "Visible document marker mode matches kind/profile metadata"
            if parser.document_marker_modes[0] == expected_marker_mode
            else "Visible document marker mode does not match kind/profile metadata",
        )
        if expected_marker_label:
            marker_text_ok = marker_text == expected_marker_label
        else:
            marker_text_ok = bool(marker_text) and not re.search(
                r"^(?:기획서\s*(?:종류|영역)|Document\s+kind|Design\s+area)\s*·",
                marker_text,
                flags=re.IGNORECASE,
            )
        results.check(
            marker_text_ok,
            "Visible document marker text matches the document contract"
            if marker_text_ok
            else "Visible document marker text does not match the document contract",
        )

    subtitle_structure_ok = len(parser.hero_subtitle_texts) == 1
    results.check(
        subtitle_structure_ok,
        "A single reader-facing cover subtitle is present"
        if subtitle_structure_ok
        else "A single reader-facing cover subtitle is required",
    )
    if subtitle_structure_ok:
        subtitle_text = re.sub(
            r"\s+", " ", parser.hero_subtitle_texts[0]
        ).strip()
        has_kind_prefix = bool(
            re.search(
                r"(?:문서\s*종류|Document\s+kind)\s*:",
                subtitle_text,
                flags=re.IGNORECASE,
            )
        )
        has_route_notation = bool(
            effective_kind
            and re.search(
                rf"\(\s*{re.escape(effective_kind)}\s*/\s*"
                rf"{re.escape(effective_profile)}\s*\)",
                subtitle_text,
                flags=re.IGNORECASE,
            )
        )
        results.check(
            not has_kind_prefix and not has_route_notation,
            "Cover subtitle contains no internal routing notation"
            if not has_kind_prefix and not has_route_notation
            else "Cover subtitle must not expose document-kind prefixes or "
            "internal kind/profile routing notation",
        )

    boundary_structure_ok = (
        len(parser.authority_boundary_texts) == 1
        and parser.authority_boundary_in_hero_top == [True]
    )
    results.check(
        boundary_structure_ok,
        "Design authority boundary is visible exactly once in the hero top"
        if boundary_structure_ok
        else "A single visible design authority boundary is required in the hero top",
    )
    if boundary_structure_ok:
        boundary_text = re.sub(
            r"\s+", " ", parser.authority_boundary_texts[0]
        ).strip()
        expected_boundary = (
            AUTHORITY_BOUNDARY_EN if is_english else AUTHORITY_BOUNDARY_KO
        )
        results.check(
            boundary_text == expected_boundary,
            "Design authority boundary text matches the fixed policy"
            if boundary_text == expected_boundary
            else "Design authority boundary text does not match the fixed policy",
        )

    expected_doc_meta_fields = {
        "status",
        "version",
        "updated",
        "author",
        "confidentiality",
    }
    results.check(
        len(parser.doc_meta_fields) == len(expected_doc_meta_fields)
        and set(parser.doc_meta_fields) == expected_doc_meta_fields,
        "Visible document metadata contains only delivery fields"
        if len(parser.doc_meta_fields) == len(expected_doc_meta_fields)
        and set(parser.doc_meta_fields) == expected_doc_meta_fields
        else "Visible document metadata must contain status, version, updated, "
        "author, and confidentiality only",
    )
    results.check(
        parser.pillar_section_count in {0, 1}
        and (
            parser.pillar_section_count == 0
            or parser.pillar_card_count >= 1
        ),
        "Design principles are omitted when no principle cards exist"
        if parser.pillar_section_count in {0, 1}
        and (
            parser.pillar_section_count == 0
            or parser.pillar_card_count >= 1
        )
        else "Design principles must be omitted when empty and rendered once "
        "when populated",
    )
    results.check(
        "Principles over features" not in raw,
        "No presentation-oriented principles slogan is exposed",
    )

    duplicate_ids = sorted(
        identifier for identifier, count in Counter(parser.ids).items() if count > 1
    )
    results.check(
        not duplicate_ids,
        "All HTML ids are unique"
        if not duplicate_ids
        else f"Duplicate HTML ids: {', '.join(duplicate_ids)}",
    )

    missing_targets = sorted(
        {target for target in parser.anchor_targets if target not in set(parser.ids)}
    )
    results.check(
        not missing_targets,
        "All internal links resolve"
        if not missing_targets
        else f"Broken internal links: {', '.join(missing_targets)}",
    )
    results.check(
        not re.search(r"\{\{[A-Z0-9_]+\}\}", raw),
        "No template placeholders remain",
    )
    results.check(
        parser.render_error_count == 0,
        "No render-error blocks are present in saved HTML",
    )

    allowed_ids = set(profile_rule["allowed_ids"])
    core_ids = set(profile_rule["core_ids"])
    if embedded_scope_mode == "filtered":
        if not embedded_profile:
            results.errors.append(
                "Filtered scope requires embedded gdd-profile metadata"
            )
        if not declared_scope_sections:
            results.errors.append(
                "Filtered scope requires a non-empty gdd-sections meta tag"
            )
        unknown_declared_sections = sorted(
            set(declared_scope_sections) - allowed_ids
        )
        if unknown_declared_sections:
            results.errors.append(
                f"Filtered scope declares sections outside {effective_profile}: "
                + ", ".join(unknown_declared_sections)
            )
        expected_plan = build_section_plan(
            effective_profile,
            declared_scope_facets,
        )
        if expected_plan["unknown_facets"]:
            results.errors.append(
                "Filtered scope contains unknown facets: "
                + ", ".join(expected_plan["unknown_facets"])
            )
        expected_filtered_ids = set(expected_plan["selected_sections"])
        missing_declared_core = sorted(core_ids - set(declared_scope_sections))
        if missing_declared_core:
            results.errors.append(
                "Filtered scope omits core sections: "
                + ", ".join(missing_declared_core)
            )
        missing_facet_sections = sorted(
            expected_filtered_ids - set(declared_scope_sections)
        )
        unsupported_declared_sections = sorted(
            (set(declared_scope_sections) & allowed_ids)
            - expected_filtered_ids
        )
        if missing_facet_sections:
            results.errors.append(
                "Filtered scope omits facet-triggered or dependency sections: "
                + ", ".join(missing_facet_sections)
            )
        if unsupported_declared_sections:
            results.errors.append(
                "Filtered scope declares sections without facet support: "
                + ", ".join(unsupported_declared_sections)
            )
        required_ids = expected_filtered_ids
    elif embedded_scope_mode == "full":
        required_ids = allowed_ids
        if declared_scope_sections and set(declared_scope_sections) != allowed_ids:
            results.errors.append(
                "Full scope gdd-sections must equal every allowed profile section"
            )
    else:
        required_ids = set(profile_rule["required_ids"])

    present_section_ids = set(parser.section_ids)
    missing_profile_ids = sorted(required_ids - set(parser.section_ids))
    results.check(
        not missing_profile_ids,
        f"All selected {effective_profile} scope sections are present"
        if not missing_profile_ids
        else f"Missing selected {effective_profile} sections: "
        + ", ".join(missing_profile_ids),
    )
    unselected_profile_ids = sorted(
        (present_section_ids & allowed_ids) - required_ids
        if embedded_scope_mode == "filtered"
        else set()
    )
    results.check(
        not unselected_profile_ids,
        "No unselected canonical profile sections are present"
        if not unselected_profile_ids
        else "Canonical profile sections were rendered outside the filtered scope: "
        + ", ".join(unselected_profile_ids),
    )
    foreign_profile_ids = sorted(
        present_section_ids & (ALL_CANONICAL_SECTION_IDS - allowed_ids)
    )
    results.check(
        not foreign_profile_ids,
        f"No canonical sections from other profiles are mixed into {effective_profile}"
        if not foreign_profile_ids
        else f"Out-of-scope canonical sections for {effective_profile}: "
        + ", ".join(foreign_profile_ids),
    )
    unscoped_custom_ids = sorted(
        section_id
        for section_id in (present_section_ids - allowed_ids)
        if section_id not in ALL_CANONICAL_SECTION_IDS
        and not section_id.startswith("appendix-")
    )
    results.check(
        not unscoped_custom_ids,
        "Non-profile sections use the appendix- prefix"
        if not unscoped_custom_ids
        else "Non-profile section ids must use the appendix- prefix: "
        + ", ".join(unscoped_custom_ids),
    )

    mermaid_min = int(profile_rule["mermaid_min"])
    mermaid_recommended = int(profile_rule["mermaid_recommended"])
    if mermaid_min:
        results.check(
            parser.mermaid_count >= mermaid_min,
            f"{effective_profile} profile has at least {mermaid_min} Mermaid diagram(s)",
        )
    if mermaid_recommended > mermaid_min:
        results.check(
            parser.mermaid_count >= mermaid_recommended,
            f"{effective_profile} profile has the recommended "
            f"{mermaid_recommended} Mermaid diagram(s)",
            severity="warning",
        )
    if parser.mermaid_count:
        results.check(parser.has_mermaid_script, "Mermaid library is included")

    chart_specs: list[dict[str, Any]] = []
    if parser.chart_config_text.strip():
        try:
            decoded = json.loads(parser.chart_config_text)
            if isinstance(decoded, list):
                chart_specs = decoded
            else:
                results.errors.append("Chart configuration must be a JSON array")
        except json.JSONDecodeError as error:
            results.errors.append(
                f"Chart configuration JSON is invalid: line {error.lineno}, "
                f"column {error.colno}: {error.msg}"
            )
    configured_id_list = [
        str(item.get("id"))
        for item in chart_specs
        if isinstance(item, dict) and item.get("id")
    ]
    configured_ids = set(configured_id_list)
    duplicate_chart_configs = sorted(
        chart_id
        for chart_id, count in Counter(configured_id_list).items()
        if count > 1
    )
    results.check(
        not duplicate_chart_configs,
        "Chart configuration ids are unique"
        if not duplicate_chart_configs
        else "Duplicate chart configuration ids: "
        + ", ".join(duplicate_chart_configs),
    )
    canvas_ids = set(parser.canvas_ids)
    results.check(
        configured_ids == canvas_ids,
        "Every chart canvas has exactly one configuration"
        if configured_ids == canvas_ids
        else "Chart canvas/config mismatch: "
        f"canvas-only={sorted(canvas_ids - configured_ids)}, "
        f"config-only={sorted(configured_ids - canvas_ids)}",
    )
    if parser.canvas_ids:
        results.check(parser.has_chart_script, "Chart.js library is included")
        results.check(
            "data-fallback" in raw,
            "Chart data fallback is present",
        )
    chart_policy = str(profile_rule["chart_policy"])
    if chart_policy == "required":
        results.check(
            bool(parser.canvas_ids),
            f"{effective_profile} profile includes at least one numeric chart",
        )
    elif chart_policy == "recommended" and not parser.canvas_ids:
        results.warnings.append(
            f"No Chart.js chart is present; {effective_profile} normally benefits "
            "from a grounded numeric model"
        )

    results.check(
        "@media print" in raw,
        "Print stylesheet is present",
    )
    results.check(
        bool(re.search(r"@media\s*\([^)]*max-width", raw)),
        "Responsive breakpoint is present",
    )
    has_decision_section = "decision-log" in parser.ids
    results.check(
        has_decision_section == (parser.decision_count >= 1),
        "Decision log is omitted when empty and populated when present",
    )
    has_sources_section = "sources" in parser.ids
    results.check(
        has_sources_section == (parser.source_item_count >= 1),
        "Sources are omitted when empty and populated when present",
    )

    visible_text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.S | re.I)
    visible_text = re.sub(r"<style\b[^>]*>.*?</style>", " ", visible_text, flags=re.S | re.I)
    visible_text = re.sub(r"<[^>]+>", " ", visible_text)
    visible_text = re.sub(r"\s+", " ", visible_text).strip()
    results.check(
        len(visible_text) >= 800,
        "Document contains substantial visible content",
        severity="warning",
    )
    results.check(
        path.stat().st_size >= 30_000,
        "Document includes the complete HTML design system",
        severity="warning",
    )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a rendered game design document HTML file."
    )
    parser.add_argument("html", type=Path, help="Rendered HTML file")
    parser.add_argument("--scenario-review", type=Path,
                        help="Verify cited source text and outcomes in the author's scenario review JSON")
    parser.add_argument(
        "--profile",
        choices=PROFILE_NAMES,
        help=(
            "Expected section profile. Omit to read the embedded gdd-profile "
            "metadata; legacy documents without metadata fall back to full."
        ),
    )
    parser.add_argument(
        "--kind",
        choices=KIND_NAMES,
        help=(
            "Expected fine-grained document kind. Omit to read the embedded "
            "gdd-kind metadata."
        ),
    )
    parser.add_argument(
        "--require-scope",
        action="store_true",
        help="Reject legacy HTML without a filtered/full scope manifest",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of the human report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.html.exists():
        print(f"[ERROR] File not found: {args.html}", file=sys.stderr)
        return 2
    if not args.html.is_file():
        print(f"[ERROR] Not a file: {args.html}", file=sys.stderr)
        return 2

    results = validate(
        args.html,
        args.profile,
        require_scope=args.require_scope,
        kind=args.kind,
        scenario_review=args.scenario_review,
    )
    payload = results.as_dict(args.html)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "Game GDD HTML validation · "
            f"profile={results.profile} · kind={results.kind or 'none'}"
        )
        print(f"File: {args.html.resolve()}")
        for message in results.errors:
            print(f"[ERROR] {message}")
        for message in results.warnings:
            print(f"[WARN]  {message}")
        for message in results.passes:
            print(f"[PASS]  {message}")
        print(
            f"Summary: {len(results.errors)} error(s), "
            f"{len(results.warnings)} warning(s), "
            f"{len(results.passes)} pass(es)"
        )
    return 1 if results.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
