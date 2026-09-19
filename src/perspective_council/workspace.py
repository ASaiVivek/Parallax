from __future__ import annotations

import json
from pathlib import Path

from .catalog import select_perspectives
from .models import Brief, Decision, PerspectiveReport
from .packets import build_manifest, build_packets, render_synthesis_prompt
from .synthesize import heuristic_decision


def prepare_workspace(brief: Brief, dest: Path, max_perspectives: int = 5) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    specs = select_perspectives(
        brief.question,
        brief.domain,
        extra_ids=brief.extra_perspective_ids,
        max_perspectives=max_perspectives,
    )
    packets = build_packets(brief, specs)
    manifest = build_manifest(brief, specs)

    (dest / "brief.json").write_text(brief.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (dest / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")

    perspectives_dir = dest / "perspectives"
    perspectives_dir.mkdir(exist_ok=True)
    for packet in packets:
        (perspectives_dir / packet.filename).write_text(packet.prompt, encoding="utf-8")
        meta = perspectives_dir / packet.filename.replace(".md", ".json")
        meta.write_text(packet.spec.model_dump_json(indent=2) + "\n", encoding="utf-8")

    reports_dir = dest / "reports"
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "README.md").write_text(
        "Drop one JSON report per perspective here. Filenames should match the perspective id, e.g. devil_advocate.json.\n",
        encoding="utf-8",
    )

    (dest / "synthesis_prompt.md").write_text(
        render_synthesis_prompt(brief, ["(replace with isolated reports)"]),
        encoding="utf-8",
    )
    (dest / "HOW_TO_RUN.md").write_text(
        "\n".join(
            [
                "# Run isolated",
                "",
                "1. For each file in `perspectives/*.md`, start a **new** chat/agent/CLI session.",
                "2. Paste only that file. Do not include other perspectives or prior answers.",
                "3. Save the JSON output to `reports/<perspective_id>.json`.",
                "4. Run `council synthesize <this-dir>` or paste `synthesis_prompt.md` into a fresh session after substituting reports.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return dest


def load_reports(reports_dir: Path) -> list[PerspectiveReport]:
    reports: list[PerspectiveReport] = []
    if not reports_dir.exists():
        return reports
    for path in sorted(reports_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        reports.append(PerspectiveReport.model_validate(payload))
    return reports


def synthesize_workspace(work_dir: Path) -> Decision:
    brief = Brief.model_validate_json((work_dir / "brief.json").read_text(encoding="utf-8"))
    reports = load_reports(work_dir / "reports")
    decision = heuristic_decision(brief, reports)
    blobs = [report.model_dump_json(indent=2) for report in reports]
    (work_dir / "synthesis_prompt.md").write_text(
        render_synthesis_prompt(brief, blobs or ["(no reports yet)"]),
        encoding="utf-8",
    )
    (work_dir / "decision.json").write_text(decision.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return decision
