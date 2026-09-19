from __future__ import annotations

import os
import re
from importlib import resources
from pathlib import Path
from typing import Iterable, Literal, Sequence

from .models import DEFAULT_N, MIN_N, MAX_ROSTER, PerspectiveSpec, RosterMode


def _read_spec(path: Path) -> PerspectiveSpec:
    return PerspectiveSpec.model_validate_json(path.read_text(encoding="utf-8"))


def _iter_json_files(directory: Path) -> Iterable[Path]:
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"))


def load_builtin_catalog() -> dict[str, PerspectiveSpec]:
    catalog: dict[str, PerspectiveSpec] = {}
    root = resources.files("parallax.offsets")
    for item in root.iterdir():
        if item.name.endswith(".json"):
            spec = PerspectiveSpec.model_validate_json(item.read_text(encoding="utf-8"))
            catalog[spec.id] = spec
    return catalog


def extra_catalog_dirs(explicit: Sequence[Path] | None = None) -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("PARALLAX_CATALOG_DIR", "")
    for part in env.split(":"):
        if part.strip():
            dirs.append(Path(part.strip()))
    local = Path(".parallax/offsets")
    if local.is_dir():
        dirs.append(local)
    if explicit:
        dirs.extend(explicit)
    return dirs


def load_catalog(extra_dirs: Sequence[Path] | None = None) -> dict[str, PerspectiveSpec]:
    """Builtin offsets plus drop-in JSON. Later dirs override the same id."""
    catalog = load_builtin_catalog()
    for directory in extra_catalog_dirs(extra_dirs):
        for path in _iter_json_files(directory):
            spec = _read_spec(path)
            catalog[spec.id] = spec
    return catalog


CATALOG: dict[str, PerspectiveSpec] = load_builtin_catalog()


def _haystack(domain: str | None, question: str) -> str:
    return f"{domain or ''} {question}".lower()


def _cue_hit(cue: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(cue.lower())}\b", text) is not None


def score_spec(spec: PerspectiveSpec, text: str) -> int:
    return sum(1 for cue in spec.cues if _cue_hit(cue, text))


def select_perspectives(
    question: str,
    domain: str | None = None,
    extra_ids: list[str] | None = None,
    mode: RosterMode | Literal["upto", "exactly"] = "upto",
    n: int = DEFAULT_N,
    min_n: int = MIN_N,
    catalog: dict[str, PerspectiveSpec] | None = None,
    extra_dirs: Sequence[Path] | None = None,
) -> list[PerspectiveSpec]:
    """Pick isolated offsets from the query.

    * upto N — include required seats plus cue matches, never more than N,
      never fewer than min_n (fills from the catalog by priority).
    * exactly N — always N seats: top scores, then priority fills.
    """
    if n < 1 or n > MAX_ROSTER:
        raise ValueError(f"n must be between 1 and {MAX_ROSTER}")
    pool = catalog if catalog is not None else load_catalog(extra_dirs)
    text = _haystack(domain, question)

    unknown = [pid for pid in (extra_ids or []) if pid not in pool]
    if unknown:
        raise ValueError(f"Unknown perspective ids: {', '.join(unknown)}")

    required = [spec for spec in pool.values() if spec.required]
    required.sort(key=lambda spec: (spec.priority, spec.id))

    chosen: list[str] = []
    hard: list[str] = []

    def take(pid: str, *, pinned: bool = False) -> None:
        if pid not in chosen and pid in pool:
            chosen.append(pid)
            if pinned:
                hard.append(pid)

    for spec in required:
        take(spec.id, pinned=True)
    for pid in extra_ids or []:
        take(pid, pinned=True)

    ranked = sorted(
        (spec for spec in pool.values() if spec.id not in chosen),
        key=lambda spec: (-score_spec(spec, text), spec.priority, spec.id),
    )

    if mode == "upto":
        for spec in ranked:
            if len(chosen) >= n:
                break
            if score_spec(spec, text) > 0:
                take(spec.id)
        fill_target = min(n, max(len(chosen), min_n))
        for spec in sorted(pool.values(), key=lambda spec: (spec.priority, spec.id)):
            if len(chosen) >= fill_target:
                break
            take(spec.id)
    else:
        for spec in ranked:
            if len(chosen) >= n:
                break
            take(spec.id)
        for spec in sorted(pool.values(), key=lambda spec: (spec.priority, spec.id)):
            if len(chosen) >= n:
                break
            take(spec.id)

    if len(chosen) > n:
        rest = [pid for pid in chosen if pid not in hard]
        keep_hard = hard[:n]
        chosen = keep_hard + rest[: max(0, n - len(keep_hard))]
    return [pool[pid] for pid in chosen]
