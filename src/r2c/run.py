"""One solve, from an input and the analysis settings to a raw record.

This is r2c's programming interface as well as what the command line calls:

    from r2c import run
    result = run.solve("beam.r2t", increment=(0, 1, 1))
    result.record_bytes()                # the raw record, r2x's format
    result.stages                        # the load stages, for anything else
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from r2c import __version__, export, inputs, record, stages as stagelib, views as viewlib
from r2c.inputs import OutOfScope, SectionInput
from r2c.notice import DISCLAIMER
from r2c.section import Section
from r2c.settings import MORE_DETAIL_MAX
from r2c.solver import Analysis, Flexure, SolveError, Stage
from r2c.units import FILE_UNITS, Units

CSA = (0.65, 0.85, 0.90)
MAX_STAGES = 101          # without shear Response stops adding load stages at 101 (0 to 100)
STAGE_SLOTS = 330         # with shear only the count of solves ends it; the program's table of
                          # stages has 330 places (docs/kernel.md, "How many stages")
MORE_DETAIL_LIMIT = 327   # and refines no further than 327


class Failed(RuntimeError):
    """The solve produced no result."""


@dataclass
class Result:
    name: str
    input_sha256: str | None
    units: Units
    factors: tuple[float, float, float]
    initial: tuple[float, float, float]      # in the units in effect
    increment: tuple[float, float, float]
    more_detail: int
    section: Section
    stages: list[Stage]
    peak: int
    gam_avg: list[float] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # the number of stages kept when the owner's override took over from Response's own
    # solve (Shear.carry_on); None where it did not
    carried_from: int | None = None

    def header(self, views, detail) -> dict[str, str]:
        h = {"r2c-version": __version__, "kernel": "r2c", "disclaimer": DISCLAIMER,
             "input-name": self.name}
        if self.input_sha256:
            h["input-sha256"] = self.input_sha256
        h["units"] = self.units.name
        h["factors"] = ",".join(f"{x:.2f}" for x in self.factors)
        h["initial"] = ",".join(f"{x:.2f}" for x in self.initial)
        h["increment"] = ",".join(f"{x:.2f}" for x in self.increment)
        h["more-detail"] = str(self.more_detail)
        h["views"] = viewlib.format_views(views)
        h["stage-count"] = str(len(self.stages))
        h["peak-stage"] = str(self.peak)
        h["detail-stages"] = stagelib.format_ranges(detail)
        return h

    def record_bytes(self, stage_spec=stagelib.PEAK, views=viewlib.ALL, on_stage=None) -> bytes:
        detail = stage_spec.resolve(len(self.stages), self.peak)
        keys = export.control_keys(self.increment)
        sections = [(record.control_section(k),
                     export.control(k, self.stages, self.units, self.gam_avg,
                                    self.section.zaxial - self.section.zc)) for k in keys]
        charts = viewlib.record_order(views)
        builder = export.Views(self.section, self.units)
        wanted = set(detail)
        done = 0
        for i, st in enumerate(self.stages):
            builder.observe(st)
            if i in wanted:
                made = builder.charts(st, [c.key for c in charts])
                for c in charts:
                    sections.append((record.stage_section(i, c.key), made[c.key]))
                done += 1
                if on_stage:
                    on_stage(i, done, len(detail))
        return record.encode(self.header(views, detail), sections)


def _factors(inp: SectionInput, factors: str | None):
    if factors == "csa":
        return CSA
    if factors == "none":
        return (1.0, 1.0, 1.0)
    return (inp.phic, inp.phis, inp.phip)


def peak_stage(stages: list[Stage], incr) -> int:
    """The stage Response shows when a solve ends: the largest load of the bottom control
    chart (moment if the increment has one, else shear, else axial load)."""
    n, m, v = incr
    if m != 0.0:
        vals = [s.m * (1 if m > 0 else -1) for s in stages]
    elif v != 0.0:
        vals = [s.v for s in stages]
    elif n != 0.0:
        vals = [s.n * (1 if n > 0 else -1) for s in stages]
    else:
        return len(stages) - 1
    return int(np.argmax(vals))


@dataclass
class Setup:
    """An input read and an analysis set up, ready to solve: what solve() does before it
    steps through the load stages. The diagnostic tools (tools/diagnose.py) start here too."""
    name: str
    input_sha256: str | None
    units: Units
    factors: tuple[float, float, float]
    initial: tuple[float, float, float]      # in the units in effect
    increment: tuple[float, float, float]
    section: Section
    analysis: Analysis

    def driver(self, on_stage=None):
        """The load-stepping driver for this analysis: with shear or without."""
        if self.analysis.shear:
            from r2c.shear import Shear
            return Shear(self.analysis, on_stage=on_stage)
        return Flexure(self.analysis, on_stage=on_stage)

    @property
    def max_stages(self) -> int:
        """The most load stages a response may have."""
        return STAGE_SLOTS if self.analysis.shear else MAX_STAGES


def setup(path: str | Path | None = None, *, units: str | None = None,
          factors: str | None = None, initial=None, increment=None,
          data: bytes | None = None) -> Setup:
    """Read an input (or take the default section when path is None) and set up its
    analysis with the given settings."""
    if path is None and data is None:
        inp = inputs.default_section()
        name, sha = "File > New", None
    else:
        raw = Path(path).read_bytes() if data is None else data
        inp = inputs.parse(raw)
        name = Path(path).name if path is not None else "input"
        sha = hashlib.sha256(raw).hexdigest()
    file_u = FILE_UNITS[inp.units]
    u = FILE_UNITS[units] if units else file_u
    fac = _factors(inp, factors)

    # loads: the input's are in its own units; options are in the units in effect
    if initial is None:
        const = inp.loading.constant
    else:
        const = (initial[0] * u.force, initial[1] * u.moment, initial[2] * u.force)
    if increment is None:
        dn, dm, dv = inp.loading.increment
        incr = (dn * file_u.force, dm * file_u.moment, dv * file_u.force)
    else:
        incr = (increment[0] * u.force, increment[1] * u.moment, increment[2] * u.force)
    shown_initial = (const[0] / u.force, const[1] / u.moment, const[2] / u.force)
    shown_incr = (incr[0] / u.force, incr[1] / u.moment, incr[2] / u.force)
    if incr[2] < 0 or const[2] < 0:
        raise OutOfScope("the shear must be positive, as in Response-2000")

    sec = Section(inp, *fac)
    an = Analysis(sec, const, incr)
    return Setup(name, sha, u, fac, shown_initial, shown_incr, sec, an)


CARRY_TOL = 0.05     # "the same place" along a curve, as docs/measures.md has it (5 %)


def _carries_on(driver, stages, again, other) -> bool:
    """Does the response of r2c's own solve (other) pass the last stage of the response that
    Response's solve gave up on (stages), and go on beyond it? The test the measure makes
    on the two programs' records (docs/measures.md, "The overrides"), made here on r2c's two
    responses: the control variable over its largest value and the load over the largest
    load, the same place within CARRY_TOL."""
    mode = driver.mode0
    xs = max(abs(driver.control_of(s, mode)) for s in stages)
    pk = max(abs(s.lam) for s in stages)
    if xs <= 0.0 or pk <= 0.0 or len(other) < 2:
        return False
    pt = lambda d, s: (d.control_of(s, mode) / xs, s.lam / pk)
    gx, gy = pt(driver, stages[-1])
    curve = [pt(again, s) for s in other]
    best, at = math.inf, 0.0
    for i in range(len(curve) - 1):
        (x0, y0), (x1, y1) = curve[i], curve[i + 1]
        dx, dy = x1 - x0, y1 - y0
        den = dx * dx + dy * dy
        t = 0.0 if den <= 0.0 else min(max(((gx - x0) * dx + (gy - y0) * dy) / den, 0.0), 1.0)
        d = math.hypot(x0 + t * dx - gx, y0 + t * dy - gy)
        if d < best:
            best, at = d, i + t
    if best > CARRY_TOL or at >= len(curve) - 1 - 1e-9:
        return False
    lx, ly = curve[-1]
    if math.hypot(lx - gx, ly - gy) <= CARRY_TOL:
        return False
    driver.joined_at = int(math.floor(at)) + 1      # the first of the other's stages beyond
    return True


# Where the response of r2c's own solve from the start is the one that carries on, the
# stages kept before Response's solve gave up stay, and the other response's stages beyond
# the place where it passes the last of them are put after them. Off: the whole response
# is the other one (as before increment 8)
JOIN = True


def solve(path: str | Path | None = None, *, units: str | None = None,
          factors: str | None = None, initial=None, increment=None, more_detail=0,
          on_event=None, data: bytes | None = None) -> Result:
    """Solve one input (or the default section when path is None)."""
    su = setup(path, units=units, factors=factors, initial=initial, increment=increment,
               data=data)
    name, sha, u, fac = su.name, su.input_sha256, su.units, su.factors
    shown_initial, shown_incr, sec = su.initial, su.increment, su.section

    def tick(count):
        if on_event:
            on_event("solving", count)

    driver = su.driver(on_stage=tick)
    try:
        stages = driver.run(su.max_stages)
    except SolveError as e:
        raise Failed(str(e)) from None
    if not stages:
        raise Failed("no load stage was solved")
    if getattr(driver, "carried_from", None) == len(stages):
        # The owner's override (docs/brief.md, 2026-11-25), kept in force: Response's
        # solve gave up and r2c's own found no stage beyond the last one kept. Where the
        # response r2c's own solve finds from the start passes that stage and goes on
        # beyond it, that response is the one given; else this one ends here, as
        # Response's does.
        fresh = setup(path, units=units, factors=factors, initial=initial,
                      increment=increment, data=data)      # its own history and mesh
        again = fresh.driver(on_stage=tick)
        again.own_solve = again.parabolic_error = False
        try:
            other = again.run(su.max_stages)
        except SolveError:
            other = []
        if other and _carries_on(driver, stages, again, other):
            if JOIN:
                again.carried_from = len(stages)
                stages = stages + other[driver.joined_at:]
                driver = again
            else:
                driver, stages = again, other
                driver.carried_from = 0     # the whole response is r2c's own solve's
    peak = peak_stage(stages, shown_incr)

    presses = 0
    want = more_detail
    limit = 99 if want == MORE_DETAIL_MAX else int(want)
    while presses < limit:
        new, newpeak = driver.more_detail(stages, peak, MORE_DETAIL_LIMIT)
        if len(new) == len(stages):
            break
        stages, peak = new, newpeak
        presses += 1
        if on_event:
            on_event("refining", (presses, len(stages)))
    notes = []
    if want != MORE_DETAIL_MAX and presses < int(want):
        notes.append(f"More Detail refined the solve {presses} times, not {want}")
    gam = [getattr(s, "gam_avg", s.gam) for s in stages]
    return Result(name, sha, u, fac, shown_initial, shown_incr, presses, sec, stages, peak, gam,
                  notes, getattr(driver, "carried_from", None))
