"""Where Response's response would end: how the tries that ran out are read, and what the
record then says (owner, 2026-11-27; docs/kernel.md, "Where Response's response ends and
r2c's goes on")."""

from types import SimpleNamespace

from r2c import record, run, shear
from r2c.solver import GAVE_UP, REFUSED, UNTOLD


def test_only_numerical_failures_are_a_give_up():
    assert shear.stop_kind(["no solve"] * 8) == GAVE_UP
    assert shear.stop_kind(["16 passes above", "no solve", "no solve"]) == GAVE_UP
    # a solved state refused because its web is crushing: Response's own limit
    assert shear.stop_kind(["code 3 above", "no solve", "no solve"]) == REFUSED
    assert shear.stop_kind(["no solve", "code 3", "no solve"]) == REFUSED
    # refused for another reason: neither for certain
    assert shear.stop_kind(["code 4", "no solve"]) == UNTOLD
    assert shear.stop_kind(["?", "no solve"]) == UNTOLD


def _driver(stop, carried_from=None):
    return SimpleNamespace(stop=stop, carried_from=carried_from)


def test_the_stage_is_marked_only_where_r2c_goes_past_it():
    stages = list(range(12))
    assert run._ending(SimpleNamespace(), stages) == (None, None)
    assert run._ending(_driver(None), stages) == (None, None)
    # the override acted at stage 7 and stages follow
    assert run._ending(_driver((7, GAVE_UP), 8), stages) == (7, None)
    # it acted and nothing follows: r2c ends as Response does, and says why
    last, why = run._ending(_driver((11, GAVE_UP), 12), stages)
    assert last is None and "no state beyond" in why
    # the load had fallen: no override
    last, why = run._ending(_driver((11, GAVE_UP)), stages)
    assert last is None and "0.8" in why
    for kind, word in ((REFUSED, "crushing"), (UNTOLD, "cannot be told")):
        last, why = run._ending(_driver((11, kind)), stages)
        assert last is None and word in why and why.startswith(run.STOPPED)


def test_the_record_of_a_response_that_does_not_go_past_has_no_such_lines():
    res = run.solve()                                   # Newbeam under moment: no shear
    rec = record.decode(res.record_bytes())
    assert res.carried_stage is None and res.ending is None
    assert not {"carried-on-stage", "carried-on-peak-stage", "carried-on",
                "ending"} & set(rec.header)
    assert run.CARRIED_STAGE not in rec.sections


def test_the_mark_in_the_header_and_in_the_data():
    res = run.solve()
    res.carried_stage = 5                               # as if r2c had carried on from stage 5
    rec = record.decode(res.record_bytes())
    assert rec.header["carried-on-stage"] == "5"
    assert int(rec.header["carried-on-peak-stage"]) <= 5
    assert "carried on with its own solve" in rec.header["carried-on"]
    assert "may end at another" in rec.header["carried-on"]         # no claim on Response
    keys = list(rec.header)
    assert keys.index("carried-on-stage") == keys.index("peak-stage") + 1
    body = rec.sections[run.CARRIED_STAGE].decode("latin-1")
    assert "Stage\t\t: 5" in body
    # the stage's own row of each control chart, as that chart prints it
    for key in ("moment_ex", "moment_phi"):
        row = rec.control(key).decode("latin-1").split("\r\n")[10 + 5]
        assert f"Chart\t\t: {key}" in body and row in body
