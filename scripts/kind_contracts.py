"""Fine-grained game-design document kind contracts.

This module adds a document-kind layer below the broad GDD profiles.  A kind
selects the profile renderer, supplies the facets that should be enabled by
default, and declares the concrete outputs and downstream handoffs expected for
that document.  It is intentionally data-only apart from lookup, matching, and
integrity helpers so the interpreter and authoring prompts can share one source
of truth.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any


CATEGORY_REFERENCE_FILES: dict[str, str] = {
    "project": "references/kinds/project.md",
    "system": "references/kinds/system.md",
    "combat": "references/kinds/combat.md",
    "level-content": "references/kinds/level-content.md",
    "economy-balance": "references/kinds/economy-balance.md",
    "ui-ux": "references/kinds/ui-ux.md",
    "narrative": "references/kinds/narrative.md",
    "data-tech": "references/kinds/data-tech.md",
    "operations-marketing": "references/kinds/operations-marketing.md",
}

CATEGORY_LABELS: dict[str, str] = {
    "project": "프로젝트 전체 기획",
    "system": "시스템 기획",
    "combat": "전투 기획",
    "level-content": "레벨·콘텐츠 기획",
    "economy-balance": "경제·밸런스 기획",
    "ui-ux": "UI·UX 기획",
    "narrative": "세계관·스토리 기획",
    "data-tech": "데이터·기술 협업 기획",
    "operations-marketing": "운영·마케팅 기획",
}

# The cross-functional minimum requested for every document kind.  Each kind
# appends deliverables that make its output materially different from its peers.
COMMON_REQUIRED_OUTPUTS: tuple[str, ...] = (
    "planning-intent",
    "application-scope",
    "operating-rules",
    "schedule-and-ownership",
    "data-contract",
    "ui-touchpoints",
    "exception-policy",
    "telemetry-plan",
    "completion-criteria",
)

# Facets are constrained to the vocabulary already used by profile_contracts.
# ``production`` is included here because that broad profile is introduced
# alongside this kind layer.
PROFILE_FACETS: dict[str, frozenset[str]] = {
    "full": frozenset({"research", "positioning", "operations", "telemetry"}),
    "concept": frozenset({"research", "positioning", "launch"}),
    "system": frozenset(
        {
            "data",
            "states",
            "exceptions",
            "insufficient-resource",
            "result-feedback",
            "formulas",
            "curves",
            "simulation",
            "scenarios",
            "tuning",
            "economy-loop",
            "telemetry",
        }
    ),
    "content": frozenset(
        {
            "rules",
            "exceptions",
            "rewards",
            "progression",
            "economy-loop",
            "difficulty",
            "curves",
            "production",
            "telemetry",
        }
    ),
    "balance": frozenset(
        {
            "curves",
            "progression",
            "difficulty",
            "scenarios",
            "simulation",
            "tuning",
            "telemetry",
        }
    ),
    "economy": frozenset(
        {
            "pricing",
            "progression",
            "rewards",
            "monetization",
            "exceptions",
            "insufficient-resource",
            "telemetry",
        }
    ),
    "level": frozenset(
        {
            "encounters",
            "difficulty",
            "flow",
            "checkpoints",
            "exceptions",
            "rewards",
            "economy-loop",
            "telemetry",
        }
    ),
    "ui-ux": frozenset(
        {
            "navigation",
            "flow",
            "batch-action",
            "interaction",
            "result-feedback",
            "states",
            "exceptions",
            "insufficient-resource",
            "accessibility",
            "mobile-touch",
            "data",
            "telemetry",
        }
    ),
    "narrative": frozenset(
        {"world", "characters", "quests", "dialogue", "delivery", "flow"}
    ),
    "live-ops": frozenset(
        {
            "rewards",
            "economy-loop",
            "monetization",
            "segmentation",
            "telemetry",
            "exceptions",
        }
    ),
    "production": frozenset(
        {"production", "dependencies", "risks", "qa", "updates", "operations"}
    ),
}

# Curated ownership boundaries copied from each kind's category-table row.
# Handoff order is meaningful and matches the row's ``출력:`` order.  These
# values are static by design: importing this module never reads reference files.
CURATED_KIND_BOUNDARIES: dict[str, dict[str, tuple[str, ...]]] = {
    "game-proposal": {
        "default_excludes": (
            "detailed-rules",
            "screen-specifications",
            "balance-values",
            "task-level-schedule",
        ),
        "handoffs": ("game-concept", "development-plan", "master-gdd"),
    },
    "game-concept": {
        "default_excludes": (
            "detailed-system-rules",
            "production-schedule",
            "logical-data-details",
            "final-art",
        ),
        "handoffs": ("master-gdd", "world-bible", "ui-spec"),
    },
    "master-gdd": {
        "default_excludes": (
            "child-kind-details",
            "detailed-tables",
            "detailed-values",
            "wireframe-duplication",
        ),
        "handoffs": ("development-plan", "data-table-spec", "logging-spec"),
    },
    "development-plan": {
        "default_excludes": (
            "game-rules",
            "balance-design",
            "ui-layout",
            "marketing-copy",
        ),
        "handoffs": ("update-spec",),
    },
    "character-system": {
        "default_excludes": (
            "combat-controls-and-roles",
            "final-growth-curves",
            "screen-layout",
        ),
        "handoffs": (
            "character-combat",
            "progression-balance",
            "data-table-spec",
            "ui-spec",
        ),
    },
    "item-system": {
        "default_excludes": (
            "store-pricing",
            "reward-and-drop-rates",
            "screen-layout",
        ),
        "handoffs": (
            "reward-design",
            "store-product",
            "data-table-spec",
            "ui-spec",
            "exception-spec",
        ),
    },
    "quest-system": {
        "default_excludes": (
            "story-dialogue",
            "reward-values",
            "screen-layout",
        ),
        "handoffs": (
            "reward-design",
            "ui-spec",
            "logging-spec",
            "exception-spec",
        ),
    },
    "achievement-system": {
        "default_excludes": (
            "reward-values",
            "badge-visual-design",
            "event-kpis",
        ),
        "handoffs": (
            "reward-design",
            "ui-spec",
            "logging-spec",
            "data-table-spec",
        ),
    },
    "crafting-enhancement-system": {
        "default_excludes": (
            "final-probability-and-cost-tuning",
            "economy-totals",
            "screen-layout",
        ),
        "handoffs": (
            "random-probability-system",
            "game-economy",
            "ui-spec",
            "data-table-spec",
            "logging-spec",
        ),
    },
    "matchmaking-system": {
        "default_excludes": (
            "combat-outcome-rules",
            "mmr-tuning",
            "queue-screen-layout",
        ),
        "handoffs": (
            "ux-flow",
            "logging-spec",
            "exception-spec",
            "combat-balance",
        ),
    },
    "combat-system": {
        "default_excludes": (
            "individual-skill-catalog",
            "character-specific-controls",
            "enemy-pattern-details",
            "final-coefficients",
        ),
        "handoffs": (
            "skill-design",
            "character-combat",
            "monster-boss",
            "combat-balance",
            "logging-spec",
        ),
    },
    "skill-design": {
        "default_excludes": (
            "character-role-composition",
            "final-power-values",
            "global-damage-rules",
        ),
        "handoffs": (
            "character-combat",
            "combat-balance",
            "data-table-spec",
            "control-scheme",
        ),
    },
    "character-combat": {
        "default_excludes": (
            "shared-combat-resolution",
            "final-coefficients",
            "narrative-and-progression-state",
        ),
        "handoffs": (
            "control-scheme",
            "combat-balance",
            "tutorial-design",
        ),
    },
    "monster-boss": {
        "default_excludes": (
            "reward-values",
            "final-level-placement",
            "numeric-tuning",
        ),
        "handoffs": (
            "dungeon-design",
            "stage-design",
            "combat-balance",
            "reward-design",
        ),
    },
    "combat-balance": {
        "default_excludes": (
            "combat-semantic-rules",
            "skill-behavior-definitions",
            "ui-presentation",
        ),
        "handoffs": ("data-table-spec", "logging-spec", "stage-design"),
    },
    "level-design": {
        "default_excludes": (
            "individual-dungeon-rules",
            "final-art",
            "enemy-stats-and-rewards",
        ),
        "handoffs": (
            "dungeon-design",
            "stage-design",
            "tutorial-design",
            "monster-boss",
        ),
    },
    "dungeon-design": {
        "default_excludes": (
            "shared-spatial-standards",
            "enemy-ai-details",
            "final-reward-values",
            "narrative-dialogue",
        ),
        "handoffs": (
            "reward-design",
            "stage-design",
            "scenario-design",
            "logging-spec",
        ),
    },
    "stage-design": {
        "default_excludes": (
            "world-route-design",
            "global-combat-rules",
            "progression-curves",
        ),
        "handoffs": (
            "reward-design",
            "progression-balance",
            "logging-spec",
        ),
    },
    "content-design": {
        "default_excludes": (
            "shared-system-details",
            "exact-reward-values",
            "screen-layout",
            "season-calendar",
        ),
        "handoffs": (
            "ui-spec",
            "reward-design",
            "event-plan",
            "logging-spec",
        ),
    },
    "tutorial-design": {
        "default_excludes": (
            "final-ui-art",
            "global-difficulty-curve",
            "final-localized-copy",
        ),
        "handoffs": ("ui-spec", "stage-design", "logging-spec"),
    },
    "game-economy": {
        "default_excludes": (
            "individual-reward-conditions",
            "product-copy-and-placement",
            "probability-pools",
        ),
        "handoffs": (
            "reward-design",
            "store-product",
            "progression-balance",
            "logging-spec",
        ),
    },
    "reward-design": {
        "default_excludes": (
            "store-pricing",
            "content-progression-rules",
            "probability-pool-weights",
        ),
        "handoffs": (
            "data-table-spec",
            "ui-spec",
            "logging-spec",
            "exception-spec",
        ),
    },
    "progression-balance": {
        "default_excludes": (
            "progression-state-rules",
            "store-pricing",
            "individual-combat-coefficients",
        ),
        "handoffs": (
            "stage-design",
            "reward-design",
            "data-table-spec",
            "logging-spec",
        ),
    },
    "random-probability-system": {
        "default_excludes": (
            "product-pricing-and-bundles",
            "post-acquisition-item-use",
            "ui-layout",
        ),
        "handoffs": (
            "store-product",
            "reward-design",
            "data-table-spec",
            "logging-spec",
        ),
    },
    "store-product": {
        "default_excludes": (
            "global-economy-balance",
            "promotion-campaign-messaging",
            "payment-screen-visuals",
        ),
        "handoffs": (
            "product-promotion",
            "ui-spec",
            "logging-spec",
            "exception-spec",
        ),
    },
    "ui-spec": {
        "default_excludes": (
            "game-rules-and-calculations",
            "final-visual-art",
            "input-device-conflict-policy",
        ),
        "handoffs": ("wireframe", "data-table-spec", "exception-spec"),
    },
    "ux-flow": {
        "default_excludes": (
            "pixel-layout",
            "final-copy",
            "internal-calculations-and-physical-data-structure",
        ),
        "handoffs": (
            "ui-spec",
            "wireframe",
            "logging-spec",
            "tutorial-design",
        ),
    },
    "wireframe": {
        "default_excludes": (
            "final-visual-style",
            "system-logic",
            "error-handling-guarantee",
        ),
        "handoffs": ("ui-spec",),
    },
    "control-scheme": {
        "default_excludes": (
            "combat-outcome-resolution",
            "screen-layout",
            "platform-sdk-implementation",
        ),
        "handoffs": ("tutorial-design", "exception-spec"),
    },
    "world-bible": {
        "default_excludes": (
            "main-event-sequence",
            "individual-character-arcs",
            "final-dialogue",
            "game-values",
        ),
        "handoffs": ("scenario-design", "character-bible", "level-design"),
    },
    "scenario-design": {
        "default_excludes": (
            "world-encyclopedia-duplication",
            "final-dialogue",
            "quest-resolution-and-rewards",
        ),
        "handoffs": ("dialogue-script", "quest-system", "dungeon-design"),
    },
    "character-bible": {
        "default_excludes": (
            "combat-kit-and-stats",
            "full-scene-dialogue",
            "shared-world-rules",
        ),
        "handoffs": (
            "scenario-design",
            "dialogue-script",
            "character-combat",
        ),
    },
    "dialogue-script": {
        "default_excludes": (
            "macro-story-changes",
            "new-world-rules",
            "screen-layout",
            "quest-resolution",
        ),
        "handoffs": ("quest-system", "ui-spec", "data-table-spec"),
    },
    "data-table-spec": {
        "default_excludes": (
            "game-rule-decisions",
            "final-balance-approval",
            "runtime-logging",
        ),
        "handoffs": ("logging-spec", "update-spec"),
    },
    "logic-rule-spec": {
        "default_excludes": (
            "ui-presentation",
            "balance-targets-and-tuning",
            "physical-data-structure",
        ),
        "handoffs": ("data-table-spec", "exception-spec"),
    },
    "logging-spec": {
        "default_excludes": (
            "game-rules",
            "kpi-target-values",
            "dashboard-visual-design",
            "raw-personal-data",
        ),
        "handoffs": ("live-ops-plan", "game-economy"),
    },
    "exception-spec": {
        "default_excludes": (
            "normal-flow-duplication",
            "ui-visual-design",
            "infrastructure-architecture",
        ),
        "handoffs": ("ui-spec", "logging-spec", "update-spec"),
    },
    "event-plan": {
        "default_excludes": (
            "permanent-system-details",
            "final-reward-rationale",
            "promotion-copy",
        ),
        "handoffs": (
            "live-ops-plan",
            "ui-spec",
            "logging-spec",
            "exception-spec",
        ),
    },
    "live-ops-plan": {
        "default_excludes": (
            "individual-feature-specs",
            "individual-event-details",
            "marketing-creative",
        ),
        "handoffs": ("development-plan", "update-spec", "event-plan"),
    },
    "product-promotion": {
        "default_excludes": (
            "sku-composition-and-list-price",
            "payment-implementation",
            "final-creative-assets",
        ),
        "handoffs": ("ui-spec", "live-ops-plan", "logging-spec"),
    },
    "update-spec": {
        "default_excludes": (
            "long-term-operations-roadmap",
            "new-feature-detailed-design",
            "task-level-development-schedule",
        ),
        "handoffs": ("live-ops-plan", "exception-spec", "logging-spec"),
    },
}


def _unique(items: Iterable[str]) -> tuple[str, ...]:
    """Return stripped strings in first-seen order."""
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _contract(
    *,
    label: str,
    category: str,
    profile: str,
    aliases: tuple[str, ...],
    default_facets: tuple[str, ...],
    required_outputs: tuple[str, ...],
    anchor: str,
) -> dict[str, Any]:
    """Build one normalized contract while keeping its public schema explicit."""
    boundary = CURATED_KIND_BOUNDARIES[anchor]
    return {
        "label": label,
        "category": category,
        "profile": profile,
        "aliases": _unique((label, *aliases)),
        "default_facets": _unique(default_facets),
        "required_outputs": _unique(
            (*COMMON_REQUIRED_OUTPUTS, *required_outputs)
        ),
        "default_excludes": _unique(boundary["default_excludes"]),
        "handoffs": _unique(boundary["handoffs"]),
        "reference": f"{CATEGORY_REFERENCE_FILES[category]}#{anchor}",
    }


KIND_CONTRACTS: dict[str, dict[str, Any]] = {
    # 1. 프로젝트 전체 기획서
    "game-proposal": _contract(
        label="게임 제안서",
        category="project",
        profile="concept",
        aliases=("게임 프로젝트 제안서", "게임 피치 문서"),
        default_facets=("research", "positioning", "launch"),
        required_outputs=(
            "genre-and-platform",
            "core-fun-pitch",
            "target-audience",
            "differentiation",
            "rough-development-schedule",
            "go-no-go-criteria",
        ),
        anchor="game-proposal",
    ),
    "game-concept": _contract(
        label="게임 콘셉트 기획서",
        category="project",
        profile="concept",
        aliases=("게임 컨셉 기획서", "게임 콘셉트 문서"),
        default_facets=("positioning",),
        required_outputs=(
            "creative-direction",
            "world-premise",
            "intended-player-experience",
            "concept-keywords",
            "visual-concept",
            "scope-boundaries",
        ),
        anchor="game-concept",
    ),
    "master-gdd": _contract(
        label="게임 디자인 문서·GDD",
        category="project",
        profile="full",
        aliases=(
            "마스터 GDD",
            "통합 GDD",
            "통합 게임 기획서",
            "전체 게임 디자인 문서",
        ),
        default_facets=("research", "operations", "telemetry"),
        required_outputs=(
            "game-pillars",
            "system-map",
            "content-and-progression-map",
            "combat-growth-ui-economy-integration",
            "production-assumptions",
            "master-acceptance-criteria",
        ),
        anchor="master-gdd",
    ),
    "development-plan": _contract(
        label="개발 일정 기획서",
        category="project",
        profile="production",
        aliases=("게임 개발 일정표", "개발 로드맵 기획서"),
        default_facets=("production", "dependencies", "risks", "qa"),
        required_outputs=(
            "milestones",
            "work-breakdown",
            "owners-and-raci",
            "priorities",
            "dependency-map",
            "definition-of-done",
        ),
        anchor="development-plan",
    ),
    # 2. 시스템 기획서
    "character-system": _contract(
        label="캐릭터 시스템 기획서",
        category="system",
        profile="system",
        aliases=("캐릭터 성장 시스템 기획서", "캐릭터 능력치 시스템 문서"),
        default_facets=("data", "states", "formulas", "curves", "telemetry"),
        required_outputs=(
            "attribute-model",
            "level-and-growth-rules",
            "class-and-role-model",
            "skill-connection",
            "character-state-table",
        ),
        anchor="character-system",
    ),
    "item-system": _contract(
        label="아이템 시스템 기획서",
        category="system",
        profile="system",
        aliases=("아이템 규칙 기획서", "인벤토리 아이템 시스템 문서"),
        default_facets=("data", "states", "exceptions", "telemetry"),
        required_outputs=(
            "item-taxonomy",
            "rarity-model",
            "acquisition-rules",
            "use-and-equip-conditions",
            "effect-resolution",
        ),
        anchor="item-system",
    ),
    "quest-system": _contract(
        label="퀘스트 시스템 기획서",
        category="system",
        profile="system",
        aliases=("임무 시스템 기획서", "퀘스트 규칙 정의서"),
        default_facets=("data", "states", "exceptions", "telemetry"),
        required_outputs=(
            "quest-lifecycle",
            "acceptance-conditions",
            "progress-triggers",
            "completion-conditions",
            "reward-delivery",
        ),
        anchor="quest-system",
    ),
    "achievement-system": _contract(
        label="업적 시스템 기획서",
        category="system",
        profile="system",
        aliases=("도전과제 시스템 기획서", "업적 규칙 문서"),
        default_facets=("data", "states", "result-feedback", "telemetry"),
        required_outputs=(
            "achievement-condition-model",
            "tier-and-stage-rules",
            "claim-policy",
            "display-policy",
            "retroactive-evaluation-policy",
        ),
        anchor="achievement-system",
    ),
    "crafting-enhancement-system": _contract(
        label="제작·강화 시스템 기획서",
        category="system",
        profile="system",
        aliases=("제작 강화 기획서", "강화 시스템 기획서"),
        default_facets=(
            "data",
            "states",
            "exceptions",
            "insufficient-resource",
            "formulas",
            "curves",
            "result-feedback",
            "telemetry",
        ),
        required_outputs=(
            "material-recipe",
            "success-probability",
            "cost-formula",
            "failure-and-protection-rules",
            "enhancement-state-transition",
        ),
        anchor="crafting-enhancement-system",
    ),
    "matchmaking-system": _contract(
        label="매칭 시스템 기획서",
        category="system",
        profile="system",
        aliases=("대전 매칭 기획서", "매치메이킹 시스템 문서"),
        default_facets=("data", "states", "exceptions", "scenarios", "telemetry"),
        required_outputs=(
            "matching-eligibility",
            "skill-rating-model",
            "region-platform-and-pool-policy",
            "queue-expansion-rules",
            "party-and-cancel-policy",
        ),
        anchor="matchmaking-system",
    ),
    # 3. 전투 기획서
    "combat-system": _contract(
        label="전투 시스템 기획서",
        category="combat",
        profile="system",
        aliases=("전투 규칙 기획서", "코어 전투 시스템 문서"),
        default_facets=(
            "data",
            "states",
            "exceptions",
            "formulas",
            "scenarios",
            "telemetry",
        ),
        required_outputs=(
            "combat-loop",
            "attack-defense-evasion-rules",
            "damage-formula",
            "combat-state-and-transition-model",
            "victory-defeat-exit-rules",
        ),
        anchor="combat-system",
    ),
    "skill-design": _contract(
        label="스킬 기획서",
        category="combat",
        profile="system",
        aliases=("전투 스킬 기획서", "액티브·패시브 스킬 문서"),
        default_facets=(
            "data",
            "states",
            "exceptions",
            "formulas",
            "curves",
            "telemetry",
        ),
        required_outputs=(
            "skill-taxonomy",
            "effect-and-targeting",
            "range-and-area",
            "cooldown-and-resource-cost",
            "presentation-cues",
        ),
        anchor="skill-design",
    ),
    "character-combat": _contract(
        label="캐릭터 전투 기획서",
        category="combat",
        profile="system",
        aliases=("플레이어 캐릭터 전투 문서", "캐릭터별 전투 설계서"),
        default_facets=("data", "states", "formulas", "scenarios", "telemetry"),
        required_outputs=(
            "combat-role",
            "input-and-action-set",
            "strengths-and-weaknesses",
            "combo-and-cancel-rules",
            "matchup-assumptions",
        ),
        anchor="character-combat",
    ),
    "monster-boss": _contract(
        label="몬스터·보스 기획서",
        category="combat",
        profile="system",
        aliases=("몬스터 보스 설계서", "적 AI·보스 패턴 기획서"),
        default_facets=("data", "states", "exceptions", "scenarios", "telemetry"),
        required_outputs=(
            "enemy-archetypes",
            "stat-and-resistance-model",
            "behavior-rules",
            "attack-patterns",
            "boss-phase-transition",
        ),
        anchor="monster-boss",
    ),
    "combat-balance": _contract(
        label="전투 밸런스 기획서",
        category="combat",
        profile="balance",
        aliases=("전투 수치 밸런스 문서", "캐릭터·무기·스킬 밸런스 기획서"),
        default_facets=(
            "curves",
            "difficulty",
            "scenarios",
            "simulation",
            "tuning",
            "telemetry",
        ),
        required_outputs=(
            "balance-targets",
            "combat-variable-dictionary",
            "damage-and-survival-curves",
            "matchup-scenarios",
            "simulation-and-tuning-plan",
        ),
        anchor="combat-balance",
    ),
    # 4. 레벨·콘텐츠 기획서
    "level-design": _contract(
        label="레벨 디자인 기획서",
        category="level-content",
        profile="level",
        aliases=("맵 레벨 기획서", "레벨 구조 설계서"),
        default_facets=(
            "encounters",
            "difficulty",
            "flow",
            "checkpoints",
            "rewards",
            "telemetry",
        ),
        required_outputs=(
            "spatial-goals",
            "layout-and-route",
            "encounter-rest-rhythm",
            "checkpoint-policy",
            "playtest-metrics",
        ),
        anchor="level-design",
    ),
    "dungeon-design": _contract(
        label="던전 기획서",
        category="level-content",
        profile="level",
        aliases=("던전 콘텐츠 기획서", "인스턴스 던전 설계서"),
        default_facets=(
            "encounters",
            "difficulty",
            "flow",
            "checkpoints",
            "exceptions",
            "rewards",
            "telemetry",
        ),
        required_outputs=(
            "dungeon-entry-and-goal",
            "room-and-route-sequence",
            "enemy-placement",
            "gimmick-and-failure-rules",
            "clear-and-reward-policy",
        ),
        anchor="dungeon-design",
    ),
    "stage-design": _contract(
        label="스테이지 기획서",
        category="level-content",
        profile="level",
        aliases=("스테이지별 기획서", "미션 스테이지 설계서"),
        default_facets=(
            "encounters",
            "difficulty",
            "flow",
            "checkpoints",
            "rewards",
            "telemetry",
        ),
        required_outputs=(
            "stage-objective",
            "stage-sequence",
            "difficulty-budget",
            "constraints",
            "clear-fail-conditions",
        ),
        anchor="stage-design",
    ),
    "content-design": _contract(
        label="콘텐츠 기획서",
        category="level-content",
        profile="content",
        aliases=("개별 콘텐츠 설계서", "게임 모드 기획서"),
        default_facets=(
            "rules",
            "exceptions",
            "rewards",
            "progression",
            "difficulty",
            "production",
            "telemetry",
        ),
        required_outputs=(
            "content-value-proposition",
            "participation-loop",
            "mode-structure",
            "entry-clear-fail-rules",
            "production-and-rotation-plan",
        ),
        anchor="content-design",
    ),
    "tutorial-design": _contract(
        label="튜토리얼 기획서",
        category="level-content",
        profile="content",
        aliases=("신규 유저 튜토리얼 설계서", "온보딩 콘텐츠 기획서"),
        default_facets=("rules", "difficulty", "production", "telemetry"),
        required_outputs=(
            "learning-objectives",
            "teaching-sequence",
            "practice-and-confirmation",
            "skip-retry-recovery-policy",
            "onboarding-success-metrics",
        ),
        anchor="tutorial-design",
    ),
    # 5. 경제·밸런스 기획서
    "game-economy": _contract(
        label="게임 경제 기획서",
        category="economy-balance",
        profile="economy",
        aliases=("재화 경제 기획서", "게임 내 경제 시스템 문서"),
        default_facets=(
            "pricing",
            "progression",
            "rewards",
            "monetization",
            "exceptions",
            "telemetry",
        ),
        required_outputs=(
            "currency-taxonomy",
            "source-sink-map",
            "exchange-and-pricing",
            "inflation-controls",
            "economy-health-metrics",
        ),
        anchor="game-economy",
    ),
    "reward-design": _contract(
        label="보상 기획서",
        category="economy-balance",
        profile="economy",
        aliases=("보상 지급 기획서", "콘텐츠 보상 설계서"),
        default_facets=("progression", "rewards", "exceptions", "telemetry"),
        required_outputs=(
            "reward-source-matrix",
            "reward-bundle-composition",
            "grant-eligibility",
            "claim-and-expiry-policy",
            "reward-budget",
        ),
        anchor="reward-design",
    ),
    "progression-balance": _contract(
        label="성장 밸런스 기획서",
        category="economy-balance",
        profile="balance",
        aliases=("레벨업 밸런스 기획서", "성장 곡선 설계서"),
        default_facets=(
            "curves",
            "progression",
            "scenarios",
            "simulation",
            "tuning",
            "telemetry",
        ),
        required_outputs=(
            "growth-targets",
            "experience-requirement-curve",
            "stat-growth-curve",
            "time-to-progress-scenarios",
            "catch-up-and-tuning-policy",
        ),
        anchor="progression-balance",
    ),
    "random-probability-system": _contract(
        label="확률형 시스템 기획서",
        category="economy-balance",
        profile="balance",
        aliases=("뽑기 확률 기획서", "랜덤 보상·천장 시스템 문서"),
        default_facets=("curves", "scenarios", "simulation", "tuning", "telemetry"),
        required_outputs=(
            "probability-table",
            "pool-and-weight-rules",
            "pity-and-guarantee-policy",
            "duplicate-and-reroll-policy",
            "distribution-simulation",
        ),
        anchor="random-probability-system",
    ),
    "store-product": _contract(
        label="상점·상품 기획서",
        category="economy-balance",
        profile="economy",
        aliases=("상점 상품 기획서", "인게임 상품 구성 문서"),
        default_facets=(
            "pricing",
            "rewards",
            "monetization",
            "exceptions",
            "insufficient-resource",
            "telemetry",
        ),
        required_outputs=(
            "store-catalog",
            "product-bundle",
            "price-and-value-policy",
            "purchase-limit-and-reset",
            "purchase-delivery-refund-policy",
        ),
        anchor="store-product",
    ),
    # 6. UI·UX 기획서
    "ui-spec": _contract(
        label="UI 기획서",
        category="ui-ux",
        profile="ui-ux",
        aliases=("게임 UI 설계서", "화면 UI 명세서"),
        default_facets=(
            "navigation",
            "flow",
            "interaction",
            "result-feedback",
            "states",
            "exceptions",
            "accessibility",
            "data",
            "telemetry",
        ),
        required_outputs=(
            "screen-inventory",
            "menu-and-navigation-map",
            "screen-layout-spec",
            "component-and-popup-rules",
            "ui-state-matrix",
        ),
        anchor="ui-spec",
    ),
    "ux-flow": _contract(
        label="UX 흐름도",
        category="ui-ux",
        profile="ui-ux",
        aliases=("사용자 경험 흐름도", "UX 플로우 기획서"),
        default_facets=(
            "navigation",
            "flow",
            "interaction",
            "result-feedback",
            "states",
            "exceptions",
            "telemetry",
        ),
        required_outputs=(
            "user-goal",
            "entry-and-exit-points",
            "happy-path",
            "branch-and-recovery-flow",
            "flow-success-metrics",
        ),
        anchor="ux-flow",
    ),
    "wireframe": _contract(
        label="와이어프레임",
        category="ui-ux",
        profile="ui-ux",
        aliases=("화면 와이어프레임", "저충실도 화면 설계서"),
        default_facets=("navigation", "flow", "interaction", "states", "accessibility"),
        required_outputs=(
            "screen-layouts",
            "content-hierarchy",
            "component-placement",
            "navigation-links",
            "state-variants",
        ),
        anchor="wireframe",
    ),
    "control-scheme": _contract(
        label="조작 기획서",
        category="ui-ux",
        profile="ui-ux",
        aliases=("입력 조작 설계서", "키보드·마우스·패드·터치 조작 문서"),
        default_facets=(
            "interaction",
            "states",
            "exceptions",
            "accessibility",
            "mobile-touch",
            "telemetry",
        ),
        required_outputs=(
            "input-device-matrix",
            "action-binding",
            "context-priority",
            "remapping-and-accessibility",
            "conflict-and-disconnect-policy",
        ),
        anchor="control-scheme",
    ),
    # 7. 세계관·스토리 기획서
    "world-bible": _contract(
        label="세계관 기획서",
        category="narrative",
        profile="narrative",
        aliases=("게임 세계관 설정서", "월드 빌딩 문서"),
        default_facets=("world", "characters"),
        required_outputs=(
            "world-premise-and-rules",
            "history-and-timeline",
            "regions",
            "races-and-factions",
            "canon-boundaries",
        ),
        anchor="world-bible",
    ),
    "scenario-design": _contract(
        label="시나리오 기획서",
        category="narrative",
        profile="narrative",
        aliases=("메인 시나리오 문서", "스토리 진행 기획서"),
        default_facets=("world", "characters", "quests", "dialogue", "delivery", "flow"),
        required_outputs=(
            "story-premise",
            "act-and-sequence-outline",
            "event-timeline",
            "branch-and-consequence",
            "quest-story-integration",
        ),
        anchor="scenario-design",
    ),
    "character-bible": _contract(
        label="캐릭터 설정서",
        category="narrative",
        profile="narrative",
        aliases=("등장인물 설정집", "캐릭터 바이블"),
        default_facets=("world", "characters", "dialogue"),
        required_outputs=(
            "identity-and-role",
            "personality-and-background",
            "goals-and-conflicts",
            "relationship-map",
            "voice-and-speech-style",
        ),
        anchor="character-bible",
    ),
    "dialogue-script": _contract(
        label="대사 스크립트",
        category="narrative",
        profile="narrative",
        aliases=("NPC 대사 문서", "컷신·선택지 대본"),
        default_facets=("characters", "dialogue", "delivery", "flow"),
        required_outputs=(
            "speaker-and-context",
            "dialogue-lines",
            "choice-and-branch",
            "cutscene-cues",
            "system-message-copy",
        ),
        anchor="dialogue-script",
    ),
    # 8. 데이터·기술 협업 기획서
    "data-table-spec": _contract(
        label="데이터 테이블 정의서",
        category="data-tech",
        profile="system",
        aliases=("게임 데이터 시트 정의서", "데이터 컬럼 명세서"),
        default_facets=("data", "states", "exceptions", "telemetry"),
        required_outputs=(
            "table-inventory",
            "data-item-dictionary",
            "units-defaults-and-ranges",
            "identifiers-and-relations",
            "sample-rows-and-validation",
        ),
        anchor="data-table-spec",
    ),
    "logic-rule-spec": _contract(
        label="로직·규칙 정의서",
        category="data-tech",
        profile="system",
        aliases=("게임 로직 정의서", "동작 규칙 명세서"),
        default_facets=("data", "states", "exceptions", "formulas", "telemetry"),
        required_outputs=(
            "preconditions",
            "inputs-and-meanings",
            "decision-rules",
            "state-transition",
            "results-and-follow-up-effects",
        ),
        anchor="logic-rule-spec",
    ),
    "logging-spec": _contract(
        label="로그 기획서",
        category="data-tech",
        profile="system",
        aliases=("이벤트 로그 정의서", "텔레메트리 로그 명세서"),
        default_facets=("data", "states", "exceptions", "telemetry"),
        required_outputs=(
            "event-taxonomy",
            "occurrence-conditions",
            "event-property-dictionary",
            "observation-context",
            "quality-and-retention-policy",
        ),
        anchor="logging-spec",
    ),
    "exception-spec": _contract(
        label="예외사항 정의서",
        category="data-tech",
        profile="system",
        aliases=("예외 처리 규칙서", "오류·경계조건 명세서"),
        default_facets=(
            "data",
            "states",
            "exceptions",
            "insufficient-resource",
            "result-feedback",
            "telemetry",
        ),
        required_outputs=(
            "exception-inventory",
            "detection-condition",
            "recovery-and-restoration-policy",
            "repeat-and-reentry-outcome",
            "user-message-and-log",
        ),
        anchor="exception-spec",
    ),
    # 9. 운영·마케팅 관련 기획서
    "event-plan": _contract(
        label="이벤트 기획서",
        category="operations-marketing",
        profile="live-ops",
        aliases=("인게임 이벤트 기획서", "기간제 이벤트 운영안"),
        default_facets=(
            "rewards",
            "economy-loop",
            "segmentation",
            "telemetry",
            "exceptions",
        ),
        required_outputs=(
            "event-period",
            "participation-conditions",
            "event-loop-and-missions",
            "reward-and-settlement",
            "operations-and-contingency",
        ),
        anchor="event-plan",
    ),
    "live-ops-plan": _contract(
        label="라이브 운영 기획서",
        category="operations-marketing",
        profile="live-ops",
        aliases=("라이브 서비스 운영안", "시즌 운영 계획서"),
        default_facets=(
            "rewards",
            "economy-loop",
            "monetization",
            "segmentation",
            "telemetry",
            "exceptions",
        ),
        required_outputs=(
            "operations-objectives",
            "update-and-season-calendar",
            "content-rotation",
            "staffing-and-runbook",
            "incident-and-recovery-policy",
        ),
        anchor="live-ops-plan",
    ),
    "product-promotion": _contract(
        label="상품 프로모션 기획서",
        category="operations-marketing",
        profile="live-ops",
        aliases=("패키지 프로모션 기획서", "상품 할인·노출 운영안"),
        default_facets=(
            "rewards",
            "monetization",
            "segmentation",
            "telemetry",
            "exceptions",
        ),
        required_outputs=(
            "promotion-objective",
            "target-segment",
            "offer-and-discount",
            "placement-and-exposure",
            "schedule-and-performance-metrics",
        ),
        anchor="product-promotion",
    ),
    "update-spec": _contract(
        label="업데이트 명세서",
        category="operations-marketing",
        profile="production",
        aliases=("게임 업데이트 변경 명세서", "패치 업데이트 사양서"),
        default_facets=("updates", "dependencies", "risks", "qa", "operations"),
        required_outputs=(
            "change-inventory",
            "added-changed-removed-items",
            "dependency-and-continuity-requirements",
            "release-and-recovery-criteria",
            "verification-and-communication",
        ),
        anchor="update-spec",
    ),
}

KIND_NAMES: tuple[str, ...] = tuple(KIND_CONTRACTS)

EXPECTED_CATEGORY_COUNTS: dict[str, int] = {
    "project": 4,
    "system": 6,
    "combat": 5,
    "level-content": 5,
    "economy-balance": 5,
    "ui-ux": 4,
    "narrative": 4,
    "data-tech": 4,
    "operations-marketing": 4,
}

EXPECTED_KIND_PROFILE_MAP: dict[str, str] = {
    "game-proposal": "concept",
    "game-concept": "concept",
    "master-gdd": "full",
    "development-plan": "production",
    "character-system": "system",
    "item-system": "system",
    "quest-system": "system",
    "achievement-system": "system",
    "crafting-enhancement-system": "system",
    "matchmaking-system": "system",
    "combat-system": "system",
    "skill-design": "system",
    "character-combat": "system",
    "monster-boss": "system",
    "combat-balance": "balance",
    "level-design": "level",
    "dungeon-design": "level",
    "stage-design": "level",
    "content-design": "content",
    "tutorial-design": "content",
    "game-economy": "economy",
    "reward-design": "economy",
    "progression-balance": "balance",
    "random-probability-system": "balance",
    "store-product": "economy",
    "ui-spec": "ui-ux",
    "ux-flow": "ui-ux",
    "wireframe": "ui-ux",
    "control-scheme": "ui-ux",
    "world-bible": "narrative",
    "scenario-design": "narrative",
    "character-bible": "narrative",
    "dialogue-script": "narrative",
    "data-table-spec": "system",
    "logic-rule-spec": "system",
    "logging-spec": "system",
    "exception-spec": "system",
    "event-plan": "live-ops",
    "live-ops-plan": "live-ops",
    "product-promotion": "live-ops",
    "update-spec": "production",
}

_REQUIRED_FIELDS = frozenset(
    {
        "label",
        "category",
        "profile",
        "aliases",
        "default_facets",
        "required_outputs",
        "default_excludes",
        "handoffs",
        "reference",
    }
)
_KIND_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SCOPE_TOKEN_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEPARATOR_RE = re.compile(r"[\s\-_/·ㆍ:;,.()\[\]{}]+")


def normalize_kind_text(value: str) -> str:
    """Normalize Korean/English document names for exact and phrase matching."""
    normalized = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    normalized = _SEPARATOR_RE.sub(" ", normalized)
    return " ".join(normalized.split())


def _build_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for kind_name, contract in KIND_CONTRACTS.items():
        candidates = (kind_name, contract["label"], *contract["aliases"])
        for candidate in candidates:
            normalized = normalize_kind_text(candidate)
            previous = index.get(normalized)
            if previous is not None and previous != kind_name:
                raise ValueError(
                    f"duplicate normalized kind alias {candidate!r}: "
                    f"{previous}, {kind_name}"
                )
            index[normalized] = kind_name
    return index


_ALIAS_INDEX = _build_alias_index()


def lookup_kind_name(value: str) -> str:
    """Resolve an exact kind id, label, or alias to its canonical kind id.

    Raises:
        KeyError: if ``value`` has no exact normalized match.
    """
    normalized = normalize_kind_text(value)
    try:
        return _ALIAS_INDEX[normalized]
    except KeyError as exc:
        raise KeyError(f"unknown document kind: {value}") from exc


def lookup_kind(value: str) -> dict[str, Any]:
    """Return the contract for an exact kind id, label, or alias."""
    return KIND_CONTRACTS[lookup_kind_name(value)]


def match_kind_names(
    text: str,
    *,
    category: str | None = None,
    profile: str | None = None,
    limit: int | None = None,
) -> tuple[str, ...]:
    """Return kind ids whose label or alias occurs in free-form ``text``.

    Exact whole-text matches rank first.  Phrase matches rank by the longest,
    most specific alias and then by registry order.  Category/profile filters
    are optional and matching is deterministic.
    """
    normalized_text = normalize_kind_text(text)
    if not normalized_text:
        return ()
    if category is not None and category not in CATEGORY_REFERENCE_FILES:
        raise ValueError(f"unknown category: {category}")
    if profile is not None and profile not in PROFILE_FACETS:
        raise ValueError(f"unknown profile: {profile}")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")

    registry_order = {name: index for index, name in enumerate(KIND_NAMES)}
    best_scores: dict[str, tuple[int, int, int]] = {}
    for alias, kind_name in _ALIAS_INDEX.items():
        contract = KIND_CONTRACTS[kind_name]
        if category is not None and contract["category"] != category:
            continue
        if profile is not None and contract["profile"] != profile:
            continue
        exact = int(alias == normalized_text)
        phrase = alias in normalized_text
        if not phrase:
            continue
        compact_length = len(alias.replace(" ", ""))
        token_count = len(alias.split())
        score = (exact, compact_length, token_count)
        if score > best_scores.get(kind_name, (-1, -1, -1)):
            best_scores[kind_name] = score

    ranked = sorted(
        best_scores,
        key=lambda name: (
            -best_scores[name][0],
            -best_scores[name][1],
            -best_scores[name][2],
            registry_order[name],
        ),
    )
    if limit is not None:
        ranked = ranked[:limit]
    return tuple(ranked)


def match_kinds(
    text: str,
    *,
    category: str | None = None,
    profile: str | None = None,
    limit: int | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return contracts matched in free-form text, in specificity order."""
    return tuple(
        KIND_CONTRACTS[name]
        for name in match_kind_names(
            text, category=category, profile=profile, limit=limit
        )
    )


