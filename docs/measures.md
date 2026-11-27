# The measures: how a result is judged against Response-2000

Reference for the developer. The tolerance and the priorities are the owner's
(`docs/brief.md`, "Fixed by the owner" and "Accuracy priorities"); this page says how the
tools apply them. The measures were carried over unchanged from the earlier record when the
brief took effect (2026-11-24). **They change only when the owner changes them**, and no
result is brought inside target by changing one.

## Targets (machine-read)

±5 % on every metric. Where a value is small, close to the precision of the printed output,
an absolute floor applies in place of the percentage.

`tools/report.py` reads the block below (`read_targets`). Percentages are measured as
`tools/compare.py` measures them:

- `peak_pct`: the difference of the largest load on the bottom control chart, relative to
  Response's.
- `curve_pct`: the rising branch. The largest distance between the two curves up to
  Response's peak, measured both ways (Response's points from r2c's curve and r2c's from
  Response's), load scaled by Response's peak, control value by its largest value over the
  whole curve.
- `post_peak_pct`: the ending. The same, after Response's peak. An r2c point counts as
  post-peak when its nearest point on Response's curve is at or after Response's peak, so a
  response that runs on past Response's end, or stops short of it, counts here.
- **Shape** (not a number): the curve's features in order (cracking, falls of load before
  the peak, the peak, and how the response ends: falling, standing still, or at the peak)
  must be the same. For a case with shear, shape leaves out how the response ends.
- **Small values:** a difference within two units of the last digit Response prints is never
  a miss, for the curves and the views alike. The resolution is read from the data. A
  difference of exactly two units counts as within them (the floor has room for the
  arithmetic of subtracting two printed numbers; before 2026-11-25 it did not).
- `views_pct`: the largest difference in a detail view at a compared stage, relative to that
  chart's largest value.

Cases without shear (no shear in the initial load or the increment) are `flexure` in the
tools; cases with shear are `shear`. These are the brief's two areas: moment and axial;
shear.

```toml
[flexure]
peak_pct = 5.0
curve_pct = 5.0
post_peak_pct = 5.0

[shear]
peak_pct = 5.0
curve_pct = 5.0
post_peak_pct = 5.0

[views]
views_pct = 5.0
views_exempt = []
# the three groups of views: stress state, shear-related, cracking-related
must = ["longitudinal_strain", "longitudinal_concrete_stress", "principal_compressive_stress",
        "principal_tensile_stress", "principal_tensile_strain", "long_reinforcement_stress",
        "long_reinf_stress_at_crack", "shrinkage_thermal_strain"]
should = ["transverse_strain", "shear_strain", "shear_stress", "shear_on_crack",
          "average_angle", "stirrup_stress", "stirrup_stress_at_crack",
          "transverse_average_bond"]
could = ["crack_widths", "long_crack_spacing", "transverse_crack_spacing",
         "diagonal_spacing", "long_average_bond"]
```

## Checks by priority

The brief's four priorities, as the tools count them (`tools/heldout.py`, `PRIORITY`). The
names `must`, `should` and `could` in the block above and in the tools are the earlier
record's names for the three groups of views; they are kept so that the measure is the same
code as before.

| Priority | Checks | In the tools |
|---|---|---|
| 1 | Peak, rising branch and shape, on every case. The stress-state views on cases without shear. | `peak`, `curve`, `shape`; tier `views` |
| 2 | The ending on cases without shear. The shear-related views; the stress-state views on cases with shear. | `post_peak` (flexure); tier `views_should` |
| 3 | The cracking-related views. | tier `views_could` |
| 4 | The ending on cases with shear. | `post_peak` (shear) |

A case is inside a priority when every one of its checks of that priority is inside target.
The views of the last stage of a case with shear are part of its ending and are not counted
in priorities 1 to 3.

## Where Response is unstable

A view check means something only where Response's own result is steady. Where Response's
view spikes at a stage, departing from its neighbours and coming back, such a check is
reported but counts neither inside nor outside. A step, where Response moves to a new state
and stays there (cracking, for one), stays assessed.

- **Which checks:** every detail view at each stage where views are compared. Not the checks
  on the curves.
