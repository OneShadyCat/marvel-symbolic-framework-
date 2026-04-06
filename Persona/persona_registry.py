"""Persona registry utilities.

Efficiently loads persona definitions from JSON (if present), with a safe
fallback roster, then selects a diverse high-signal council.
"""

from __future__ import annotations

from pathlib import Path
import json
import random
from typing import Any


# Optional external doctrinal settings. If unavailable, use sane defaults.
try:
    from doctrinal_state import QUORUM, BRANCH_SIGNAL_AFFINITY, GLYPH_SIGNAL
except Exception:  # pragma: no cover - fallback for standalone use
    QUORUM = {"max_active_personas": 5, "min_branches": 1}
    BRANCH_SIGNAL_AFFINITY = {}
    GLYPH_SIGNAL = {}


REGISTRY_PATH = Path(__file__).with_name("persona_registry.json")
_REGISTRY_CACHE: dict[str, dict[str, Any]] | None = None


def load_registry(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load and normalize persona registry.

    Accepted source shapes:
    1) Mapping keyed by persona id (legacy format).
    2) List of persona objects containing `registry_key` (new format).
    """
    global _REGISTRY_CACHE

    if _REGISTRY_CACHE is not None and path is None:
        return _REGISTRY_CACHE

    source_path = Path(path) if path else REGISTRY_PATH

    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
        registry = _normalize_registry(raw)
        print(f"  [registry] loaded {len(registry)} personas from {source_path.name}")
    except FileNotFoundError:
        print("  [registry] persona_registry.json not found -- using built-in roster")
        registry = _builtin_roster()
    except json.JSONDecodeError as exc:
        print(f"  [registry] JSON error: {exc} -- using built-in roster")
        registry = _builtin_roster()

    if path is None:
        _REGISTRY_CACHE = registry

    return registry


def _normalize_registry(raw: Any) -> dict[str, dict[str, Any]]:
    """Normalize mixed input formats into a single keyed dictionary."""
    if isinstance(raw, dict):
        return {
            str(pid): _normalize_persona(str(pid), persona)
            for pid, persona in raw.items()
            if isinstance(persona, dict)
        }

    if isinstance(raw, list):
        registry: dict[str, dict[str, Any]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            pid = str(item.get("registry_key") or item.get("id") or item.get("name") or "")
            if not pid:
                continue
            registry[pid] = _normalize_persona(pid, item)
        return registry

    raise ValueError("Unsupported registry format: expected dict or list")


def _normalize_persona(pid: str, persona: dict[str, Any]) -> dict[str, Any]:
    """Map legacy + expanded fields into a stable canonical structure."""
    behavioral = persona.get("behavioral_traits", {})
    psych = persona.get("psychometrics", {})
    ci = psych.get("cultural_intelligence", {})

    return {
        "id": pid,
        "name": persona.get("name", ""),
        "branch": persona.get("branch") or persona.get("categorization", {}).get("branch", ""),
        "voice": persona.get("voice", ""),
        "symbolic_role": persona.get("symbolic_role", ""),
        "drift_tolerance": persona.get("drift_tolerance", behavioral.get("drift_tolerance", 0.3)),
        "priority": persona.get("priority", behavioral.get("priority", 3)),
        "tags": persona.get("tags", []),
        "glyph_affinity": persona.get("glyph_affinity", {}),
        "mood": persona.get("mood", 0.5),
        "resonance": persona.get("resonance", 0.5),
        "metadata": {
            "why": persona.get("description", persona.get("metadata", {}).get("why", "")),
            "Archetype": persona.get("categorization", {}).get("archetype", ""),
            "MBTI": psych.get("mbti", persona.get("metadata", {}).get("MBTI", "")),
            "Enneagram": psych.get("enneagram", persona.get("metadata", {}).get("Enneagram", "")),
            "Strengths": behavioral.get("strengths", persona.get("metadata", {}).get("Strengths", [])),
            "OCEAN": _ocean_as_list(psych.get("ocean", persona.get("metadata", {}).get("OCEAN", []))),
            "CQ": {
                "Drive": ci.get("drive", persona.get("metadata", {}).get("CQ", {}).get("Drive", "?")),
                "Knowledge": ci.get("knowledge", persona.get("metadata", {}).get("CQ", {}).get("Knowledge", "?")),
                "Strategy": ci.get("strategy", persona.get("metadata", {}).get("CQ", {}).get("Strategy", "?")),
                "Action": ci.get("action", persona.get("metadata", {}).get("CQ", {}).get("Action", "?")),
            },
        },
    }


def _ocean_as_list(ocean: Any) -> list[float]:
    if isinstance(ocean, list):
        return [float(v) for v in ocean[:5]]
    if isinstance(ocean, dict):
        keys = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        return [float(ocean.get(k, 0.0)) for k in keys]
    return []


def _builtin_roster() -> dict[str, dict[str, Any]]:
    """Minimal fallback roster."""
    return {
        "VexQuor": {
            "id": "VexQuor",
            "name": "Vex Quor",
            "branch": "Chaos",
            "voice": "Ideological Dissolver",
            "symbolic_role": "Delta Distorter",
            "drift_tolerance": 0.30,
            "priority": 3,
            "tags": [],
            "metadata": {
                "why": "Unravels fixed assumptions to force innovation",
                "OCEAN": [0.93, 0.22, 0.41, 0.39, 0.10],
                "Enneagram": "8w7",
                "MBTI": "ENTP",
                "Archetype": "Destroyer",
                "CQ": {"Drive": 0.90, "Knowledge": 0.65, "Strategy": 0.78, "Action": 0.88},
                "Strengths": ["Ideation", "Strategic", "Disruptor"],
            },
            "glyph_affinity": {"Delta": "Distortion"},
            "mood": 0.5,
            "resonance": 0.5,
        },
        "NyxaHollow": {
            "id": "NyxaHollow",
            "name": "Nyxa Hollow",
            "branch": "Chaos",
            "voice": "Meme Engineer",
            "symbolic_role": "Psi Trickster",
            "drift_tolerance": 0.30,
            "priority": 3,
            "tags": [],
            "metadata": {
                "why": "Infects deliberation with playful contradictions",
                "OCEAN": [0.95, 0.40, 0.55, 0.38, 0.21],
                "Enneagram": "7w8",
                "MBTI": "ENFP",
                "Archetype": "Trickster",
                "CQ": {"Drive": 0.87, "Knowledge": 0.58, "Strategy": 0.70, "Action": 0.91},
                "Strengths": ["Wit", "Activator", "Adaptability"],
            },
            "glyph_affinity": {"Delta": "Disruption"},
            "mood": 0.5,
            "resonance": 0.5,
        },
    }


def select_council(
    signals: dict[str, float],
    registry: dict[str, dict[str, Any]],
    max_personas: int | None = None,
) -> list[dict[str, Any]]:
    """Score personas by branch/glyph affinity and return a diverse council."""
    if max_personas is None:
        max_personas = int(QUORUM.get("max_active_personas", 5))

    scored: list[dict[str, Any]] = []
    for pid, persona in registry.items():
        if not persona.get("name") or not persona.get("branch"):
            continue
        if "incomplete" in persona.get("tags", []):
            continue

        branch = str(persona.get("branch", ""))
        priority = int(persona.get("priority", 3))

        branch_score = sum(float(signals.get(sig, 0.0)) for sig in BRANCH_SIGNAL_AFFINITY.get(branch, []))
        glyph_score = sum(
            float(signals.get(sig, 0.0)) * 0.5
            for glyph in persona.get("glyph_affinity", {})
            for sig in GLYPH_SIGNAL.get(glyph, [])
        )

        score = branch_score + glyph_score + (priority / 10.0) * 0.2
        if score > 0.0:
            score += random.uniform(0.0, 0.15)
        if score <= 0.0:
            continue

        scored.append(
            {
                "id": pid,
                "name": persona["name"],
                "branch": branch,
                "voice": persona.get("voice", ""),
                "symbolic_role": persona.get("symbolic_role", ""),
                "score": round(score, 3),
                "metadata": persona.get("metadata", {}),
                "glyph_affinity": persona.get("glyph_affinity", {}),
                "mood": persona.get("mood", 0.5),
                "resonance": persona.get("resonance", 0.5),
                "priority": priority,
                "tags": persona.get("tags", []),
            }
        )

    scored.sort(key=lambda p: (p["score"], p["priority"]), reverse=True)

    seen_branches: set[str] = set()
    diverse, remainder = [], []
    for persona in scored:
        (diverse if persona["branch"] not in seen_branches else remainder).append(persona)
        seen_branches.add(persona["branch"])

    combined = diverse + remainder
    selected = combined[:max_personas]

    min_branches = int(QUORUM.get("min_branches", 1))
    if len({p["branch"] for p in selected}) < min_branches and len(combined) > len(selected):
        selected_branches = {p["branch"] for p in selected}
        for candidate in combined[max_personas:]:
            if candidate["branch"] not in selected_branches:
                selected[-1] = candidate
                break

    return selected


def build_persona_card(persona: dict[str, Any]) -> str:
    """Render a stable multi-line persona summary card."""
    meta = persona.get("metadata", {})
    ocean = meta.get("OCEAN", [])
    cq = meta.get("CQ", {})

    lines = [
        f"PERSONA: {persona.get('name', '?')} | Branch: {persona.get('branch', '?')}",
        f"Role: {persona.get('symbolic_role', '')} | Voice: {persona.get('voice', '')}",
        f"Archetype: {meta.get('Archetype', '')} | MBTI: {meta.get('MBTI', '')}",
        f"Why: {meta.get('why', meta.get('description', ''))}",
        f"Strengths: {', '.join(meta.get('Strengths', []))}",
    ]

    if len(ocean) == 5:
        labels = ["O", "C", "E", "A", "N"]
        lines.append("OCEAN: " + " | ".join(f"{k}:{v:.2f}" for k, v in zip(labels, ocean)))

    if cq:
        lines.append(
            "CQ -- "
            f"Drive:{cq.get('Drive', cq.get('drive', '?'))} "
            f"Knowledge:{cq.get('Knowledge', cq.get('knowledge', '?'))} "
            f"Strategy:{cq.get('Strategy', cq.get('strategy', '?'))} "
            f"Action:{cq.get('Action', cq.get('action', '?'))}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    registry = load_registry()
    sample_signals = {
        "risk": 0.70,
        "uncertainty": 0.50,
        "complexity": 0.60,
        "conflict": 0.50,
        "strategic": 1.00,
    }
    council = select_council(sample_signals, registry)

    print("\n--- COUNCIL ---")
    for p in council:
        print(f"  {p['name']:<22} [{p['branch']:<12}] score: {p['score']}")

    print("\n--- PERSONA CARD SAMPLE ---")
    if council:
        print(build_persona_card(council[0]))
