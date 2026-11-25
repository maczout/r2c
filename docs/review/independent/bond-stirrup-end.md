# Independent assessment

## What the evidence shows

- Five checks, all `transverse_average_bond`, on four shear cases: 28.5, 14.5, 14.3, 10.5 and 6.0 % ("The instances").
- Peak loads agree within 0.2 % on all four cases ("The two responses").
- Evaluated in Response's own state, r2c still differs: 12.5, 10.4, 13.3, 6.6 and 18.0 % (same table). For `column-mv` stage 36 every other view is within 1.61 %, loads within 0.11 % (`diagnose.py states ... --stages 36 --views`).
- The bond rule applied to Response's own stirrup stress chart reproduces Response's bond chart: 0.0 % for `column-mv` stage 36 and `newbeam-m05v` stage 51 (`bond.py`).
- The same tool on `newbeam-us-mv` stages 30 and 56 gives 100 %: the rule returns 0.0000 against 1919.97 and 4625.71 (`bond.py ... --stages 30,56`). No `bond.py` run is given for `newbeam-usfile-mv`.
- `column-mv`, stirrup stress at the peak: point differences up to 228 MPa near depth +70 to +75, up to 149 MPa near −102 to −117, and −98 to +138 MPa near −181 to −189, where Response's own profile swings between 173 and −57 MPa (`viewlines.py ... stirrup_stress`).
- The bond charts differ in the same bands: depth 60 to 90, Response 30 to 34, r2c 14 to 19; −90 to −120, Response 33 to 36, r2c 54 to 58; −165 to −210, Response 26 to 29, r2c 8 to 15 ("The views").

## The reason

- **measured**: The post-processing rule is not the cause on the two SI cases. `bond.py` gives 0.0 % on Response's own stirrup stresses (`column-mv` 36, `newbeam-m05v` 51). The difference therefore enters through the stirrup stress profile r2c feeds the rule.
- **measured**: The solver's path is not the main cause. In Response's own state the differences remain 6.6 to 18.0 %, all outside target, and for `newbeam-us-mv` at the peak larger (18.0 %) than the check itself (6.0 %).
- **measured**: On `column-mv` the stirrup stress profiles differ locally by up to 228 MPa (`viewlines.py`), in the bands where the bond charts differ. The stirrup stress view itself scores only 1.61 % in Response's state.
- **read**: The rule at `0047fcd0` takes the size of the stress change between nodes over their distance. The decompiled routine bears this out for its `param_3 == 1` branch: absolute difference, division by node spacing, zero unless two nodes' `+0x80` values are positive, 41 heights, window clipped at the faces and averaged. It does not show that `+0x80` is the stirrup ratio, the constants (eighth, twentieth, five diameters), the routines `00485640` and `00484420`, or which branch draws this chart.
- **inferred**: Because the rule differentiates, a shift of a few millimetres in where the stirrup stress jumps, small in the stirrup view's measure, becomes a large bond difference. Nothing in the file tests this.

## What the evidence does not establish

- Why r2c's stirrup stress differs locally from Response's in the same state. Best diagnostic: the node-by-node stirrup stress of both in Response's state, `column-mv` stage 36.
- Whether r2c's bond chart follows from r2c's own stirrup stresses. By my rough sum of the chart near depth 60 to 90 the stress change is about equal (roughly 255 against 260 MPa), yet r2c's bond is half. An error in r2c's implementation of the rule is not excluded. Best diagnostic: `bond.py` on r2c's own record.
- The US-unit cases (three of five checks). The rule check fails outright (100 %) on one and is absent for the other; whether that is the tool or the rule is unknown. Best diagnostic: `bond.py` fixed or explained for US units, run on both.
- Whether Response's bond chart is steady at these stages. Its stirrup profile at `column-mv` looks erratic, but no neighbouring stages' views are given. Best diagnostic: the D54 test's figures for each check.
- The in-state figure is given per view only for `column-mv`.

## Against the targets

`transverse_average_bond` is in the Should tier (`should` list; all four are shear cases). Target `views_pct` = 5 %; not exempt; no owner's override applies. The checks are 28.5 % (5.7 × target), 14.5 % (2.9), 14.3 % (2.9), 10.5 % (2.1) and 6.0 % (1.2): all outside. Four are at the peak, one at a fall of load (stage 30). They are assessed, so none was set aside as unstable.

## On the developer's reason

1. **Supported.** The instances table gives r2c in Response's own state at 12.5, 10.4, 13.3, 6.6 and 18.0 %, all over the 5 % target, so the state reached does not explain them. The mark "measured" is right, though the tool named (`tools/sources.py`) is not in my evidence; the figures there come from the table and, for `column-mv` only, from `diagnose.py states`.

2. **Supported for two checks, not for the other three.** `bond.py` gives 0.0 % on `column-mv` stage 36 and `newbeam-m05v` stage 51. On `newbeam-us-mv` stages 30 and 56 it gives 100 % (the rule returns 0.0000), and there is no run for `newbeam-usfile-mv`. As a statement about the whole group, "measured" is too strong: it is measured for the two SI cases, and for the US cases the only measurement in the file goes the other way (tool fault or rule fault, the file does not say). The conclusion "the rule is the program's" also covers only chart-to-chart; it does not show that r2c's own bond chart follows from r2c's own stirrup stresses, which my rough sum on `column-mv` puts in doubt.

3. **Not decided, and partly contradicted.** That a state rebuilt from Response's charts is too coarse is untested, as the developer says; "inferred" is the right mark. But "largest where the stirrups end" does not fit the charts. On `column-mv` the differences are at depths 60 to 90 and −90 to −120, well inside the range where both stirrup stress charts are non-zero (about +140 to −218), and only the third band (−165 to −210) is near an end. On `newbeam-usfile-mv` the largest differences are at −4.1 to −5.9 and +2.4 of ±11.8, while the two ends agree closely. Only `newbeam-m05v` (depth 255) and `newbeam-us-mv` stage 30 (depth 10.0) show a difference at an end, alongside interior ones. The remark that the rule was never checked on a hoop sits oddly with the rule record in the evidence, which says it was checked on the column with interlocking hoops, and with `bond.py` giving 0.0 % on `column-mv`. The evidence also offers a local cause the developer does not name: stirrup stress differences of up to 228 MPa at the same depths on `column-mv`.

Verdict: does not decide
Suggestion: take up again - the cause is untested, its stated location (the stirrups' end) does not match where the charts differ, and two cheap runs (`bond.py` on r2c's own record and on the US cases) would show whether the fault is in r2c's rule, its stirrup stresses or the diagnostic.
