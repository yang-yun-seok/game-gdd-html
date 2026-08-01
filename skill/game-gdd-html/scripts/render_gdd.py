#!/usr/bin/env python3
"""Render a structured game design document JSON file as a single HTML file."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from kind_contracts import KIND_CONTRACTS, KIND_NAMES
from profile_contracts import (
    ALL_CANONICAL_SECTION_IDS,
    PROFILE_NAMES,
    PROFILE_RULES,
    build_section_plan,
)


ALLOWED_SECTION_ID = re.compile(r"^[a-z][a-z0-9-]*$")
PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")
ALLOWED_CHART_TYPES = {"line", "bar", "scatter", "radar", "doughnut", "pie"}
PALETTE = [
    "#e36245",
    "#1f5a4d",
    "#d2a33a",
    "#5574a8",
    "#8a5c91",
    "#2d8a8a",
]

PROFILE_LABELS_KO = {
    "full": "통합 게임 디자인 문서·GDD",
    "concept": "게임 콘셉트 기획서",
    "system": "시스템 기획서",
    "ui-ux": "UI·UX 기획서",
    "content": "콘텐츠 기획서",
    "balance": "밸런스 기획서",
    "economy": "게임 경제 기획서",
    "level": "레벨 디자인 기획서",
    "narrative": "세계관·스토리 기획서",
    "live-ops": "라이브 운영 기획서",
    "production": "개발 일정 기획서",
    "business": "게임 사업 기획서",
}

KIND_LABELS_EN = {
    "game-proposal": "Game Proposal",
    "game-concept": "Game Concept Document",
    "master-gdd": "Game Design Document",
    "development-plan": "Development Plan",
    "character-system": "Character System Specification",
    "item-system": "Item System Specification",
    "quest-system": "Quest System Specification",
    "achievement-system": "Achievement System Specification",
    "crafting-enhancement-system": "Crafting & Enhancement System Specification",
    "matchmaking-system": "Matchmaking System Specification",
    "combat-system": "Combat System Specification",
    "skill-design": "Skill Design Specification",
    "character-combat": "Character Combat Specification",
    "monster-boss": "Monster & Boss Specification",
    "combat-balance": "Combat Balance Specification",
    "level-design": "Level Design Specification",
    "dungeon-design": "Dungeon Design Specification",
    "stage-design": "Stage Design Specification",
    "content-design": "Content Design Specification",
    "tutorial-design": "Tutorial Design Specification",
    "game-economy": "Game Economy Specification",
    "reward-design": "Reward Design Specification",
    "progression-balance": "Progression Balance Specification",
    "random-probability-system": "Random Reward System Specification",
    "store-product": "Store & Product Specification",
    "ui-spec": "UI Specification",
    "ux-flow": "UX Flow",
    "wireframe": "Wireframe",
    "control-scheme": "Control Scheme Specification",
    "world-bible": "World Bible",
    "scenario-design": "Scenario Design Specification",
    "character-bible": "Character Bible",
    "dialogue-script": "Dialogue Script",
    "data-table-spec": "Data Table Definition",
    "logic-rule-spec": "Logic & Rule Definition",
    "logging-spec": "Logging Specification",
    "exception-spec": "Exception Handling Specification",
    "event-plan": "Event Plan",
    "live-ops-plan": "Live Operations Plan",
    "product-promotion": "Product Promotion Plan",
    "update-spec": "Update Specification",
}


class RenderError(ValueError):
    """Raised when the input document does not match the renderer contract."""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def paragraph_text(value: Any) -> str:
    return esc(value).replace("\n", "<br>\n")


def display_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def slugify(value: str) -> str:
    value = re.sub(r"[^\w가-힣-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-_")
    return value or "game"


class BlockRenderer:
    def __init__(self, labels: dict[str, str]) -> None:
        self.labels = labels
        self.mermaid_count = 0
        self.chart_counter = 0
        self.chart_configs: list[dict[str, Any]] = []

    def render_many(self, blocks: Any, path: str) -> str:
        if not isinstance(blocks, list):
            raise RenderError(f"{path} must be an array")
        return "\n".join(
            self.render_block(block, f"{path}[{index}]")
            for index, block in enumerate(blocks)
        )

    def render_block(self, block: Any, path: str) -> str:
        if not isinstance(block, dict):
            raise RenderError(f"{path} must be an object")
        block_type = str(block.get("type", "")).strip().lower()
        handlers = {
            "lead": self.render_lead,
            "paragraph": self.render_paragraph,
            "heading": self.render_heading,
            "bullets": self.render_bullets,
            "cards": self.render_cards,
            "metrics": self.render_metrics,
            "table": self.render_table,
            "callout": self.render_callout,
            "formula": self.render_formula,
            "mermaid": self.render_mermaid,
            "chart": self.render_chart,
            "timeline": self.render_timeline,
            "user_story": self.render_user_story,
            "html": self.render_raw_html,
        }
        if block_type not in handlers:
            supported = ", ".join(sorted(handlers))
            raise RenderError(
                f"{path}.type is '{block_type or '<empty>'}'. Supported: {supported}"
            )
        return handlers[block_type](block, path)

    def require_text(self, block: dict[str, Any], field: str, path: str) -> str:
        value = block.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RenderError(f"{path}.{field} must be a non-empty string")
        return value.strip()

    def render_lead(self, block: dict[str, Any], path: str) -> str:
        return f'<p class="section-lead">{paragraph_text(self.require_text(block, "text", path))}</p>'

    def render_paragraph(self, block: dict[str, Any], path: str) -> str:
        return f"<p>{paragraph_text(self.require_text(block, 'text', path))}</p>"

    def render_heading(self, block: dict[str, Any], path: str) -> str:
        level = block.get("level", 3)
        if level not in (3, 4):
            raise RenderError(f"{path}.level must be 3 or 4")
        return f"<h{level}>{esc(self.require_text(block, 'text', path))}</h{level}>"

    def render_bullets(self, block: dict[str, Any], path: str) -> str:
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise RenderError(f"{path}.items must be a non-empty array")
        tag = "ol" if block.get("ordered") else "ul"
        item_html = "".join(f"<li>{paragraph_text(item)}</li>" for item in items)
        return f'<{tag} class="content-list">{item_html}</{tag}>'

    def render_cards(self, block: dict[str, Any], path: str) -> str:
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise RenderError(f"{path}.items must be a non-empty array")
        rendered: list[str] = []
        allowed_tones = {"default", "accent", "success", "warning", "risk"}
        for index, item in enumerate(items):
            item_path = f"{path}.items[{index}]"
            if not isinstance(item, dict):
                raise RenderError(f"{item_path} must be an object")
            title = self.require_text(item, "title", item_path)
            text = self.require_text(item, "text", item_path)
            tone = str(item.get("tone", "default")).lower()
            if tone not in allowed_tones:
                tone = "default"
            meta = (
                f'<span class="card-meta">{esc(item["meta"])}</span>'
                if item.get("meta")
                else ""
            )
            rendered.append(
                f'<article class="info-card tone-{tone}">{meta}'
                f"<h4>{esc(title)}</h4><p>{paragraph_text(text)}</p></article>"
            )
        return f'<div class="card-grid">{"".join(rendered)}</div>'

    def render_metrics(self, block: dict[str, Any], path: str) -> str:
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise RenderError(f"{path}.items must be a non-empty array")
        rendered: list[str] = []
        for index, item in enumerate(items):
            item_path = f"{path}.items[{index}]"
            if not isinstance(item, dict):
                raise RenderError(f"{item_path} must be an object")
            label = self.require_text(item, "label", item_path)
            value = self.require_text(item, "value", item_path)
            detail = paragraph_text(item.get("detail", ""))
            trend = (
                f'<span class="metric-trend">{esc(item["trend"])}</span>'
                if item.get("trend")
                else ""
            )
            rendered.append(
                '<article class="metric-card">'
                f'<div class="metric-label">{esc(label)}</div>'
                f'<div class="metric-value">{esc(value)}</div>'
                f'<div class="metric-detail">{detail}</div>{trend}</article>'
            )
        return f'<div class="metric-grid">{"".join(rendered)}</div>'

    def table_parts(
        self, block: dict[str, Any], path: str
    ) -> tuple[list[tuple[str, str]], list[list[Any]]]:
        columns = block.get("columns")
        rows = block.get("rows")
        if not isinstance(columns, list) or not columns:
            raise RenderError(f"{path}.columns must be a non-empty array")
        if not isinstance(rows, list):
            raise RenderError(f"{path}.rows must be an array")

        normalized_columns: list[tuple[str, str]] = []
        for index, column in enumerate(columns):
            if isinstance(column, str):
                normalized_columns.append((str(index), column))
            elif isinstance(column, dict) and column.get("key") and column.get("label"):
                normalized_columns.append((str(column["key"]), str(column["label"])))
            else:
                raise RenderError(
                    f"{path}.columns[{index}] must be a string or key/label object"
                )

        normalized_rows: list[list[Any]] = []
        for index, row in enumerate(rows):
            if isinstance(row, list):
                values = list(row)
                if len(values) < len(normalized_columns):
                    values.extend([""] * (len(normalized_columns) - len(values)))
                normalized_rows.append(values[: len(normalized_columns)])
            elif isinstance(row, dict):
                normalized_rows.append(
                    [row.get(key, "") for key, _ in normalized_columns]
                )
            else:
                raise RenderError(f"{path}.rows[{index}] must be an array or object")
        return normalized_columns, normalized_rows

    def render_table(self, block: dict[str, Any], path: str) -> str:
        columns, rows = self.table_parts(block, path)
        caption = (
            f"<caption>{esc(block['caption'])}</caption>"
            if block.get("caption")
            else ""
        )
        head = "".join(f"<th scope=\"col\">{esc(label)}</th>" for _, label in columns)
        body = "".join(
            "<tr>"
            + "".join(f"<td>{paragraph_text(display_value(cell))}</td>" for cell in row)
            + "</tr>"
            for row in rows
        )
        if not body:
            body = (
                f'<tr><td colspan="{len(columns)}" class="empty-cell">'
                f"{esc(self.labels['no_data'])}</td></tr>"
            )
        return (
            '<div class="table-shell"><table>'
            f"{caption}<thead><tr>{head}</tr></thead><tbody>{body}</tbody>"
            "</table></div>"
        )

    def render_callout(self, block: dict[str, Any], path: str) -> str:
        title = self.require_text(block, "title", path)
        text = self.require_text(block, "text", path)
        tone = str(block.get("tone", "insight")).lower()
        if tone not in {"insight", "success", "warning", "risk", "tbd"}:
            tone = "insight"
        return (
            f'<aside class="callout callout-{tone}"><strong>{esc(title)}</strong>'
            f"<p>{paragraph_text(text)}</p></aside>"
        )

    def render_formula(self, block: dict[str, Any], path: str) -> str:
        label = self.require_text(block, "label", path)
        expression = self.require_text(block, "expression", path)
        note = (
            f"<p>{paragraph_text(block['note'])}</p>" if block.get("note") else ""
        )
        return (
            '<figure class="formula-block">'
            f"<figcaption>{esc(label)}</figcaption><code>{esc(expression)}</code>{note}"
            "</figure>"
        )

    def render_mermaid(self, block: dict[str, Any], path: str) -> str:
        title = self.require_text(block, "title", path)
        code = self.require_text(block, "code", path)
        self.mermaid_count += 1
        caption = (
            f"<figcaption>{paragraph_text(block['caption'])}</figcaption>"
            if block.get("caption")
            else ""
        )
        return (
            '<figure class="visual-block diagram-block">'
            f'<div class="visual-heading"><span>{esc(self.labels["diagram"])}</span>'
            f"<h4>{esc(title)}</h4></div>"
            f'<pre class="mermaid">{esc(code)}</pre>{caption}</figure>'
        )

    def render_chart(self, block: dict[str, Any], path: str) -> str:
        title = self.require_text(block, "title", path)
        chart_type = str(block.get("chart_type", "")).lower()
        if chart_type not in ALLOWED_CHART_TYPES:
            raise RenderError(
                f"{path}.chart_type must be one of {', '.join(sorted(ALLOWED_CHART_TYPES))}"
            )
        labels = block.get("labels", [])
        datasets = block.get("datasets")
        if not isinstance(labels, list):
            raise RenderError(f"{path}.labels must be an array")
        if not isinstance(datasets, list) or not datasets:
            raise RenderError(f"{path}.datasets must be a non-empty array")

        self.chart_counter += 1
        chart_id = f"gdd-chart-{self.chart_counter}"
        configured_datasets: list[dict[str, Any]] = []
        for index, dataset in enumerate(datasets):
            dataset_path = f"{path}.datasets[{index}]"
            if not isinstance(dataset, dict):
                raise RenderError(f"{dataset_path} must be an object")
            if not dataset.get("label"):
                raise RenderError(f"{dataset_path}.label must be a non-empty string")
            if not isinstance(dataset.get("data"), list):
                raise RenderError(f"{dataset_path}.data must be an array")
            item = copy.deepcopy(dataset)
            color = PALETTE[index % len(PALETTE)]
            if chart_type in {"doughnut", "pie"}:
                item.setdefault(
                    "backgroundColor",
                    [PALETTE[i % len(PALETTE)] for i in range(len(item["data"]))],
                )
                item.setdefault("borderColor", "#fffdf8")
                item.setdefault("borderWidth", 3)
            else:
                item.setdefault("borderColor", color)
                item.setdefault("backgroundColor", color + "33")
                item.setdefault("pointBackgroundColor", color)
                item.setdefault("borderWidth", 2)
                item.setdefault("tension", 0.28)
            configured_datasets.append(item)

        default_options: dict[str, Any] = {
            "animation": False,
            "responsive": True,
            "maintainAspectRatio": False,
            "interaction": {"mode": "index", "intersect": False},
            "plugins": {
                "legend": {
                    "position": "bottom",
                    "labels": {"usePointStyle": True, "boxWidth": 8, "padding": 18},
                }
            },
        }
        if chart_type not in {"doughnut", "pie", "radar"}:
            default_options["scales"] = {
                "x": {"grid": {"display": False}},
                "y": {"grid": {"color": "rgba(24, 33, 31, 0.08)"}},
            }
        option_overrides = block.get("options", {})
        if not isinstance(option_overrides, dict):
            raise RenderError(f"{path}.options must be an object")
        options = deep_merge(default_options, option_overrides)
        config = {
            "type": chart_type,
            "data": {"labels": labels, "datasets": configured_datasets},
            "options": options,
        }
        self.chart_configs.append({"id": chart_id, "config": config})

        fallback_columns = [self.labels["category"]] + [
            str(dataset.get("label", f"Series {index + 1}"))
            for index, dataset in enumerate(datasets)
        ]
        longest = max(
            [len(labels)]
            + [len(dataset.get("data", [])) for dataset in datasets]
            + [0]
        )
        fallback_rows: list[list[Any]] = []
        for index in range(longest):
            row: list[Any] = [labels[index] if index < len(labels) else index + 1]
            for dataset in datasets:
                values = dataset.get("data", [])
                row.append(values[index] if index < len(values) else "")
            fallback_rows.append(row)
        fallback = self.render_table(
            {"columns": fallback_columns, "rows": fallback_rows},
            f"{path}.fallback",
        )
        caption = (
            f"<figcaption>{paragraph_text(block['caption'])}</figcaption>"
            if block.get("caption")
            else ""
        )
        return (
            '<figure class="visual-block chart-block">'
            f'<div class="visual-heading"><span>{esc(self.labels["data_label"])}</span>'
            f"<h4>{esc(title)}</h4></div>"
            f'<div class="chart-canvas"><canvas id="{chart_id}" role="img" '
            f'aria-label="{esc(title)}"></canvas></div>{caption}'
            f'<details class="data-fallback"><summary>{esc(self.labels["show_data"])}</summary>'
            f"{fallback}</details></figure>"
        )

    def render_timeline(self, block: dict[str, Any], path: str) -> str:
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise RenderError(f"{path}.items must be a non-empty array")
        rendered: list[str] = []
        for index, item in enumerate(items):
            item_path = f"{path}.items[{index}]"
            if not isinstance(item, dict):
                raise RenderError(f"{item_path} must be an object")
            phase = self.require_text(item, "phase", item_path)
            title = self.require_text(item, "title", item_path)
            text = self.require_text(item, "text", item_path)
            status = str(item.get("status", "planned")).lower()
            if status not in {"done", "active", "planned"}:
                status = "planned"
            tags = "".join(
                f"<span>{esc(tag)}</span>" for tag in item.get("tags", [])
            )
            rendered.append(
                f'<article class="timeline-item status-{status}">'
                f'<div class="timeline-marker" aria-hidden="true"></div>'
                f'<div class="timeline-body"><div class="timeline-phase">{esc(phase)}</div>'
                f"<h4>{esc(title)}</h4><p>{paragraph_text(text)}</p>"
                f'<div class="timeline-tags">{tags}</div></div></article>'
            )
        return f'<div class="timeline">{"".join(rendered)}</div>'

    def render_user_story(self, block: dict[str, Any], path: str) -> str:
        actor = self.require_text(block, "actor", path)
        want = self.require_text(block, "want", path)
        reason = self.require_text(block, "reason", path)
        acceptance = block.get("acceptance", [])
        if not isinstance(acceptance, list):
            raise RenderError(f"{path}.acceptance must be an array")
        criteria = "".join(f"<li>{paragraph_text(item)}</li>" for item in acceptance)
        criteria_html = (
            f'<div class="story-criteria"><strong>{esc(self.labels["acceptance"])}</strong>'
            f"<ul>{criteria}</ul></div>"
            if criteria
            else ""
        )
        return (
            '<article class="user-story">'
            f'<div class="story-label">{esc(self.labels["user_story"])}</div>'
            f'<div class="story-statement">'
            f'<p><span>{esc(self.labels["story_actor"])}</span><strong>{esc(actor)}</strong></p>'
            f'<p><span>{esc(self.labels["story_goal"])}</span>{paragraph_text(want)}</p>'
            f'<p><span>{esc(self.labels["story_reason"])}</span>{paragraph_text(reason)}</p>'
            f"</div>{criteria_html}</article>"
        )

    def render_raw_html(self, block: dict[str, Any], path: str) -> str:
        content = block.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RenderError(f"{path}.content must be a non-empty string")
        return content


def labels_for(language: str) -> dict[str, str]:
    if language.lower().startswith("en"):
        return {
            "menu": "Open contents",
            "contents": "Contents",
            "pillars": "Design principles",
            "decisions": "Decision log",
            "sources": "Sources & evidence",
            "print": "Print / Save PDF",
            "version": "Version",
            "status": "Status",
            "authority_boundary": (
                "Design defines game rules and user-facing outcomes. "
                "Implementation is finalized with engineering."
            ),
            "updated": "Updated",
            "author": "Owner",
            "confidentiality": "Access",
            "category": "Category",
            "show_data": "View chart data",
            "no_data": "No data",
            "acceptance": "Acceptance criteria",
            "user_story": "USER STORY",
            "story_actor": "Actor",
            "story_goal": "Goal",
            "story_reason": "Reason",
            "diagram": "Diagram",
            "data_label": "Data",
            "decision_owner": "Owner",
            "decision_due": "Due",
            "source_accessed": "Accessed",
            "close": "Close contents",
            "back_to_top": "Back to top",
        }
    return {
        "menu": "목차 열기",
        "contents": "문서 목차",
        "pillars": "설계 원칙",
        "decisions": "결정 로그",
        "sources": "출처와 근거",
        "print": "인쇄 / PDF 저장",
        "version": "버전",
        "status": "상태",
        "authority_boundary": (
            "게임 규칙과 사용자 결과를 정의한다. 구현 방식은 개발 협의에서 확정한다."
        ),
        "updated": "업데이트",
        "author": "담당",
        "confidentiality": "공개 범위",
        "category": "구분",
        "show_data": "차트 데이터 보기",
        "no_data": "데이터 없음",
        "acceptance": "수용 조건",
        "user_story": "사용자 스토리",
        "story_actor": "사용자",
        "story_goal": "목표",
        "story_reason": "이유",
        "diagram": "흐름도",
        "data_label": "데이터",
        "decision_owner": "담당",
        "decision_due": "결정 시점",
        "source_accessed": "확인",
        "close": "목차 닫기",
        "back_to_top": "맨 위로",
    }


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RenderError(f"{path} must be an object")
    return value


def require_nonempty(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RenderError(f"{path} must be a non-empty string")
    return value.strip()


def require_string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list):
        raise RenderError(f"{path} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise RenderError(f"{path}[{index}] must be a non-empty string")
        normalized = item.strip()
        if normalized in result:
            raise RenderError(f"{path} contains a duplicate value: {normalized}")
        result.append(normalized)
    return result


def find_authoring_placeholders(
    value: Any,
    path: str = "$",
) -> list[str]:
    matches: list[str] = []
    if isinstance(value, str):
        if "[작성 필요]" in value:
            matches.append(path)
    elif isinstance(value, dict):
        for key, item in value.items():
            matches.extend(find_authoring_placeholders(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            matches.extend(
                find_authoring_placeholders(item, f"{path}[{index}]")
            )
    return matches


def default_output_path(
    data: dict[str, Any],
    directory: Path | None = None,
) -> Path:
    document = require_object(data.get("document"), "document")
    title = require_nonempty(document.get("title"), "document.title")
    date = str(document.get("date") or dt.date.today().isoformat()).replace("-", "")
    profile = str(document.get("profile", "")).strip()
    kind = str(document.get("kind", "")).strip()
    document_type = kind or profile
    type_suffix = f"_{document_type}" if document_type else ""
    return (directory or Path.cwd()) / (
        f"{slugify(title)}{type_suffix}_GDD_{date}.html"
    )


def compact_template(template: str) -> str:
    """Remove source indentation without touching generated document content."""
    return "\n".join(
        line.lstrip()
        for line in template.splitlines()
        if line.strip()
    ) + "\n"


def render_document(
    data: dict[str, Any],
    template: str,
    *,
    compact: bool = True,
) -> str:
    placeholders = find_authoring_placeholders(data)
    if placeholders:
        raise RenderError(
            "unresolved authoring placeholders: " + ", ".join(placeholders)
        )
    document = require_object(data.get("document"), "document")
    title = require_nonempty(document.get("title"), "document.title")
    subtitle = require_nonempty(document.get("subtitle"), "document.subtitle")
    status = require_nonempty(document.get("status"), "document.status")
    version = require_nonempty(document.get("version"), "document.version")
    date = require_nonempty(document.get("date"), "document.date")
    profile = str(document.get("profile", "")).strip()
    if profile and profile not in PROFILE_RULES:
        raise RenderError(
            "document.profile must be one of: " + ", ".join(PROFILE_NAMES)
        )
    kind = str(document.get("kind", "")).strip()
    if kind and kind not in KIND_CONTRACTS:
        raise RenderError(
            "document.kind must be one of: " + ", ".join(KIND_NAMES)
        )
    kind_rule = KIND_CONTRACTS.get(kind)
    if kind_rule:
        expected_profile = str(kind_rule["profile"])
        if not profile:
            raise RenderError("document.profile is required when document.kind is used")
        if profile != expected_profile:
            raise RenderError(
                f"document.kind {kind} requires profile {expected_profile}, "
                f"not {profile}"
            )
    profile_rule = PROFILE_RULES.get(profile, {})
    language = str(document.get("language", "ko")).strip() or "ko"
    labels = labels_for(language)
    renderer = BlockRenderer(labels)
    eyebrow = str(document.get("eyebrow", "")).strip()
    eyebrow_html = (
        f'<span class="eyebrow">{esc(eyebrow)}</span>' if eyebrow else ""
    )
    document_marker_mode = "kind" if kind_rule else "profile"
    is_english = language.lower().startswith("en")
    if kind_rule:
        profile_label = (
            KIND_LABELS_EN.get(kind, str(kind_rule["label"]))
            if is_english
            else str(kind_rule["label"])
        )
    elif is_english:
        profile_label = str(
            profile_rule.get("label", "Game Design Document")
        )
    else:
        profile_label = PROFILE_LABELS_KO.get(
            profile,
            str(profile_rule.get("label", "게임 기획서")),
        )
    document_marker_text = profile_label

    forbidden_subtitle_prefix = re.search(
        r"(?:문서\s*종류|Document\s+kind)\s*:",
        subtitle,
        flags=re.IGNORECASE,
    )
    route_notation = (
        re.search(
            rf"\(\s*{re.escape(kind)}\s*/\s*{re.escape(profile)}\s*\)",
            subtitle,
            flags=re.IGNORECASE,
        )
        if kind and profile
        else None
    )
    if forbidden_subtitle_prefix or route_notation:
        raise RenderError(
            "document.subtitle must be reader-facing copy without document-kind "
            "prefixes or internal kind/profile routing notation"
        )

    if kind_rule and document.get("scope") is None:
        raise RenderError("document.scope is required when document.kind is used")

    scope_mode = "legacy"
    scope_sections: list[str] = []
    scope_facets: list[str] = []
    if document.get("scope") is not None:
        if not profile:
            raise RenderError("document.profile is required when document.scope is used")
        scope = require_object(document.get("scope"), "document.scope")
        scope_mode = str(scope.get("mode", "filtered")).strip().lower()
        if scope_mode not in {"filtered", "full"}:
            raise RenderError("document.scope.mode must be filtered or full")
        scope_facets = require_string_list(
            scope.get("facets", []),
            "document.scope.facets",
        )
        invalid_scope_facets = [
            facet
            for facet in scope_facets
            if not ALLOWED_SECTION_ID.fullmatch(facet)
        ]
        if invalid_scope_facets:
            raise RenderError(
                "document.scope.facets must use lowercase ids: "
                + ", ".join(invalid_scope_facets)
            )
        if kind_rule:
            missing_kind_facets = [
                facet
                for facet in kind_rule["default_facets"]
                if facet not in scope_facets
            ]
            if missing_kind_facets:
                raise RenderError(
                    f"document.scope.facets is missing defaults for kind {kind}: "
                    + ", ".join(missing_kind_facets)
                )
        declared_sections = require_string_list(
            scope.get("sections", []),
            "document.scope.sections",
        )
        allowed_scope_sections = set(profile_rule["allowed_ids"])
        if scope_mode == "full":
            scope_sections = list(profile_rule["allowed_ids"])
            if declared_sections and set(declared_sections) != set(scope_sections):
                raise RenderError(
                    "document.scope.sections must contain every profile section "
                    "when document.scope.mode is full"
                )
        else:
            if not declared_sections:
                raise RenderError(
                    "document.scope.sections must be non-empty in filtered mode"
                )
            unknown_scope_sections = sorted(
                set(declared_sections) - allowed_scope_sections
            )
            if unknown_scope_sections:
                raise RenderError(
                    "document.scope.sections contains sections outside "
                    f"{profile}: {', '.join(unknown_scope_sections)}"
                )
            missing_core_sections = sorted(
                set(profile_rule["core_ids"]) - set(declared_sections)
            )
            if missing_core_sections:
                raise RenderError(
                    "document.scope.sections is missing core sections: "
                    + ", ".join(missing_core_sections)
                )
            expected_plan = build_section_plan(profile, scope_facets)
            if expected_plan["unknown_facets"]:
                raise RenderError(
                    "document.scope.facets contains unknown facets: "
                    + ", ".join(expected_plan["unknown_facets"])
                )
            expected_sections = set(expected_plan["selected_sections"])
            if set(declared_sections) != expected_sections:
                missing_triggered = sorted(
                    expected_sections - set(declared_sections)
                )
                untriggered = sorted(
                    set(declared_sections) - expected_sections
                )
                details: list[str] = []
                if missing_triggered:
                    details.append(
                        "missing triggered/dependency sections="
                        + ", ".join(missing_triggered)
                    )
                if untriggered:
                    details.append(
                        "sections without facet support="
                        + ", ".join(untriggered)
                    )
                raise RenderError(
                    "document.scope.sections does not match the facet closure: "
                    + "; ".join(details)
                )
            scope_sections = [
                section_id
                for section_id in profile_rule["allowed_ids"]
                if section_id in set(declared_sections)
            ]

    project_meta = data.get("project_meta", [])
    if not isinstance(project_meta, list) or not project_meta:
        raise RenderError("project_meta must be a non-empty array")
    meta_html: list[str] = []
    for index, item in enumerate(project_meta):
        item = require_object(item, f"project_meta[{index}]")
        label = require_nonempty(item.get("label"), f"project_meta[{index}].label")
        value = require_nonempty(item.get("value"), f"project_meta[{index}].value")
        meta_html.append(
            f'<div class="project-meta-item"><span>{esc(label)}</span>'
            f"<strong>{esc(value)}</strong></div>"
        )

    summary = require_nonempty(data.get("summary"), "summary")
    pillars = data.get("pillars", [])
    if not isinstance(pillars, list):
        raise RenderError("pillars must be an array")
    pillar_html: list[str] = []
    for index, item in enumerate(pillars):
        item = require_object(item, f"pillars[{index}]")
        pillar_title = require_nonempty(item.get("title"), f"pillars[{index}].title")
        pillar_text = require_nonempty(item.get("text"), f"pillars[{index}].text")
        tag = esc(item.get("tag", f"PILLAR {index + 1:02d}"))
        pillar_html.append(
            '<article class="pillar-card">'
            f'<span class="pillar-tag">{tag}</span><h3>{esc(pillar_title)}</h3>'
            f"<p>{paragraph_text(pillar_text)}</p></article>"
        )
    pillar_section_html = ""
    if pillar_html:
        pillar_section_html = (
            '<section class="pillar-section" aria-labelledby="pillars-title">'
            '<div class="mini-header">'
            f'<h2 id="pillars-title">{esc(labels["pillars"])}</h2>'
            '</div>'
            f'<div class="pillar-grid">{"".join(pillar_html)}</div>'
            '</section>'
        )

    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        raise RenderError("sections must be a non-empty array")
    seen_ids: set[str] = set()
    toc_html: list[str] = []
    section_html: list[str] = []
    for index, section in enumerate(sections):
        section_path = f"sections[{index}]"
        section = require_object(section, section_path)
        section_id = require_nonempty(section.get("id"), f"{section_path}.id")
        if not ALLOWED_SECTION_ID.fullmatch(section_id):
            raise RenderError(
                f"{section_path}.id must match {ALLOWED_SECTION_ID.pattern}"
            )
        if section_id in seen_ids:
            raise RenderError(f"duplicate section id: {section_id}")
        seen_ids.add(section_id)
        number = str(section.get("number", f"{index + 1:02d}"))
        section_title = require_nonempty(section.get("title"), f"{section_path}.title")
        section_subtitle = str(section.get("subtitle", "")).strip()
        blocks = section.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            raise RenderError(f"{section_path}.blocks must be a non-empty array")
        content = renderer.render_many(blocks, f"{section_path}.blocks")
        toc_html.append(
            f'<a class="toc-link" href="#{esc(section_id)}" data-section="{esc(section_id)}">'
            f'<span>{esc(number)}</span><strong>{esc(section_title)}</strong></a>'
        )
        subtitle_html = (
            f"<p>{esc(section_subtitle)}</p>" if section_subtitle else ""
        )
        section_html.append(
            f'<section class="gdd-section" id="{esc(section_id)}">'
            f'<header class="section-header"><div class="section-number">{esc(number)}</div>'
            f'<div><h2>{esc(section_title)}</h2>{subtitle_html}</div></header>'
            f'<div class="section-content">{content}</div></section>'
        )

    if profile:
        allowed_profile_sections = set(profile_rule["allowed_ids"])
        canonical_sections = seen_ids & ALL_CANONICAL_SECTION_IDS
        foreign_sections = sorted(canonical_sections - allowed_profile_sections)
        if foreign_sections:
            raise RenderError(
                f"sections contains canonical ids outside {profile}: "
                + ", ".join(foreign_sections)
            )
        if scope_mode in {"filtered", "full"}:
            expected_sections = set(scope_sections)
            missing_sections = sorted(expected_sections - canonical_sections)
            extra_sections = sorted(canonical_sections - expected_sections)
            if missing_sections or extra_sections:
                details: list[str] = []
                if missing_sections:
                    details.append("missing=" + ", ".join(missing_sections))
                if extra_sections:
                    details.append("unselected=" + ", ".join(extra_sections))
                raise RenderError(
                    "sections does not match document.scope.sections: "
                    + "; ".join(details)
                )

    decisions = data.get("decisions", [])
    if not isinstance(decisions, list):
        raise RenderError("decisions must be an array")
    decision_labels = {
        "confirmed": "확정" if language.startswith("ko") else "Confirmed",
        "assumption": "가정" if language.startswith("ko") else "Assumption",
        "proposal": "제안" if language.startswith("ko") else "Proposal",
        "tbd": "검토 필요" if language.startswith("ko") else "TBD",
    }
    decision_aliases = {
        "확정": "confirmed",
        "가정": "assumption",
        "제안": "proposal",
        "미정": "tbd",
        "검토 필요": "tbd",
    }
    decision_html: list[str] = []
    for index, item in enumerate(decisions):
        item_path = f"decisions[{index}]"
        item = require_object(item, item_path)
        raw_status = str(item.get("status", "tbd")).lower()
        decision_status = decision_aliases.get(raw_status, raw_status)
        if decision_status not in decision_labels:
            raise RenderError(
                f"{item_path}.status must be confirmed, assumption, proposal, or tbd"
            )
        decision_title = require_nonempty(item.get("title"), f"{item_path}.title")
        detail = require_nonempty(item.get("detail"), f"{item_path}.detail")
        owner = (
            f'<span><b>{esc(labels["decision_owner"])}</b> {esc(item["owner"])}</span>'
            if item.get("owner")
            else ""
        )
        due = (
            f'<span><b>{esc(labels["decision_due"])}</b> {esc(item["due"])}</span>'
            if item.get("due")
            else ""
        )
        decision_html.append(
            f'<article class="decision-card decision-{decision_status}">'
            f'<span class="decision-status">{esc(decision_labels[decision_status])}</span>'
            f"<h3>{esc(decision_title)}</h3><p>{paragraph_text(detail)}</p>"
            f'<div class="decision-meta">{owner}{due}</div></article>'
        )
    decision_toc_html = ""
    decision_section_html = ""
    if decision_html:
        decision_toc_html = (
            '<a class="toc-link" href="#decision-log" '
            'data-section="decision-log"><span>+</span>'
            f'<strong>{esc(labels["decisions"])}</strong></a>'
        )
        decision_section_html = (
            '<section class="closing-section" id="decision-log">'
            '<header class="closing-head"><div class="section-number">+</div>'
            f'<div><h2>{esc(labels["decisions"])}</h2></div></header>'
            f'<div class="decision-grid">{"".join(decision_html)}</div>'
            '</section>'
        )

    sources = data.get("sources", [])
    if not isinstance(sources, list):
        raise RenderError("sources must be an array")
    source_html: list[str] = []
    for index, item in enumerate(sources):
        item_path = f"sources[{index}]"
        item = require_object(item, item_path)
        label = require_nonempty(item.get("label"), f"{item_path}.label")
        url = str(item.get("url", "")).strip()
        title_html = esc(label)
        if url:
            if not re.match(r"^https?://", url, flags=re.IGNORECASE):
                raise RenderError(f"{item_path}.url must start with http:// or https://")
            title_html = (
                f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
                f"{esc(label)}</a>"
            )
        accessed = (
            f'<span>{esc(labels["source_accessed"])} · {esc(item["accessed"])}</span>'
            if item.get("accessed")
            else ""
        )
        note = f"<p>{paragraph_text(item['note'])}</p>" if item.get("note") else ""
        source_html.append(
            f'<li data-source-entry="true"><div><strong>{title_html}</strong>'
            f"{note}</div>{accessed}</li>"
        )
    source_toc_html = ""
    source_section_html = ""
    if source_html:
        source_toc_html = (
            '<a class="toc-link" href="#sources" data-section="sources">'
            f'<span>↗</span><strong>{esc(labels["sources"])}</strong></a>'
        )
        source_section_html = (
            '<section class="closing-section" id="sources">'
            '<header class="closing-head"><div class="section-number">↗</div>'
            f'<div><h2>{esc(labels["sources"])}</h2></div></header>'
            f'<ol class="source-list">{"".join(source_html)}</ol>'
            '</section>'
        )

    chart_json = json.dumps(
        renderer.chart_configs, ensure_ascii=False, separators=(",", ":")
    )
    chart_json = (
        chart_json.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    values = {
        "LANG": esc(language),
        "TITLE": esc(title),
        "META_DESCRIPTION": esc(summary[:180]),
        "PROFILE": esc(profile),
        "KIND_META": (
            f'<meta name="gdd-kind" content="{esc(kind)}">' if kind else ""
        ),
        "SCOPE_MODE": esc(scope_mode),
        "SCOPE_SECTIONS": esc(",".join(scope_sections)),
        "SCOPE_FACETS": esc(",".join(scope_facets)),
        "PROFILE_LABEL": esc(profile_label),
        "DOCUMENT_MARKER_MODE": esc(document_marker_mode),
        "DOCUMENT_MARKER_TEXT": esc(document_marker_text),
        "DESIGN_AUTHORITY_BOUNDARY": esc(labels["authority_boundary"]),
        "EYEBROW_HTML": eyebrow_html,
        "SUBTITLE": esc(subtitle),
        "STATUS": esc(status),
        "VERSION": esc(version),
        "DATE": esc(date),
        "AUTHOR": esc(document.get("author", "")),
        "CONFIDENTIALITY": esc(document.get("confidentiality", "")),
        "PROJECT_META": "".join(meta_html),
        "PILLAR_SECTION": pillar_section_html,
        "TOC_ITEMS": "".join(toc_html),
        "OPTIONAL_TOC_ITEMS": decision_toc_html + source_toc_html,
        "SECTIONS": "".join(section_html),
        "DECISION_SECTION": decision_section_html,
        "SOURCE_SECTION": source_section_html,
        "FOOTER_NOTE": paragraph_text(
            data.get("footer_note", "Generated with game-gdd-html")
        ),
        "CHART_CONFIGS": chart_json,
        "MERMAID_SCRIPT": (
            '<script defer src="https://cdn.jsdelivr.net/npm/mermaid@10/'
            'dist/mermaid.min.js"></script>'
            if renderer.mermaid_count
            else ""
        ),
        "CHART_SCRIPT": (
            '<script defer src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/'
            'dist/chart.umd.min.js"></script>'
            if renderer.chart_configs
            else ""
        ),
        "MENU_LABEL": esc(labels["menu"]),
        "CLOSE_LABEL": esc(labels["close"]),
        "CONTENTS_LABEL": esc(labels["contents"]),
        "PRINT_LABEL": esc(labels["print"]),
        "VERSION_LABEL": esc(labels["version"]),
        "STATUS_LABEL": esc(labels["status"]),
        "UPDATED_LABEL": esc(labels["updated"]),
        "AUTHOR_LABEL": esc(labels["author"]),
        "CONFIDENTIALITY_LABEL": esc(labels["confidentiality"]),
        "BACK_TO_TOP_LABEL": esc(labels["back_to_top"]),
    }
    output = compact_template(template) if compact else template
    for key, value in values.items():
        output = output.replace("{{" + key + "}}", value)
    leftovers = sorted(set(PLACEHOLDER.findall(output)))
    if leftovers:
        raise RenderError(f"unresolved template placeholders: {', '.join(leftovers)}")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a structured game GDD JSON file as a single HTML document."
    )
    parser.add_argument("input", type=Path, help="UTF-8 JSON input file")
    parser.add_argument("-o", "--output", type=Path, help="Output HTML path")
    parser.add_argument(
        "--template",
        type=Path,
        help="Optional template path; defaults to ../assets/gdd-template.html",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Keep template indentation for source debugging",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    template_path = (
        args.template
        if args.template
        else script_dir.parent / "assets" / "gdd-template.html"
    )
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RenderError("top-level JSON value must be an object")
        template = template_path.read_text(encoding="utf-8")
        output_html = render_document(data, template, compact=not args.pretty)
        if args.output:
            output_path = args.output
        else:
            output_path = default_output_path(data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_html, encoding="utf-8", newline="\n")
    except FileNotFoundError as error:
        print(f"[ERROR] File not found: {error.filename}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(
            f"[ERROR] Invalid JSON at line {error.lineno}, column {error.colno}: "
            f"{error.msg}",
            file=sys.stderr,
        )
        return 2
    except (OSError, RenderError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2
    print(f"[OK] Rendered {output_path.resolve()}")
    print(f"[INFO] Sections: {len(data.get('sections', []))}")
    profile = str(data.get("document", {}).get("profile", "")).strip()
    if profile:
        print(f"[INFO] Profile: {profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
