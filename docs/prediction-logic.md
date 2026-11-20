# Prediction / comparison logic

**This is historical comparison, not a guarantee.** Output shows the exact official record(s) used.

## Engineering (MHT-CET, JEE Main) – percentile
`gap = student_percentile − closing_percentile` (percentile points) against a past round's closing cutoff.
* `gap < −m` → **ambitious**; `|gap| ≤ m` → **moderate**; `gap > +m` → **safer historical**.
* `m` = `ComparisonConfig.percentile_margin`, default **1.0** – an uncalibrated starting value; tune by backtesting prior-year cutoffs against next-year closings (Phase 4).
* No official closing value → `insufficient_data` with a reason. Never treated as 0.
* Records are matched on exam, year, round, category code, seat type (State / Home University / Other Than HU) and quota; Maharashtra State and All India records are never combined.

### How results are grouped and ordered (predictor)
* One result per college branch + seat type, with every year/round record listed under "Cutoff history".
* **Headline comparison** = the most recent year available, using that year's **Round 1** (the strictest closing cutoff). Later rounds, which close lower, are shown in the history so a student can see them but do not set the headline status.
* Order: *safer* — highest cutoff first (the best colleges you clear); *moderate* — smallest gap first; *ambitious* — lowest cutoff first (closest reach).

## Medical (NEET UG) – rank (Phase 6)
Separate engine (AIR / state merit rank, lower is better, MCC vs DMER rules). Not implemented; `get_engine("NEET_UG")` raises.