- **The test (a spike):** Response's views at the stages just before and after are captured
  as well. A view at a stage is *unstable* when both hold, each with the same distance
  measure and printed-precision floor as the comparison: its two neighbours agree with each
  other within `views_pct`; and Response's own view at the stage lies farther than
  `views_pct` from the blend of its two neighbours' views, taken at the stage's place along
  the control curve.
- **Without both neighbours** (the first or last stage) a view is not tested and stays
  assessed.

## The overrides

**The circular column under axial load alone.** r2c keeps its uniform post-peak response
(`docs/brief.md`). The checks on that case that follow from it are outside target and are
counted as such; the override says they are not chased, not that they pass.

**With shear, where Response's solve gives up and r2c carries on** (owner, 2026-11-25;
narrowed 2026-11-27): r2c keeps carrying on, and such a case is compared up to Response's
last stage. Since 2026-11-27 the override holds only where a trace of Response confirms a
numerical give-up, and priority 1 with shear is reported with no case cut first and cut
second. The owner's decision is the comparison; how such a case is told is the developer's
reading, the same for the development and the held-out sets (`tools/compare.py`,
`carried_on`). It is such a case when all of these hold:

- the case has shear;
- a trace of Response's own stage control on the case (`tools/rtrace.py`, read by
  `tools/traceend.py`) shows a numerical give-up: after the last stage Response kept, its
  tries ran down to the smallest step, and every one of them failed in the solve of the
  global strains or had not settled after 16 passes. A case is not cut where there is no
  trace, where the trace does not reach the capture's last stage, where one of those tries
  is a solved state that Response refused on its state code (the web crushing, a stirrup
  past rupture), or where Response ended on a stage it kept, of its own accord. The
  endings are kept by the capture's control curves: `tests/oracle/trace-ends.json` for the
  development set, a file in each held-out archive for its set;
- Response's last stage carries at least 0.8 of its peak load, so its response was not
  ended by its own test on a load that has fallen;
- r2c's curve passes Response's last stage at the same place (within `curve_pct`, as the
  curves are measured);
- r2c has stages beyond that point, and its own last stage is not at the same place as
  Response's: if r2c ends where Response ends, it has not carried on.

r2c's curve is then cut at its point nearest Response's last stage, and peak, rising
branch, ending and shape are measured on the cut curve. The views are compared with r2c's
stages up to the first one at or past that point. Where Response's last stage is its
peak, nothing is left after the peak on either curve and the ending counts as the same.

Every comparison that is cut is also kept as it is with no cut (`compare.uncut`), and the
held-out scorer records both totals. What the measure cannot show: whether r2c carried on
by the override (its copy of Response's solve gave up there and its own went on, which
its record then marks: `response-last-stage`) or because its copy did not fail where
Response's did. `python tools/marks.py` counts the two.

## The regression limits

The limits in `tests/test_oracle.py` say "no worse than when last compared". They guard what
works on the development set; they are not the target.

## Speed (owner, 2026-11-26)

A reported measure, not a target (owner, 2026-11-26, the second answer of that day;
between the two it was part of the solution threshold): r2c's run time beside r2x's on
the same input, measured on the same machine, with r2x reading every stage. No compiled
routines in r2c. r2c's standing is generated into the brief and shown on the results
page.

- r2x's time: the wall-clock seconds of one `r2x.worker` command on the case, start to
  exit, with the case's own options (`python tools/r2xtimes.py measure`; recorded for the
  development set in `tests/oracle/r2x-times.json`). Two readings are recorded: with the
  detail views of every stage, as the development captures were made and as
  `tools/verify.py` has r2c write them, and with the detail views of the peak stage
  alone, r2x's default. The bar for the reported measure is the first (owner,
  2026-11-26).
- r2c's time: the seconds `tools/verify.py` records for the solve of the case.
- `python tools/r2xtimes.py compare VERIFY_OUT` counts the cases within, by area.
- A speed change changes no result: `tests/oracle/records.json` (the hash of r2c's whole
  record of every development case), `python tools/same.py VERIFY_OUT`, and the oracle
  tests, which hold each case they solve to its hash. A change of result rewrites the
  hashes in its own commit.

Not measured on the held-out sets: nothing per case of theirs is kept, and the scorer's
only word on time is its limit a case.

