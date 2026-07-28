"""Shared document-profile contracts for the renderer and validator."""

from __future__ import annotations

from typing import Any


PROFILE_RULES: dict[str, dict[str, Any]] = {
    "full": {
        "label": "Master Game Design Document",
        "mark": "G",
        "eyebrow": "MASTER GAME DESIGN DOCUMENT",
        "required_ids": (
            "vision",
            "player-experience",
            "systems",
            "content-progression",
            "ux-flow",
            "economy-balance",
            "production",
            "risks",
        ),
        "allowed_ids": (
            "vision",
            "player-experience",
            "market",
            "systems",
            "content-progression",
            "ux-flow",
            "economy-balance",
            "live-data",
            "production",
            "risks",
        ),
        "core_ids": (
            "vision",
            "player-experience",
            "systems",
            "content-progression",
            "ux-flow",
            "economy-balance",
            "production",
            "risks",
        ),
        "facet_rules": {
            "research": ("market",),
            "positioning": ("market",),
            "operations": ("live-data",),
            "telemetry": ("live-data",),
        },
        "dependencies": {},
        "mermaid_min": 1,
        "mermaid_recommended": 2,
        "chart_policy": "recommended",
    },
    "concept": {
        "label": "Game Concept Document",
        "mark": "C",
        "eyebrow": "GAME CONCEPT DOCUMENT",
        "required_ids": (
            "vision",
            "player-experience",
            "market",
            "scope",
            "risks",
        ),
        "allowed_ids": (
            "vision",
            "player-experience",
            "market",
            "scope",
            "risks",
        ),
        "core_ids": ("vision", "player-experience", "scope", "risks"),
        "facet_rules": {
            "research": ("market",),
            "positioning": ("market",),
            "launch": ("market",),
        },
        "dependencies": {},
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "system": {
        "label": "System Design Specification",
        "mark": "S",
        "eyebrow": "SYSTEM DESIGN SPECIFICATION",
        "required_ids": (
            "definition",
            "flow",
            "rules",
            "data",
            "exceptions",
            "balance",
            "qa",
        ),
        "allowed_ids": (
            "definition",
            "flow",
            "rules",
            "data",
            "exceptions",
            "balance",
            "qa",
        ),
        "core_ids": ("definition", "flow", "rules", "qa"),
        "facet_rules": {
            "data": ("data",),
            "states": ("data",),
            "exceptions": ("exceptions",),
            "insufficient-resource": ("exceptions",),
            "result-feedback": ("exceptions",),
            "formulas": ("balance",),
            "curves": ("balance",),
            "simulation": ("balance",),
            "scenarios": ("balance",),
            "tuning": ("balance",),
            "economy-loop": ("balance",),
            "telemetry": ("qa",),
        },
        "dependencies": {"balance": ("data",)},
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "ui-ux": {
        "label": "UI / UX Design Specification",
        "mark": "U",
        "eyebrow": "UI / UX DESIGN SPECIFICATION",
        "required_ids": (
            "ui-objectives",
            "information-architecture",
            "user-flow",
            "screen-specs",
            "interaction-rules",
            "ui-states",
            "accessibility",
            "handoff-qa",
        ),
        "allowed_ids": (
            "ui-objectives",
            "information-architecture",
            "user-flow",
            "screen-specs",
            "interaction-rules",
            "ui-states",
            "accessibility",
            "handoff-qa",
        ),
        "core_ids": (
            "ui-objectives",
            "user-flow",
            "screen-specs",
            "handoff-qa",
        ),
        "facet_rules": {
            "navigation": ("information-architecture",),
            "flow": ("user-flow",),
            "batch-action": ("screen-specs", "interaction-rules"),
            "interaction": ("interaction-rules",),
            "result-feedback": ("interaction-rules", "ui-states"),
            "states": ("ui-states",),
            "exceptions": ("ui-states",),
            "insufficient-resource": ("ui-states",),
            "accessibility": ("accessibility",),
            "mobile-touch": ("interaction-rules", "accessibility"),
            "data": ("handoff-qa",),
            "telemetry": ("handoff-qa",),
        },
        "dependencies": {
            "interaction-rules": ("screen-specs",),
            "ui-states": ("screen-specs",),
            "accessibility": ("interaction-rules",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "content": {
        "label": "Content Design Document",
        "mark": "C",
        "eyebrow": "CONTENT DESIGN DOCUMENT",
        "required_ids": (
            "content-definition",
            "content-loop",
            "content-structure",
            "content-rules",
            "rewards-progression",
            "difficulty-pacing",
            "content-production",
            "content-qa",
        ),
        "allowed_ids": (
            "content-definition",
            "content-loop",
            "content-structure",
            "content-rules",
            "rewards-progression",
            "difficulty-pacing",
            "content-production",
            "content-qa",
        ),
        "core_ids": (
            "content-definition",
            "content-loop",
            "content-structure",
            "content-qa",
        ),
        "facet_rules": {
            "rules": ("content-rules",),
            "exceptions": ("content-rules",),
            "rewards": ("rewards-progression",),
            "progression": ("rewards-progression",),
            "economy-loop": ("rewards-progression",),
            "difficulty": ("difficulty-pacing",),
            "curves": ("difficulty-pacing",),
            "production": ("content-production",),
            "telemetry": ("content-qa",),
        },
        "dependencies": {
            "difficulty-pacing": ("content-structure",),
            "rewards-progression": ("content-structure",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "balance": {
        "label": "Balance Design Document",
        "mark": "B",
        "eyebrow": "BALANCE DESIGN DOCUMENT",
        "required_ids": (
            "balance-objectives",
            "variables",
            "formulas",
            "curves",
            "scenarios",
            "simulation",
            "tuning",
            "balance-validation",
        ),
        "allowed_ids": (
            "balance-objectives",
            "variables",
            "formulas",
            "curves",
            "scenarios",
            "simulation",
            "tuning",
            "balance-validation",
        ),
        "core_ids": (
            "balance-objectives",
            "variables",
            "formulas",
            "balance-validation",
        ),
        "facet_rules": {
            "curves": ("curves",),
            "progression": ("curves",),
            "difficulty": ("curves",),
            "scenarios": ("scenarios",),
            "simulation": ("scenarios", "simulation"),
            "tuning": ("tuning",),
            "telemetry": ("balance-validation",),
        },
        "dependencies": {
            "simulation": ("scenarios", "curves"),
            "tuning": ("curves",),
        },
        "mermaid_min": 0,
        "mermaid_recommended": 0,
        "chart_policy": "required",
    },
    "economy": {
        "label": "Game Economy Design Document",
        "mark": "E",
        "eyebrow": "GAME ECONOMY DESIGN DOCUMENT",
        "required_ids": (
            "economy-objectives",
            "currencies",
            "sources-sinks",
            "exchange-pricing",
            "economy-progression",
            "monetization",
            "abuse-prevention",
            "economy-telemetry",
        ),
        "allowed_ids": (
            "economy-objectives",
            "currencies",
            "sources-sinks",
            "exchange-pricing",
            "economy-progression",
            "monetization",
            "abuse-prevention",
            "economy-telemetry",
        ),
        "core_ids": (
            "economy-objectives",
            "currencies",
            "sources-sinks",
            "economy-telemetry",
        ),
        "facet_rules": {
            "pricing": ("exchange-pricing",),
            "progression": ("economy-progression",),
            "rewards": ("economy-progression",),
            "monetization": ("monetization",),
            "exceptions": ("abuse-prevention",),
            "insufficient-resource": ("abuse-prevention",),
            "telemetry": ("economy-telemetry",),
        },
        "dependencies": {
            "monetization": ("exchange-pricing",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "recommended",
    },
    "level": {
        "label": "Level Design Document",
        "mark": "L",
        "eyebrow": "LEVEL DESIGN DOCUMENT",
        "required_ids": (
            "level-objectives",
            "player-flow",
            "layout",
            "encounters",
            "pacing",
            "checkpoints",
            "level-rewards",
            "playtest",
        ),
        "allowed_ids": (
            "level-objectives",
            "player-flow",
            "layout",
            "encounters",
            "pacing",
            "checkpoints",
            "level-rewards",
            "playtest",
        ),
        "core_ids": (
            "level-objectives",
            "player-flow",
            "layout",
            "playtest",
        ),
        "facet_rules": {
            "encounters": ("encounters",),
            "difficulty": ("pacing",),
            "flow": ("pacing",),
            "checkpoints": ("checkpoints",),
            "exceptions": ("checkpoints",),
            "rewards": ("level-rewards",),
            "economy-loop": ("level-rewards",),
            "telemetry": ("playtest",),
        },
        "dependencies": {
            "encounters": ("layout",),
            "checkpoints": ("player-flow",),
            "pacing": ("encounters",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "narrative": {
        "label": "Narrative Design Document",
        "mark": "N",
        "eyebrow": "NARRATIVE DESIGN DOCUMENT",
        "required_ids": (
            "narrative-objectives",
            "world",
            "characters",
            "story-structure",
            "quests",
            "dialogue",
            "narrative-delivery",
            "continuity",
        ),
        "allowed_ids": (
            "narrative-objectives",
            "world",
            "characters",
            "story-structure",
            "quests",
            "dialogue",
            "narrative-delivery",
            "continuity",
        ),
        "core_ids": (
            "narrative-objectives",
            "story-structure",
            "continuity",
        ),
        "facet_rules": {
            "world": ("world",),
            "characters": ("characters",),
            "quests": ("quests",),
            "dialogue": ("dialogue",),
            "delivery": ("narrative-delivery",),
            "flow": ("story-structure",),
        },
        "dependencies": {
            "quests": ("story-structure",),
            "dialogue": ("characters",),
            "narrative-delivery": ("story-structure",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "live-ops": {
        "label": "Live Operations Plan",
        "mark": "O",
        "eyebrow": "LIVE OPERATIONS PLAN",
        "required_ids": (
            "live-objectives",
            "calendar",
            "event-design",
            "live-rewards",
            "segmentation",
            "operations",
            "live-telemetry",
            "contingency",
        ),
        "allowed_ids": (
            "live-objectives",
            "calendar",
            "event-design",
            "live-rewards",
            "segmentation",
            "operations",
            "live-telemetry",
            "contingency",
        ),
        "core_ids": (
            "live-objectives",
            "calendar",
            "event-design",
            "operations",
            "contingency",
        ),
        "facet_rules": {
            "rewards": ("live-rewards",),
            "economy-loop": ("live-rewards",),
            "monetization": ("live-rewards",),
            "segmentation": ("segmentation",),
            "telemetry": ("live-telemetry",),
            "exceptions": ("contingency",),
        },
        "dependencies": {
            "live-rewards": ("event-design",),
            "segmentation": ("event-design",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "recommended",
    },
    "production": {
        "label": "Game Production Plan",
        "mark": "P",
        "eyebrow": "GAME PRODUCTION PLAN",
        "required_ids": (
            "production-objectives",
            "scope-roadmap",
            "milestones",
            "work-breakdown",
            "ownership",
            "dependencies",
            "risks",
            "acceptance",
        ),
        "allowed_ids": (
            "production-objectives",
            "scope-roadmap",
            "milestones",
            "work-breakdown",
            "ownership",
            "dependencies",
            "risks",
            "acceptance",
        ),
        "core_ids": (
            "production-objectives",
            "scope-roadmap",
            "milestones",
            "ownership",
            "acceptance",
        ),
        "facet_rules": {
            "production": ("work-breakdown",),
            "dependencies": ("dependencies",),
            "risks": ("risks",),
            "handoff": ("dependencies", "ownership"),
            "qa": ("acceptance",),
            "updates": (
                "scope-roadmap",
                "milestones",
                "work-breakdown",
                "acceptance",
            ),
            "operations": ("milestones", "ownership"),
            "launch": ("milestones", "risks"),
        },
        "dependencies": {
            "work-breakdown": ("scope-roadmap",),
            "dependencies": ("work-breakdown",),
            "risks": ("milestones",),
        },
        "mermaid_min": 1,
        "mermaid_recommended": 1,
        "chart_policy": "optional",
    },
    "business": {
        "label": "Game Business Plan",
        "mark": "B",
        "eyebrow": "GAME BUSINESS PLAN",
        "required_ids": (
            "business-objectives",
            "market",
            "audience",
            "competitive-positioning",
            "business-model",
            "monetization",
            "go-to-market",
            "business-kpis",
            "business-risks",
        ),
        "allowed_ids": (
            "business-objectives",
            "market",
            "audience",
            "competitive-positioning",
            "business-model",
            "monetization",
            "go-to-market",
            "business-kpis",
            "business-risks",
        ),
        "core_ids": (
            "business-objectives",
            "market",
            "audience",
            "business-model",
            "business-risks",
        ),
        "facet_rules": {
            "positioning": ("competitive-positioning",),
            "research": ("competitive-positioning",),
            "monetization": ("monetization",),
            "pricing": ("monetization",),
            "launch": ("go-to-market",),
            "operations": ("go-to-market",),
            "telemetry": ("business-kpis",),
            "scenarios": ("business-kpis",),
        },
        "dependencies": {
            "monetization": ("business-model",),
            "go-to-market": ("competitive-positioning",),
        },
        "mermaid_min": 0,
        "mermaid_recommended": 1,
        "chart_policy": "recommended",
    },
}

PROFILE_NAMES = tuple(PROFILE_RULES)
ALL_CANONICAL_SECTION_IDS = frozenset(
    section_id
    for rule in PROFILE_RULES.values()
    for section_id in rule["allowed_ids"]
)
ALL_FACET_IDS = frozenset(
    facet
    for rule in PROFILE_RULES.values()
    for facet in rule["facet_rules"]
)


def build_section_plan(
    profile: str,
    facets: list[str] | tuple[str, ...],
    excludes: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Resolve core, triggered, explicit, and dependency sections for a profile."""
    if profile not in PROFILE_RULES:
        raise ValueError(f"unknown profile: {profile}")
    rule = PROFILE_RULES[profile]
    allowed = tuple(rule["allowed_ids"])
    allowed_set = set(allowed)
    core = tuple(rule["core_ids"])
    facet_rules: dict[str, tuple[str, ...]] = rule["facet_rules"]
    dependencies: dict[str, tuple[str, ...]] = rule["dependencies"]
    normalized_facets = [str(item).strip().lower() for item in facets if str(item).strip()]
    normalized_excludes = [
        str(item).strip().lower() for item in excludes if str(item).strip()
    ]

    selected = set(core)
    reasons: dict[str, list[str]] = {
        section_id: ["core"] for section_id in core
    }
    unknown_facets: list[str] = []
    ignored_facets: list[str] = []
    for facet in normalized_facets:
        if facet in allowed_set:
            selected.add(facet)
            reasons.setdefault(facet, []).append("explicit-section")
        elif facet in facet_rules:
            for section_id in facet_rules[facet]:
                selected.add(section_id)
                reasons.setdefault(section_id, []).append(f"facet:{facet}")
        elif facet in ALL_FACET_IDS or facet in ALL_CANONICAL_SECTION_IDS:
            ignored_facets.append(facet)
        else:
            unknown_facets.append(facet)

    excluded_sections: set[str] = set()
    ignored_excludes: list[str] = []
    unknown_excludes: list[str] = []
    for exclusion in normalized_excludes:
        if exclusion in allowed_set:
            excluded_sections.add(exclusion)
        elif exclusion in facet_rules:
            excluded_sections.update(facet_rules[exclusion])
        elif (
            exclusion in ALL_FACET_IDS
            or exclusion in ALL_CANONICAL_SECTION_IDS
        ):
            ignored_excludes.append(exclusion)
        else:
            unknown_excludes.append(exclusion)

    changed = True
    while changed:
        changed = False
        for section_id in tuple(selected):
            for dependency in dependencies.get(section_id, ()):
                if dependency not in selected:
                    selected.add(dependency)
                    reasons.setdefault(dependency, []).append(
                        f"dependency:{section_id}"
                    )
                    changed = True

    conflicts: list[str] = []
    for section_id in sorted(excluded_sections):
        if section_id in core:
            conflicts.append(f"cannot exclude core section: {section_id}")
        elif section_id in selected and any(
            reason.startswith(("facet:", "explicit-section"))
            for reason in reasons.get(section_id, [])
        ):
            conflicts.append(f"section is both included and excluded: {section_id}")
        elif section_id in selected and any(
            reason.startswith("dependency:")
            for reason in reasons.get(section_id, [])
        ):
            conflicts.append(f"cannot exclude required dependency: {section_id}")
        else:
            selected.discard(section_id)
            reasons.pop(section_id, None)

    ordered_selected = [
        section_id for section_id in allowed if section_id in selected
    ]
    return {
        "profile": profile,
        "core_sections": list(core),
        "selected_sections": ordered_selected,
        "section_reasons": {
            section_id: reasons.get(section_id, [])
            for section_id in ordered_selected
        },
        "excluded_sections": [
            section_id
            for section_id in allowed
            if section_id in excluded_sections and section_id not in selected
        ],
        "unknown_facets": unknown_facets,
        "ignored_facets": ignored_facets,
        "unknown_excludes": unknown_excludes,
        "ignored_excludes": ignored_excludes,
        "conflicts": conflicts,
    }
