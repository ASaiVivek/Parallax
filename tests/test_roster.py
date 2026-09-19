import json
from pathlib import Path

from parallax.catalog import load_catalog, select_perspectives
from parallax.models import PerspectiveSpec


def test_upto_does_not_bloat_on_narrow_query():
    specs = select_perspectives("What color should the icon be?", mode="upto", n=6)
    ids = [spec.id for spec in specs]
    assert ids[0] == "devil_advocate"
    assert 2 <= len(specs) < 6


def test_exactly_locks_count():
    specs = select_perspectives("What color should the icon be?", mode="exactly", n=5)
    assert len(specs) == 5
    assert specs[0].id == "devil_advocate"


def test_software_query_picks_operator_within_cap():
    specs = select_perspectives(
        "Design the rollout for this API",
        domain="software",
        mode="upto",
        n=4,
    )
    ids = [spec.id for spec in specs]
    assert "operator" in ids
    assert len(specs) <= 4


def test_product_query_picks_beneficiary():
    specs = select_perspectives("Redesign the checkout UX", domain="product", mode="upto", n=4)
    ids = [spec.id for spec in specs]
    assert ids[0] == "devil_advocate"
    assert "beneficiary" in ids
    assert len(specs) <= 4


def test_drop_in_json_extends_catalog(tmp_path: Path):
    extra = tmp_path / "offsets"
    extra.mkdir()
    (extra / "regulator.json").write_text(
        json.dumps(
            {
                "id": "regulator",
                "title": "Regulator",
                "stance": "legal",
                "mandate": "Ask whether a supervisor would allow this.",
                "cues": ["bank", "capital", "basel"],
                "required": False,
                "priority": 15,
            }
        ),
        encoding="utf-8",
    )
    catalog = load_catalog([extra])
    assert "regulator" in catalog
    specs = select_perspectives(
        "Does this meet Basel capital rules for the bank?",
        mode="upto",
        n=4,
        catalog=catalog,
    )
    assert "regulator" in [spec.id for spec in specs]


def test_forced_id_is_included():
    specs = select_perspectives(
        "Pick a name",
        extra_ids=["science"],
        mode="upto",
        n=3,
    )
    assert "science" in [spec.id for spec in specs]
    assert len(specs) <= 3


def test_unknown_forced_id_raises():
    try:
        select_perspectives("Pick a name", extra_ids=["not_a_real_offset"])
    except ValueError as exc:
        assert "not_a_real_offset" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_override_builtin_via_drop_in(tmp_path: Path):
    extra = tmp_path / "offsets"
    extra.mkdir()
    (extra / "devil_advocate.json").write_text(
        PerspectiveSpec(
            id="devil_advocate",
            title="Stricter advocate",
            stance="challenge",
            mandate="Be harsher.",
            required=True,
            priority=0,
        ).model_dump_json(),
        encoding="utf-8",
    )
    catalog = load_catalog([extra])
    assert catalog["devil_advocate"].title == "Stricter advocate"