def match_kind(
    text: str,
    *,
    category: str | None = None,
    profile: str | None = None,
) -> dict[str, Any] | None:
    """Return the best free-form match, or ``None`` when no kind is present."""
    matches = match_kinds(text, category=category, profile=profile, limit=1)
    return matches[0] if matches else None


def kinds_for_profile(profile: str) -> tuple[str, ...]:
    """Return all kind ids rendered by ``profile`` in registry order."""
    if profile not in PROFILE_FACETS:
        raise ValueError(f"unknown profile: {profile}")
    return tuple(
        kind_name
        for kind_name, contract in KIND_CONTRACTS.items()
        if contract["profile"] == profile
    )


def kinds_for_category(category: str) -> tuple[str, ...]:
    """Return all kind ids in one of the nine document categories."""
    if category not in CATEGORY_REFERENCE_FILES:
        raise ValueError(f"unknown category: {category}")
    return tuple(
        kind_name
        for kind_name, contract in KIND_CONTRACTS.items()
        if contract["category"] == category
    )


def validate_kind_contracts(
    contracts: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    """Return all contract-integrity errors without mutating the registry."""
    source = KIND_CONTRACTS if contracts is None else contracts
    errors: list[str] = []

    if contracts is None:
        if len(CATEGORY_REFERENCE_FILES) != 9:
            errors.append(
                "CATEGORY_REFERENCE_FILES must contain exactly 9 categories"
            )
        if set(CATEGORY_REFERENCE_FILES) != set(CATEGORY_LABELS):
            errors.append(
                "CATEGORY_LABELS and CATEGORY_REFERENCE_FILES keys differ"
            )
        if len(source) != 41:
            errors.append(f"expected 41 document kinds, found {len(source)}")
        if tuple(source) != KIND_NAMES:
            errors.append("KIND_NAMES does not match KIND_CONTRACTS order")
        if set(source) != set(EXPECTED_KIND_PROFILE_MAP):
            errors.append("kind registry differs from EXPECTED_KIND_PROFILE_MAP")
        if set(source) != set(CURATED_KIND_BOUNDARIES):
            errors.append(
                "kind registry differs from CURATED_KIND_BOUNDARIES"
            )

    normalized_alias_owner: dict[str, str] = {}
    actual_category_counts = {
        category: 0 for category in CATEGORY_REFERENCE_FILES
    }
    for kind_name, contract in source.items():
        if not _KIND_NAME_RE.fullmatch(kind_name):
            errors.append(f"{kind_name}: invalid canonical kind id")

        fields = set(contract)
        missing = _REQUIRED_FIELDS - fields
        extra = fields - _REQUIRED_FIELDS
        if missing:
            errors.append(
                f"{kind_name}: missing fields {sorted(missing)}"
            )
        if extra:
            errors.append(f"{kind_name}: unknown fields {sorted(extra)}")
        if missing:
            continue

        label = contract["label"]
        category = contract["category"]
        profile = contract["profile"]
        aliases = contract["aliases"]
        facets = contract["default_facets"]
        outputs = contract["required_outputs"]
        excludes = contract["default_excludes"]
        handoffs = contract["handoffs"]
        reference = contract["reference"]

        if not isinstance(label, str) or not label.strip():
            errors.append(f"{kind_name}: label must be a non-empty string")
        if category not in CATEGORY_REFERENCE_FILES:
            errors.append(f"{kind_name}: unknown category {category!r}")
        else:
            actual_category_counts[category] += 1
        if profile not in PROFILE_FACETS:
            errors.append(f"{kind_name}: unknown profile {profile!r}")

        for field_name, values, require_nonempty in (
            ("aliases", aliases, True),
            ("default_facets", facets, False),
            ("required_outputs", outputs, True),
            ("default_excludes", excludes, False),
            ("handoffs", handoffs, False),
        ):
            if not isinstance(values, tuple):
                errors.append(f"{kind_name}: {field_name} must be a tuple")
                continue
            if require_nonempty and not values:
                errors.append(f"{kind_name}: {field_name} may not be empty")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                errors.append(
                    f"{kind_name}: {field_name} contains an empty/non-string value"
                )
            if len(values) != len(set(values)):
                errors.append(f"{kind_name}: {field_name} contains duplicates")

        if isinstance(aliases, tuple):
            if aliases and aliases[0] != label:
                errors.append(
                    f"{kind_name}: first alias must be the primary Korean label"
                )
            for alias in (kind_name, *aliases):
                normalized = normalize_kind_text(alias)
                if not normalized:
                    errors.append(f"{kind_name}: alias normalizes to empty")
                    continue
                previous = normalized_alias_owner.get(normalized)
                if previous is not None and previous != kind_name:
                    errors.append(
                        f"{kind_name}: normalized alias {alias!r} "
                        f"collides with {previous}"
                    )
                normalized_alias_owner[normalized] = kind_name

        if profile in PROFILE_FACETS and isinstance(facets, tuple):
            invalid_facets = set(facets) - PROFILE_FACETS[profile]
            if invalid_facets:
                errors.append(
                    f"{kind_name}: facets not supported by {profile}: "
                    f"{sorted(invalid_facets)}"
                )

        if isinstance(outputs, tuple):
            missing_common = set(COMMON_REQUIRED_OUTPUTS) - set(outputs)
            if missing_common:
                errors.append(
                    f"{kind_name}: missing common outputs "
                    f"{sorted(missing_common)}"
                )
            if not set(outputs) - set(COMMON_REQUIRED_OUTPUTS):
                errors.append(
                    f"{kind_name}: requires at least one kind-specific output"
                )

        if isinstance(excludes, tuple):
            if not 2 <= len(excludes) <= 4:
                errors.append(
                    f"{kind_name}: default_excludes must contain 2 to 4 tokens"
                )
            invalid_excludes = [
                token
                for token in excludes
                if not _SCOPE_TOKEN_RE.fullmatch(token)
            ]
            if invalid_excludes:
                errors.append(
                    f"{kind_name}: default_excludes must use lowercase "
                    "ASCII kebab-case ids: "
                    + ", ".join(invalid_excludes)
                )

        if isinstance(handoffs, tuple):
            unknown_handoffs = set(handoffs) - set(source)
            if unknown_handoffs:
                errors.append(
                    f"{kind_name}: unknown handoffs {sorted(unknown_handoffs)}"
                )
            if kind_name in handoffs:
                errors.append(f"{kind_name}: may not hand off to itself")

        curated_boundary = CURATED_KIND_BOUNDARIES.get(kind_name)
        if curated_boundary is not None:
            curated_excludes = tuple(curated_boundary["default_excludes"])
            curated_handoffs = tuple(curated_boundary["handoffs"])
            if isinstance(excludes, tuple) and excludes != curated_excludes:
                errors.append(
                    f"{kind_name}: default_excludes differ from the curated "
                    "category-row boundary or order"
                )
            if isinstance(handoffs, tuple) and handoffs != curated_handoffs:
                errors.append(
                    f"{kind_name}: handoffs differ from the curated "
                    "category-row output ids or order"
                )

        if category in CATEGORY_REFERENCE_FILES:
            expected_prefix = CATEGORY_REFERENCE_FILES[category] + "#"
            if (
                not isinstance(reference, str)
                or not reference.startswith(expected_prefix)
                or reference == expected_prefix
            ):
                errors.append(
                    f"{kind_name}: reference must start with "
                    f"{expected_prefix!r} and include an anchor"
                )

        expected_profile = EXPECTED_KIND_PROFILE_MAP.get(kind_name)
        if expected_profile is not None and profile != expected_profile:
            errors.append(
                f"{kind_name}: expected profile {expected_profile!r}, "
                f"found {profile!r}"
            )

    if contracts is None and actual_category_counts != EXPECTED_CATEGORY_COUNTS:
        errors.append(
            "category counts differ: "
            f"expected {EXPECTED_CATEGORY_COUNTS}, "
            f"found {actual_category_counts}"
        )
    return errors


def assert_kind_contracts_valid(
    contracts: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Raise ``ValueError`` when any document-kind contract is inconsistent."""
    errors = validate_kind_contracts(contracts)
    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"invalid document-kind contracts:\n{formatted}")


if __name__ == "__main__":
    assert_kind_contracts_valid()
    print(
        f"OK: {len(KIND_CONTRACTS)} document kinds, "
        f"{len(CATEGORY_REFERENCE_FILES)} categories, "
        f"{len(PROFILE_FACETS)} profiles"
    )
